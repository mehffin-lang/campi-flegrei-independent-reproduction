"""Infer/associate only the targeted pre-2025 continuous training batches."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
import argparse,json,hashlib,copy,concurrent.futures,multiprocessing
import numpy as np,pandas as pd
from pyproj import Transformer
import process_continuous as p
from extend_velocity_training import R,D,I,C,END,sha,dump

def worker():
    p.CACHE=I/'pick_cache';p.initialize_worker()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pick-only',action='store_true');ap.add_argument('--tag',default='new_catalog');ap.add_argument('--day');ap.add_argument('--jobs',default='new_input_jobs.json');ap.add_argument('--base-picks');args=ap.parse_args()
    out=D/args.tag;out.mkdir(exist_ok=True);cache=I/'pick_cache';cache.mkdir(exist_ok=True)
    jobs=json.loads((D/args.jobs).read_text());identity=p.inference_identity();pending=[]
    if args.day:jobs=[j for j in jobs if str(p.UTCDateTime(j['start'])).startswith(args.day)]
    assert jobs and all(j['end']<END for j in jobs)
    for j in jobs:
        assert sha(R/j['file'])==j['sha256'];cp=cache/(hashlib.sha256(j['file'].encode()).hexdigest()[:20]+'.json')
        if cp.exists():
            rec=json.loads(cp.read_text());assert rec['input_sha256']==j['sha256'] and rec['settings']==p.SETTINGS and rec['inference_identity']==identity and rec['core_start']==j['start'] and rec['core_end']==j['end']
        else:pending.append((j['file'],j['start'],j['end'],j['sha256']))
    log=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,initializer=worker,mp_context=multiprocessing.get_context('spawn')) as pool:
        for r in pool.map(p.pick,pending):log.append(r);print(r,flush=True)
    dump(out/'inference_run.json',log);assert all(r['status']=='processed' for r in log)
    if args.pick_only:return
    frames=[];coverage=[];exposure=[]
    for j in jobs:
        rec=json.loads((cache/(hashlib.sha256(j['file'].encode()).hexdigest()[:20]+'.json')).read_text());frames.extend(rec['picks']);coverage.extend(rec['coverage']);exposure.extend(rec['prediction_coverage'])
    frame=pd.DataFrame(frames)
    if args.base_picks:
        base=pd.read_csv(D/args.base_picks);assert (base.time<'2025-01-01').all();assert not set(base.trace_id)&set(frame.trace_id),'Tie stations should be distinct from target array'
        frame=pd.concat([base,frame],ignore_index=True)
    frame=frame.sort_values('time').reset_index(drop=True);assert (frame.time<'2025-01-01').all()
    frame.to_csv(out/'picks.csv',index=False);pd.DataFrame(coverage).to_csv(out/'processed_coverage.csv',index=False);pd.DataFrame(exposure).to_csv(out/'prediction_coverage.csv',index=False)
    stations=pd.read_csv(C/'stations.csv');stations.to_csv(out/'stations.csv',index=False)
    config=json.loads((R/'config/continuation_association.json').read_text());config['ncpu']=2;dump(out/'association_config.json',config)
    dump(out/'input_jobs.json',jobs)
    from gamma_reproducibility import install
    install()
    from gamma.utils import association
    np.random.seed(0)
    table=frame.rename(columns=dict(trace_id='id',time='timestamp',phase='type',probability='prob'));table['timestamp']=pd.to_datetime(table.timestamp,utc=True,format='ISO8601')
    trans=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    events=[];assigned=[]
    for day,g in table.groupby(table.timestamp.dt.date):
        ev,ass=association(g,stations,copy.deepcopy(config),method='BGMM');offset=len(events)
        for e in ev:
            e['event_index']+=offset;e.pop('magnitude',None);e['longitude'],e['latitude']=trans.transform(e['x(km)'],e['y(km)'],direction='INVERSE')
        events.extend(ev);assigned.extend((i,j+offset,score) for i,j,score in ass);print(day,len(g),len(ev),flush=True)
    events.sort(key=lambda e:(e['time'],e['x(km)'],e['y(km)'],e['z(km)']));mapping={e['event_index']:i for i,e in enumerate(events)}
    for i,e in enumerate(events):e['event_index']=i
    assigned=sorted((i,mapping[j],s) for i,j,s in assigned)
    pd.DataFrame(events).to_csv(out/'initial_events.csv',index=False);pd.DataFrame(assigned,columns=['pick_index','event_index','score']).to_csv(out/'associations.csv',index=False)
    assert len({i for i,j,s in assigned})==len(assigned)
    dump(out/'summary.json',dict(input_files=len(jobs),picks=len(frame),P=int(frame.phase.eq('P').sum()),S=int(frame.phase.eq('S').sum()),events=len(events),assigned_picks=len(assigned),
        stations=sorted(frame.trace_id.unique()),input_channel_hours=sum(r['end']-r['start'] for r in coverage)/3600,
        configuration_sha256=sha(out/'association_config.json'),weights=identity,base_picks=args.base_picks,
        base_picks_sha256=sha(D/args.base_picks) if args.base_picks else None,
        scope='Targeted pre-2025 station data; provisional alternative-profile associations. '+('Includes event-selected network tie clips: no completeness/detection-rate claim.' if args.base_picks else 'Calendar-selected six-hour continuous windows only.')))

if __name__=='__main__':main()
