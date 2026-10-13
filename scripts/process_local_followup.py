"""Process omitted original observations and a bounded public acquisition batch.

Separate identifiers preserve the earlier cohort used for mechanism review.
Event-selected local archive windows are labeled and are never used as exposure
for continuous discovery. Only own numerical picks enter association.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
from obspy import read
import process_continuous as p
import extend_calibration_observations as checkpoint

ROOT=p.ROOT;D=ROOT/'data/local_extension'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pick-only',action='store_true');ap.add_argument('--frozen',action='store_true');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    D.mkdir(exist_ok=True)
    jobs=p.jobs();listed={j[0] for j in jobs};roles=[]
    files=list((ROOT/'inputs/local_inspection').glob('*.mseed'))+list((ROOT/'inputs/waveforms').glob('E*.mseed'))+[ROOT/'inputs/resumption/S4_CSOB_20240520.mseed']
    for file in sorted(files):
        source=str(file.relative_to(ROOT))
        if source in listed:continue
        st=read(str(file),headonly=True)
        job=(source,min(float(tr.stats.starttime) for tr in st),max(float(tr.stats.endtime)+1/tr.stats.sampling_rate for tr in st),hashlib.sha256(file.read_bytes()).hexdigest())
        jobs.append(job)
        roles.append(dict(file=source,role='Original observation in an event-selected short window; not continuous discovery exposure',channels=[tr.id for tr in st],start=job[1],end=job[2],sha256=job[3]))
    if args.frozen:
        jobs=[(r['file'],r['start'],r['end'],r['sha256']) for r in json.loads((D/'input_jobs.json').read_text())]
        roles=json.loads((D/'short_window_inputs.json').read_text())
        for file,a,b,h in jobs:assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==h,file
    p.jobs=lambda:jobs;p.OUT=D
    (D/'input_jobs.json').write_text(json.dumps([dict(file=f,start=a,end=b,sha256=h) for f,a,b,h in jobs],indent=2)+'\n')
    (D/'short_window_inputs.json').write_text(json.dumps(roles,indent=2)+'\n')
    shutil.copyfile(ROOT/'data/continuation/alternative_starting_profile.csv',D/'alternative_starting_profile.csv')
    p.infer(args.workers)
    if args.pick_only:return
    from reuse_own_associations import install
    install(ROOT,D,ROOT/'data/coverage_extension')
    p.associate()
    checkpoint.OUT=D;checkpoint.seal_expanded()
    # Associate ignores IDs absent from verified metadata; retain those picks
    # explicitly rather than silently claiming they were located.
    import pandas as pd
    picks=pd.read_csv(D/'picks.csv');stations=pd.read_csv(D/'stations.csv')
    picks[~picks.trace_id.isin(stations.id)].to_csv(D/'picks_without_metadata.csv',index=False)
    receipt=json.loads((D/'processing_checkpoint.json').read_text())
    receipt['files'][str(Path(__file__).resolve().relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt['classification']='Independent sparse observations and separately identified event-selected windows; provisional alternate-profile associations.'
    (D/'processing_checkpoint.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
