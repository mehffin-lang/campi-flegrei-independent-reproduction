"""Continuous-file checkpoint; excludes every known event-selected snippet.

Prior own daily associations are reused only for exact numerical input, station
table and configuration matches. Inference caches also verify waveform/model/
implementation hashes. No paper result or external event catalog is read.
"""
import argparse,hashlib,json,shutil
import pandas as pd
import process_continuous as p
import extend_calibration_observations as checkpoint

ROOT=p.ROOT;D=ROOT/'data/eida_continuation'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');ap.add_argument('--pick-only',action='store_true');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    excluded={r['file'] for r in json.loads((ROOT/'data/local_extension/short_window_inputs.json').read_text())}
    baseline=pd.read_csv(ROOT/'data/extended/picks.csv')
    assert not set(baseline.source)&excluded, 'Baseline contains event-selected picks'
    if a.freeze:
        jobs=[j for j in p.jobs() if j[0] not in excluded]
        (D/'input_jobs.json').write_text(json.dumps([dict(file=f,start=x,end=y,sha256=h) for f,x,y,h in jobs],indent=2)+'\n')
    jobs=[(r['file'],r['start'],r['end'],r['sha256']) for r in json.loads((D/'input_jobs.json').read_text())]
    for f,x,y,h in jobs:assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    p.jobs=lambda:jobs;p.OUT=D
    shutil.copyfile(ROOT/'data/continuation/alternative_starting_profile.csv',D/'alternative_starting_profile.csv')
    p.infer(a.workers)
    if a.pick_only:return
    original=p.assemble
    def assemble():
        frame=original();assert not set(frame.source)&excluded
        cov=pd.read_csv(D/'processed_coverage.csv');removed=cov[cov.file.isin(excluded)].copy();cov=cov[~cov.file.isin(excluded)].copy()
        removed.to_csv(D/'excluded_event_selected_coverage.csv',index=False);cov.to_csv(D/'processed_coverage.csv',index=False)
        union=[]
        for channel,g in cov.groupby('channel'):
            spans=[]
            for x,y in sorted(zip(g.start,g.end)):
                if spans and x<=spans[-1][1]+.001:spans[-1][1]=max(y,spans[-1][1])
                else:spans.append([x,y])
            union.append(dict(channel=channel,intervals=spans,hours=sum(y-x for x,y in spans)/3600))
        (D/'processed_coverage_union.json').write_text(json.dumps(union,indent=2)+'\n')
        roles=[]
        for f in sorted(set(cov.file)):
            file=ROOT/f
            purpose='Original continuous waveform interval; sparse calendar sampling, not complete exposure.'
            if '20240520T180000_20240521T000000' in f:purpose+=' Purposefully selected six-hour continuous block containing the written S4 benchmark; no independent discovery of the known swarm or population completeness is claimed.'
            roles.append(dict(file=f,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),bytes=file.stat().st_size,role=purpose))
        (D/'all_observation_inputs.json').write_text(json.dumps(roles,indent=2)+'\n')
        (D/'eligibility.json').write_text(json.dumps(dict(excluded_files=sorted(excluded),baseline_picks_contain_excluded_files=False,current_picks_contain_excluded_files=False,excluded_coverage_rows=len(removed),rule=__doc__),indent=2)+'\n')
        return frame
    p.assemble=assemble
    from reuse_own_associations import install
    install(ROOT,D,ROOT/'data/coverage_extension')
    p.associate();checkpoint.OUT=D;checkpoint.seal_expanded()
    receipt=json.loads((D/'processing_checkpoint.json').read_text())
    for f in [__file__,D/'all_observation_inputs.json',D/'eligibility.json']:
        f=__import__('pathlib').Path(f).resolve();receipt['files'][str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    receipt['classification']='Own sparse continuous-observation inference and alternative-profile association; all known event-selected snippets excluded.'
    (D/'processing_checkpoint.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':main()
