"""Incremental inference and association using permitted observations and weights.

No routine catalog, author-derived catalog, or released picks are read here.
Cached picks are outputs of this implementation, identified by input/config hash.
"""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.update(SEISBENCH_CACHE_ROOT=str(ROOT/'tmp/seisbench'),NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
import argparse
import bisect
import concurrent.futures
import copy
import hashlib
import json
import multiprocessing
import inspect
import importlib.metadata
import sqlite3
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
from pyproj import Transformer
OUT=ROOT/'data/continuation'
CACHE=ROOT/'inputs/continuation/pick_cache'
SETTINGS=dict(highpass_hz=1,corners=4,zerophase=False,P_threshold=.3,S_threshold=.3,core_s=1800,context_s=30,merge_tolerance_s=.25,exclude_s=['CASE','CFB1','CFB3'])
FROZEN=False


def inference_identity():
    return dict(artifacts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                ['inputs/models/phasenet_retrained.pt','inputs/models/phasenet_retrained.json']},
                software={p:importlib.metadata.version(p) for p in ['torch','seisbench','obspy']},
                implementation_sha256=hashlib.sha256((inspect.getsource(pick)+inspect.getsource(initialize_worker)).encode()).hexdigest())


def initialize_worker():
    global NET
    import torch,seisbench.models as sbm
    torch.set_num_threads(2);torch.manual_seed(0)
    meta=json.loads(Path('inputs/models/phasenet_retrained.json').read_text())
    NET=sbm.PhaseNet(**meta['model_args'])
    NET.load_state_dict(torch.load('inputs/models/phasenet_retrained.pt',weights_only=True,map_location='cpu'))
    NET.eval();NET.default_args.update(meta['default_args'])


def pick(job):
    source,begin,end,digest=job
    try:
        st=read(source);st.merge(method=0);st=st.split()
        begin=max(begin,min(float(tr.stats.starttime) for tr in st))
        end=min(end,max(float(tr.stats.endtime)+1/tr.stats.sampling_rate for tr in st))
        picks=[];coverage=[]
        for tr in st:
            a=max(begin,float(tr.stats.starttime));b=min(end,float(tr.stats.endtime)+1/tr.stats.sampling_rate)
            if b>a:coverage.append(dict(channel=tr.id,start=a,end=b,file=source,sample_rate=tr.stats.sampling_rate))
        for t in np.arange(begin,end,SETTINGS['core_s']):
            block=st.copy().trim(UTCDateTime(t-30),UTCDateTime(min(t+1830,end+30)))
            if not block:continue
            block.detrend('demean');block.filter('highpass',freq=1,corners=4,zerophase=False)
            result=NET.classify(block,P_threshold=.3,S_threshold=.3,batch_size=128)
            for p in result.picks:
                if not(t<=float(p.peak_time)<min(t+1800,end)):continue
                if p.phase=='S' and p.trace_id.split('.')[1] in SETTINGS['exclude_s']:continue
                picks.append(dict(source=source,trace_id=p.trace_id,phase=p.phase,time=str(p.peak_time),probability=float(p.peak_value)))
        record=dict(file=source,input_sha256=digest,picks=picks,coverage=coverage,settings=SETTINGS,inference_identity=inference_identity(),core_start=job[1],core_end=job[2])
        path=CACHE/(hashlib.sha256(source.encode()).hexdigest()[:20]+'.json')
        path.with_suffix('.tmp').write_text(json.dumps(record));path.with_suffix('.tmp').replace(path)
        return dict(file=source,picks=len(picks),status='processed')
    except Exception as e:return dict(file=source,status='failed',error=repr(e))


def jobs():
    if FROZEN:
        return [(r['file'],r['start'],r['end'],r['sha256']) for r in json.loads(Path('docs/continuation_processed_inputs.json').read_text())]
    conn=sqlite3.connect('inputs/continuation/acquisition.sqlite');conn.row_factory=sqlite3.Row
    rows=list(conn.execute("SELECT file,start,end,sha256 FROM jobs WHERE status='downloaded' ORDER BY start,station"));conn.close()
    listed={r['file'] for r in rows}
    # Include the three successful initial chunk probes too.
    for file in sorted(Path('inputs/continuation/waveforms').glob('*.mseed')):
        if str(file) in listed:continue
        st=read(str(file),headonly=True)
        rows.append(dict(file=str(file),start=min(float(tr.stats.starttime) for tr in st),end=max(float(tr.stats.endtime)+1/tr.stats.sampling_rate for tr in st),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    return [(r['file'],r['start'],r['end'],r['sha256']) for r in rows]


def infer(workers):
    CACHE.mkdir(exist_ok=True)
    pending=[]
    for job in jobs():
        file=CACHE/(hashlib.sha256(job[0].encode()).hexdigest()[:20]+'.json')
        if file.exists():
            old=json.loads(file.read_text())
            if (old.get('input_sha256')==job[3] and old.get('settings')==SETTINGS
                and old.get('inference_identity')==inference_identity()
                and old.get('core_start')==job[1] and old.get('core_end')==job[2]):continue
            # A failed replacement must not leave an incompatible old cache
            # available for assembly as if inference had succeeded.
            file.unlink()
        pending.append(job)
    print(f'Processing {len(pending)} new waveform files on {workers} workers.',flush=True)
    log=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers,initializer=initialize_worker,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures=[pool.submit(pick,j) for j in pending]
        for f in concurrent.futures.as_completed(futures):
            r=f.result();log.append(r);print(r,flush=True)
    (OUT/'inference_last_run.json').write_text(json.dumps(log,indent=2)+'\n')
    if any(r['status']=='failed' for r in log):print('Some files failed; inspect inference_last_run.json.',flush=True)


def assemble():
    # Old picks are independent outputs generated in this repository, not author
    # picks. Their original preprocessing/source receipts remain preserved.
    frames=[pd.read_csv('data/extended/picks.csv')]
    coverage=[]
    old=pd.read_csv('data/extended/coverage.csv')
    for r in old.to_dict('records'):
        coverage.append(dict(file=r['file'],channel=r['channel'],start=float(UTCDateTime(r['start'])),end=float(UTCDateTime(r['end']))+1/r['sample_rate'],sample_rate=r['sample_rate']))
    # Coverage for the earlier one-day run is in its own record.
    p=Path('data/observations/coverage.csv')
    if p.exists():
        for r in pd.read_csv(p).to_dict('records'):
            coverage.append(dict(file=r['file'],channel=r.get('channel',r.get('id')),start=float(UTCDateTime(r['start'])),end=float(UTCDateTime(r['end']))+1/r.get('sample_rate',100),sample_rate=r.get('sample_rate',100)))
    selected={j[0]:j for j in jobs()};identity=inference_identity()
    for file in sorted(CACHE.glob('*.json')):
        c=json.loads(file.read_text())
        job=selected.get(c['file'])
        if job is None:continue
        if not (c.get('input_sha256')==job[3] and c.get('settings')==SETTINGS
                and c.get('inference_identity')==identity
                and c.get('core_start')==job[1] and c.get('core_end')==job[2]):continue
        frames.append(pd.DataFrame(c['picks']));coverage.extend(c['coverage'])
    allp=pd.concat(frames,ignore_index=True).sort_values('probability',ascending=False)
    # Processing margins are context, not extra study-period observations.
    study_start=float(UTCDateTime('2022-01-21'));study_end=float(UTCDateTime('2025-03-21'))
    coverage=[dict(r,start=max(study_start,r['start']),end=min(study_end,r['end'])) for r in coverage if r['end']>study_start and r['start']<study_end]
    accepted=[];seen={}
    for p in allp.to_dict('records'):
        key=(p['trace_id'],p['phase']);t=float(UTCDateTime(p['time']));arr=seen.setdefault(key,[]);i=bisect.bisect_left(arr,t)
        if not study_start<=t<study_end:continue
        if (i>0 and t-arr[i-1]<.25) or (i<len(arr) and arr[i]-t<.25):continue
        arr.insert(i,t);accepted.append(p)
    frame=pd.DataFrame(accepted).sort_values('time').reset_index(drop=True)
    frame.to_csv(OUT/'picks.csv',index=False)
    pd.DataFrame(coverage).to_csv(OUT/'processed_coverage.csv',index=False)
    trans=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    stations={};epochs=[]
    files=list(Path('inputs/extended/responses').glob('*.xml'))+list(Path('inputs/continuation').glob('*_responses.xml'))
    for file in files:
        inv=read_inventory(str(file))
        for net in inv:
            for s in net:
                x,y=trans.transform(s.longitude,s.latitude)
                for ch in s:
                    ident=f'{net.code}.{s.code}.{ch.location_code}'
                    stations[ident]=dict(id=ident,**{'x(km)':x,'y(km)':y,'z(km)':-s.elevation/1000},longitude=s.longitude,latitude=s.latitude)
                    epochs.append(dict(id=ident,channel=ch.code,start=str(ch.start_date),end=str(ch.end_date) if ch.end_date else '',response_present=ch.response is not None,source=str(file)))
    pd.DataFrame(stations.values()).to_csv(OUT/'stations.csv',index=False)
    pd.DataFrame(epochs).drop_duplicates().to_csv(OUT/'response_epochs.csv',index=False)
    intervals={}
    for r in coverage:intervals.setdefault(r['channel'],[]).append((r['start'],r['end']))
    totals=[]
    for ident,spans in sorted(intervals.items()):
        merged=[]
        for a,b in sorted(spans):
            if merged and a<=merged[-1][1]+.001:merged[-1][1]=max(b,merged[-1][1])
            else:merged.append([a,b])
        totals.append(dict(channel=ident,hours=sum(b-a for a,b in merged)/3600,intervals=merged))
    (OUT/'processed_coverage_union.json').write_text(json.dumps(totals,indent=2)+'\n')
    return frame


def associate():
    from gamma.utils import association
    np.random.seed(0)
    frame=assemble();station=pd.read_csv(OUT/'stations.csv')
    profile=pd.read_csv(OUT/'alternative_starting_profile.csv')
    z=[-.5];p=[float(profile.vp_km_s.iloc[0])];s=[float(profile.vs_km_s.iloc[0])]
    for i,r in profile.iterrows():
        if i:
            z.append(float(r.depth_top_km_bsl)-.00001);p.append(p[-1]);s.append(s[-1])
        z.append(float(r.depth_top_km_bsl));p.append(float(r.vp_km_s));s.append(float(r.vs_km_s))
    config=dict(dims=['x(km)','y(km)','z(km)'],use_dbscan=True,use_amplitude=False,dbscan_eps=10,dbscan_min_samples=3,oversample_factor=5,initial_points=[1,1,1],min_picks_per_eq=6,min_p_picks_per_eq=0,min_s_picks_per_eq=0,max_sigma11=2,xlim=[-12,12],ylim=[-12,12],zlim=[0,8],bfgs_bounds=[(-12,12),(-12,12),(0,8),(None,None)],vel={'p':3.,'s':1.7},ncpu=6,covariance_prior=[1.])
    config['eikonal']=dict(vel=dict(z=z,p=p,s=s),h=.1,xlim=[-12,12],ylim=[-12,12],zlim=[-.5,8])
    config.update({'x(km)':[-12,12],'y(km)':[-12,12],'z(km)':[0,8]})
    Path('config/continuation_association.json').write_text(json.dumps(config,indent=2)+'\n')
    table=frame.rename(columns=dict(trace_id='id',time='timestamp',phase='type',probability='prob'))
    table['timestamp']=pd.to_datetime(table.timestamp,utc=True,format='ISO8601');table=table[table.id.isin(station.id)]
    events=[];assignments=[]
    trans=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    for day,g in table.groupby(table.timestamp.dt.date):
        ev,ass=association(g,station,copy.deepcopy(config),method='BGMM');offset=len(events)
        for e in ev:
            e['event_index']+=offset;e.pop('magnitude',None)
            e['longitude'],e['latitude']=trans.transform(e['x(km)'],e['y(km)'],direction='INVERSE')
        events.extend(ev);assignments.extend((i,j+offset,score) for i,j,score in ass)
        print(day,'picks',len(g),'events',len(ev),flush=True)
    # Parallel clusters can finish in different orders. Canonicalize identifiers
    # by origin time so the saved index is independent of scheduling.
    assert len({e['event_index'] for e in events})==len(events), 'Duplicate provisional event identifiers'
    events.sort(key=lambda e:(e['time'],e['x(km)'],e['y(km)'],e['z(km)']))
    remap={e['event_index']:i for i,e in enumerate(events)}
    for i,e in enumerate(events):e['event_index']=i
    assignments=sorted((i,remap[j],score) for i,j,score in assignments)
    pd.DataFrame(events).to_csv(OUT/'initial_events.csv',index=False)
    pd.DataFrame(assignments,columns=['pick_index','event_index','score']).to_csv(OUT/'associations.csv',index=False)
    checks=dict(probability_bounds=bool(frame.probability.between(.3,1).all()),excluded_s_absent=not any(r.phase=='S' and r.trace_id.split('.')[1] in SETTINGS['exclude_s'] for r in frame.itertuples()),minimum_six_picks=all(e['num_picks']>=6 for e in events),unique_assigned_picks=len({a[0] for a in assignments})==len(assignments),valid_pick_indices=all(0<=a[0]<len(frame) for a in assignments))
    assert all(checks.values()),checks
    cov=json.loads((OUT/'processed_coverage_union.json').read_text())
    summary=dict(picks=len(frame),p_picks=int((frame.phase=='P').sum()),s_picks=int((frame.phase=='S').sum()),events=len(events),assigned_picks=len(assignments),processed_channel_hours=sum(r['hours'] for r in cov),stations=sorted({r['channel'].split('.')[1] for r in cov}),files=pd.read_csv(OUT/'processed_coverage.csv').file.nunique(),checks=checks,status='Partial: published alternative starting profile, incomplete continuous acquisition, no VELEST/TomoDD final catalog.',alternative_profile='Tramelli et al. (2021), Table 1; not asserted identical to Calo--Tramelli (2018).',settings=SETTINGS)
    (OUT/'analysis_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['pick','associate','all']);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--frozen',action='store_true');ap.add_argument('--fresh',action='store_true');a=ap.parse_args()
    FROZEN=a.frozen
    if a.fresh:
        for p in CACHE.glob('*.json'):p.unlink()
    if a.mode in ['pick','all']:infer(a.workers)
    if a.mode in ['associate','all']:associate()
