"""Scan every downloaded common CAAM/COLB continuous interval, without a catalog."""
from pathlib import Path
import os,json,argparse
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
import numpy as np
import pandas as pd
from obspy import read,UTCDateTime
from scipy.signal import fftconvolve,find_peaks
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--dataset',choices=['extended','continuation'],default='extended');args=ap.parse_args()
OUT=Path('data')/args.dataset;cfg=json.loads(Path('config/observations.json').read_text())
def corr(x,y):
    y=y-y.mean();n=len(y);s=np.r_[0.,np.cumsum(x)];ss=np.r_[0.,np.cumsum(x*x)]
    den=np.sqrt(np.maximum(ss[n:]-ss[:-n]-(s[n:]-s[:-n])**2/n,0))*np.linalg.norm(y)
    return np.divide(fftconvolve(x,y[::-1],mode='valid'),den,out=np.zeros(len(x)-n+1),where=den>0)
templates={}
for label,time in cfg['template_times'].items():
    templates[label]={}
    for sta in ['CAAM','COLB']:
        st=read(f'inputs/waveforms/{label}_{sta}.mseed').select(component='Z');st.detrend('demean');st.filter('bandpass',freqmin=.2,freqmax=6,corners=4)
        t=UTCDateTime(time);y=st[0].copy().trim(t,t+7.99).data.astype(float);assert len(y)==800 and abs(corr(y,y)[0]-1)<1e-9
        templates[label][sta]=y
index={s:[] for s in ['CAAM','COLB']}
files=list(Path('inputs/waveforms').glob('day_*.mseed'))+list(Path('inputs/extended/waveforms').glob('*.mseed'))
if args.dataset=='continuation':
    # Reuse the exact observation checkpoint; later downloads must not silently
    # change the exposure of an offline rebuild.
    files += [Path(r['file']) for r in json.loads(Path('docs/continuation_processed_inputs.json').read_text())]
for f in files:
    if not any(s in f.name for s in index):continue
    for tr in read(str(f),headonly=True).select(component='Z'):
        if tr.stats.station in index:index[tr.stats.station].append((tr.stats.starttime,tr.stats.endtime,str(f)))
intervals=[];candidates=[];covered=[]
for a0,a1,af in sorted(index['CAAM']):
    for b0,b1,bf in sorted(index['COLB']):
        start=max(a0,b0,UTCDateTime('2022-01-21'));end=min(a1,b1,UTCDateTime('2025-03-21'))
        if end-start<30:continue
        # Partition against already scanned intervals to avoid duplicate exposure.
        chunks=[(start,end)]
        for u,v in covered:
            remaining=[]
            for a,b in chunks:
                if b<=u or a>=v:remaining.append((a,b));continue
                if a<u:remaining.append((a,u))
                if b>v:remaining.append((v,b))
            chunks=remaining
        for a,b in chunks:
            if b-a<30:continue
            ca=read(af,starttime=a,endtime=b).select(component='Z');cb=read(bf,starttime=a,endtime=b).select(component='Z')
            if len(ca)!=1 or len(cb)!=1:continue
            # Use common sampled times, never interpolate over gaps.
            begin=max(ca[0].stats.starttime,cb[0].stats.starttime);finish=min(ca[0].stats.endtime,cb[0].stats.endtime)
            ca.trim(begin,finish);cb.trim(begin,finish)
            if any(tr.stats.sampling_rate!=100 for tr in [ca[0],cb[0]]):continue
            if abs(ca[0].stats.starttime-cb[0].stats.starttime)>.005:continue
            for st in [ca,cb]:st.detrend('demean');st.filter('bandpass',freqmin=.2,freqmax=6,corners=4)
            n=min(len(ca[0]),len(cb[0]));maximum={}
            for label,template in templates.items():
                caam_score=corr(ca[0].data[:n],template['CAAM']);colb_score=corr(cb[0].data[:n],template['COLB'])
                score=(caam_score+colb_score)/2
                idx,_=find_peaks(score,height=.25,distance=800);idx=idx[(idx>=1000)&(idx<len(score)-1000)]
                maximum[label]=float(score[1000:-1000].max())
                for i in idx:candidates.append(dict(time=str(begin+i/100),template=label,score=float(score[i]),caam_score=float(caam_score[i]),colb_score=float(colb_score[i]),reviewed=False,caam_file=af,colb_file=bf))
            covered.append((a,b));intervals.append(dict(start=str(begin+10),end=str(begin+(n-800-1000)/100),valid_start_seconds=(n-800-2000+1)/100,caam_file=af,colb_file=bf,**maximum))
pd.DataFrame(intervals).to_csv(OUT/'hybrid_scan_intervals.csv',index=False)
pd.DataFrame(candidates,columns=['time','template','score','caam_score','colb_score','reviewed','caam_file','colb_file']).to_csv(OUT/'hybrid_candidates.csv',index=False)
summary=dict(intervals=len(intervals),valid_hours=sum(r['valid_start_seconds'] for r in intervals)/3600,candidates=len(candidates),one_station_nonpositive_score=sum(min(r['caam_score'],r['colb_score'])<=0 for r in candidates),reviewed_hybrid_events=0,full_study_search_complete=False,
    score_caveat='The documented two-station mean threshold can pass when one station has weak or negative similarity. Individual station scores are retained for review; no additional station threshold was imposed.')
(OUT/'hybrid_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
