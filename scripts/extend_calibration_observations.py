"""Process the frozen additional observations without renumbering the pilot.

The 1,003-event calibration cohort stays immutable. This separate expanded
checkpoint uses the same documented inference/association implementation.
"""
from pathlib import Path
import argparse,json,shutil,hashlib
import process_continuous as p
ROOT=p.ROOT;OUT=ROOT/'data/calibration_followup/expanded'

def seal_expanded():
    paths=[OUT/name for name in ['input_jobs.json','picks.csv','initial_events.csv','associations.csv','analysis_summary.json','processed_coverage.csv','processed_coverage_union.json','stations.csv','alternative_starting_profile.csv']]
    paths += [ROOT/name for name in ['scripts/process_continuous.py','scripts/gamma_reproducibility.py','config/continuation_association.json','data/extended/picks.csv','inputs/models/phasenet_retrained.pt','inputs/models/phasenet_retrained.json']]
    (OUT/'processing_checkpoint.json').write_text(json.dumps(dict(
        classification='Independently computed inference/association checkpoint; not accepted earthquake locations',
        command='.venv/bin/python scripts/extend_calibration_observations.py --workers 8',
        inference='Compatible per-file caches are reused only after input/settings/model/implementation hash checks.',
        files={str(file.relative_to(ROOT)):hashlib.sha256(file.read_bytes()).hexdigest() for file in paths}),indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=8);parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    manifest=OUT/'input_jobs.json'
    if args.freeze:
        manifest.write_text(json.dumps([dict(file=f,start=a,end=b,sha256=h) for f,a,b,h in p.jobs()],indent=2)+'\n')
    jobs=json.loads(manifest.read_text())
    for r in jobs:assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256'],r['file']
    p.jobs=lambda:[(r['file'],r['start'],r['end'],r['sha256']) for r in jobs]
    p.OUT=OUT
    shutil.copy2(ROOT/'data/continuation/alternative_starting_profile.csv',OUT/'alternative_starting_profile.csv')
    p.infer(args.workers);p.associate()
    # The main pilot is deliberately not overwritten: its event indices are
    # referenced by waveform delays, fits and uncertainties already calculated.
    (OUT/'scope.json').write_text(json.dumps(dict(role='Expanded independent picking/association checkpoint; uncalibrated',
        calibration_cohort='data/continuation/initial_events.csv',calibration_events=1003,
        relationship='Not substituted for the frozen calibration cohort; no shared event-index assumption.',
        command='.venv/bin/python scripts/extend_calibration_observations.py --workers 8'),indent=2)+'\n')
    seal_expanded()

if __name__=='__main__':main()
