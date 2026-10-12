"""Independent picking and provisional GaMMA association; no catalog input.

This retained baseline regenerates waveform picks only. The old grid-dependent
association is quarantined; current association uses process_continuous.py.
"""
from pathlib import Path
import os, json, csv, hashlib, copy
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(SEISBENCH_CACHE_ROOT=str(ROOT/'tmp/seisbench'),NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
import numpy as np
import pandas as pd
from obspy import read, read_inventory, UTCDateTime
from pyproj import Transformer
OUT=Path('data/extended');OUT.mkdir(exist_ok=True)

def save(name, rows, fields=None):
    pd.DataFrame(rows,columns=fields).to_csv(OUT/name,index=False)

def main():
    import torch,seisbench.models as sbm
    from gamma.utils import association
    torch.set_num_threads(2);torch.manual_seed(0);np.random.seed(0)
    cfg=json.loads(Path('config/observations.json').read_text())
    meta=json.loads(Path('inputs/models/phasenet_retrained.json').read_text())
    net=sbm.PhaseNet(**meta['model_args']);net.load_state_dict(torch.load('inputs/models/phasenet_retrained.pt',weights_only=True,map_location='cpu'));net.eval();net.default_args.update(meta['default_args'])
    coverage=[];picks=[];failures=[]
    old=pd.read_csv('data/observations/picks.csv')
    picks.extend(old.to_dict('records'))
    for f in sorted(Path('inputs/extended/waveforms').glob('*.mseed')):
        if f.stat().st_size==0:continue
        try:
            st=read(str(f));st.merge(method=0);st=st.split()
            for tr in st:
                coverage.append(dict(file=str(f),channel=tr.id,start=str(tr.stats.starttime),end=str(tr.stats.endtime),samples=tr.stats.npts,sample_rate=tr.stats.sampling_rate))
            # Disjoint 30-minute cores with 15-s context avoid internal blind edges.
            begin=min(tr.stats.starttime for tr in st);end=max(tr.stats.endtime for tr in st)
            for t in np.arange(float(begin),float(end),1800):
                core=UTCDateTime(t);block=st.copy().trim(core-15,core+1815)
                if not block:continue
                block.detrend('demean');block.filter('highpass',freq=1,corners=4,zerophase=False)
                result=net.classify(block,P_threshold=.3,S_threshold=.3,batch_size=64)
                for p in result.picks:
                    if not(core<=p.peak_time<core+1800):continue
                    if p.phase=='S' and p.trace_id.split('.')[1] in ['CASE','CFB1','CFB3']:continue
                    picks.append(dict(source=str(f),trace_id=p.trace_id,phase=p.phase,time=str(p.peak_time),probability=float(p.peak_value)))
            print(f,len(picks),flush=True)
        except Exception as e:
            failures.append(dict(file=str(f),error=repr(e)))
    frame=pd.DataFrame(picks).sort_values('probability',ascending=False)
    # Merge repeated measurements of an arrival across overlapping retrievals.
    accepted=[];seen={}
    for p in frame.to_dict('records'):
        key=(p['trace_id'],p['phase']);t=float(UTCDateTime(p['time']))
        if any(abs(t-q)<.25 for q in seen.get(key,[])):continue
        seen.setdefault(key,[]).append(t);accepted.append(p)
    frame=pd.DataFrame(accepted).sort_values('time').reset_index(drop=True)
    frame.to_csv(OUT/'picks.csv',index=False);save('coverage.csv',coverage)
    (OUT/'read_failures.json').write_text(json.dumps(failures,indent=2))
    trans=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    stations={}
    for f in sorted(Path('inputs/extended/responses').glob('*.xml')):
        inv=read_inventory(str(f))
        for network in inv:
            for s in network:
                x,y=trans.transform(s.longitude,s.latitude)
                for ch in s:
                    ident=f'{network.code}.{s.code}.{ch.location_code}'
                    stations[ident]=dict(id=ident,**{'x(km)':x,'y(km)':y,'z(km)':-s.elevation/1000},longitude=s.longitude,latitude=s.latitude)
    station=pd.DataFrame(stations.values());station.to_csv(OUT/'stations.csv',index=False)
    print('Baseline waveform picking rebuilt. Superseded background-grid association is disabled.',flush=True)
if __name__=='__main__':main()
