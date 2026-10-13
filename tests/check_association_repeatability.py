"""Serial/parallel association equivalence on two observed event windows.

The windows were chosen from the project's own baseline waveform reviews;
neither a published catalog nor author picks defines them. This tests software
repeatability, not earthquake or phase accuracy. No empirical catalog is edited.
"""
from pathlib import Path
import os,sys,copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'))
sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
import pandas as pd
from gamma_reproducibility import install
from gamma.utils import association


def main():
    install()
    source=ROOT/'data/continuation/picks.csv'
    picks=pd.read_csv(source).rename(columns=dict(trace_id='id',time='timestamp',phase='type',probability='prob'))
    picks['timestamp']=pd.to_datetime(picks.timestamp,utc=True,format='ISO8601')
    starts=['2025-03-19T11:54:50Z','2025-03-20T03:17:56Z']
    selected=np.zeros(len(picks),dtype=bool)
    for start in starts:
        t=pd.Timestamp(start);selected|=picks.timestamp.between(t,t+pd.Timedelta(seconds=40)).to_numpy()
    picks=picks[selected];stations=pd.read_csv(ROOT/'data/continuation/stations.csv')
    config=json.loads((ROOT/'config/continuation_association.json').read_text())
    results=[]
    for workers,seed in [(1,19),(3,701)]:
        np.random.seed(seed);cfg=copy.deepcopy(config);cfg['ncpu']=workers
        events,assigned=association(picks,stations,cfg,method='BGMM')
        events=sorted(events,key=lambda x:(x['time'],x['x(km)'],x['y(km)'],x['z(km)']))
        remap={r['event_index']:i for i,r in enumerate(events)}
        positions=np.array([[float(pd.Timestamp(r['time']).timestamp()),r['x(km)'],r['y(km)'],r['z(km)']] for r in events])
        assignments=sorted((int(i),remap[j]) for i,j,score in assigned)
        results.append((positions,assignments))
    assert len(results[0][0])>=2, 'Repeatability test must recover nonempty associations in both observation windows'
    assert results[0][0].shape==results[1][0].shape
    assert results[0][1]==results[1][1], 'Serial/parallel assignments changed'
    difference=np.max(abs(results[0][0]-results[1][0]),axis=0)
    assert difference[0]<1e-5 and np.max(difference[1:])<1e-7,difference
    record=dict(passed=True,classification='Software repeatability test using own picks on original observations; not detection/location validation',
        picks_file=str(source.relative_to(ROOT)),picks_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        selection_utc=starts,duration_s=40,picks=len(picks),associated_events=len(results[0][0]),assigned_picks=len(results[0][1]),
        workers=[1,3],different_parent_seeds=[19,701],maximum_origin_time_difference_s=float(difference[0]),
        maximum_coordinate_difference_km=float(np.max(difference[1:])),
        assumption='Independent cluster seed 42 + deterministic DBSCAN label; same permitted GaMMA equations and BGMM random_state=42.')
    (ROOT/'tests/results/association_repeatability.json').write_text(json.dumps(record,indent=2)+'\n')
    print(record)


if __name__=='__main__':main()
