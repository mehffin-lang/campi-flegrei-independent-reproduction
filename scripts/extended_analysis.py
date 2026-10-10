"""Independent picking and provisional GaMMA association; no catalog input.

The averaged external 3D model is an explicit sensitivity alternative to the
unavailable numerical Calo--Tramelli (2018) starting profile. This is NOT VELEST
or TomoDD relocation and must not be labeled a final reproduced catalog.
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

def model():
    lines=Path('inputs/extended/background_3d_vmod').read_text().splitlines()
    _,nx,ny,nz=lines[0].split();nx,ny,nz=map(int,(nx,ny,nz))
    lon,lat,z=[np.fromstring(s,sep=' ') for s in lines[1:4]]
    a=np.fromstring(' '.join(lines[4:]),sep=' ').reshape(2,nz,ny,nx)
    # TomoDD MOD convention: Vp followed by Vp/Vs. Exclude bounding nodes.
    assert np.all(a>0) and np.all((a[1]>1)&(a[1]<3))
    rows=[];profiles={}
    for name,box in [('caldera',(14.02,14.20,40.77,40.86)),('central',(14.11,14.16,40.81,40.84))]:
        mask=(lat[:,None]>=box[2])&(lat[:,None]<=box[3])&(lon[None,:]>=box[0])&(lon[None,:]<=box[1])
        vp=a[0,:,mask].mean(axis=0);vs=(a[0]/a[1])[:,mask].mean(axis=1)
        for zz,p,s in zip(z,vp,vs): rows.append(dict(region=name,depth_km=zz,vp_km_s=p,vs_km_s=s))
        keep=(z>=0)&(z<=7)
        profiles[name]=dict(z=np.r_[-.5,z[keep]].tolist(),p=np.r_[vp[keep][0],vp[keep]].tolist(),s=np.r_[vs[keep][0],vs[keep]].tolist())
    save('background_averages.csv',rows)
    return profiles

def main():
    import torch,seisbench.models as sbm
    from gamma.utils import association
    torch.set_num_threads(2);torch.manual_seed(0);np.random.seed(0)
    cfg=json.loads(Path('config/observations.json').read_text())
    meta=json.loads(Path('inputs/models/phasenet_retrained.json').read_text())
    net=sbm.PhaseNet(**meta['model_args']);net.load_state_dict(torch.load('inputs/models/phasenet_retrained.pt',weights_only=True,map_location='cpu'));net.eval();net.default_args.update(meta['default_args'])
    profiles=model()
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
    p=frame.rename(columns=dict(trace_id='id',time='timestamp',phase='type',probability='prob'))
    p['timestamp']=pd.to_datetime(p.timestamp,utc=True);p=p[p.id.isin(station.id)]
    config=dict(dims=['x(km)','y(km)','z(km)'],use_dbscan=True,use_amplitude=False,
        dbscan_eps=10,dbscan_min_samples=3,oversample_factor=5,initial_points=[1,1,1],
        min_picks_per_eq=6,min_p_picks_per_eq=0,min_s_picks_per_eq=0,max_sigma11=2,
        xlim=[-12,12],ylim=[-12,12],zlim=[0,8],bfgs_bounds=[(-12,12),(-12,12),(0,8),(None,None)],
        vel={'p':3.,'s':1.7},ncpu=1,covariance_prior=[1.])
    config['eikonal']=dict(vel=profiles['caldera'],h=.1,xlim=[-12,12],ylim=[-12,12],zlim=[-.5,8])
    config.update({'x(km)':[-12,12],'y(km)':[-12,12],'z(km)':[0,8]})
    Path('config/association.json').write_text(json.dumps(config,indent=2)+'\n')
    events=[];assignments=[]
    for day,g in p.groupby(p.timestamp.dt.date):
        ev,ass=association(g,station,copy.deepcopy(config),method='BGMM')
        offset=len(events)
        for e in ev:
            e['event_index']+=offset;e.pop('magnitude',None)
            e['longitude'],e['latitude']=trans.transform(e['x(km)'],e['y(km)'],direction='INVERSE')
        events.extend(ev);assignments.extend((i,j+offset,score) for i,j,score in ass)
    save('associations.csv',assignments,['pick_index','event_index','score'])
    save('initial_events.csv',events)
    checks=dict(pick_probability_bounds=bool(frame.probability.between(.3,1).all()),
        excluded_s_absent=not any(p['phase']=='S' and p['trace_id'].split('.')[1] in ['CASE','CFB1','CFB3'] for p in accepted),
        all_events_six_picks=all(e['num_picks']>=6 for e in events),
        picks_assigned_once=len({a[0] for a in assignments})==len(assignments),
        valid_assignment_indices=all(0<=a[0]<len(frame) for a in assignments))
    assert all(checks.values()),checks
    summary=dict(picks=len(frame),p_picks=int((frame.phase=='P').sum()),s_picks=int((frame.phase=='S').sum()),
        events=len(events),assigned_picks=len(assignments),waveform_files=len({r['file'] for r in coverage}),
        waveform_stations=sorted({r['channel'].split('.')[1] for r in coverage}),checks=checks,
        status='provisional association with alternative external profile; no VELEST/TomoDD relocation',
        numerical_starting_profile='data/extended/background_averages.csv',source_3d_sha256=hashlib.sha256(Path('inputs/extended/background_3d_vmod').read_bytes()).hexdigest())
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
