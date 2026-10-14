"""Resume unchanged measurements after the generic TomoDD logging fix.

Calibration and differential-time measurements are retained with exact hash
checks. New downstream stages are executed and recorded; no old cohort fills gaps.
Stops before reviewed mechanism inversions so new waveform packets can be read.
"""
from pathlib import Path
import datetime,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';W=ROOT/'tmp/eida_continuation'
def main():
    env=dict(os.environ,CF_GRID_BASE='data/eida_continuation/calibration',CF_GRID_WORK='tmp/eida_continuation',CF_OBSERVATIONS='data/eida_continuation')
    stages=[('run_grid_tomodd.py',['--reuse-measurements']),('grid_uncertainty.py',[]),('downstream_checks.py',['--dataset','grid','--workers','4']),('magnitude_statistics.py',['--grid']),('grid_panel_data.py',[]),('grid_location_checks.py',[]),('validate_eida_holdout.py',[]),('eida_shallow_example.py',[]),('grid_focal_attempt.py',[]),('link_eida_candidates.py',[]),('mechanism_measurements.py',[]),('mechanism_unpicked.py',[]),('prepare_eida_mechanism_review.py',[])]
    for script,args in stages:
        if script=='mechanism_measurements.py':env.update(CF_MECH_OUT='data/mechanism_eida',CF_MECH_OBSERVATIONS='data/eida_continuation',CF_MECH_WORK='tmp/mechanism_eida',CF_MECH_DECISIONS='config/mechanism_eida_decisions.json',CF_MECH_LOCATIONS='data/mechanism_eida/candidate_locations.csv',CF_MECH_MODEL='data/eida_continuation/calibration/merged4/independent_calibrated.mod')
        path=D/'pipeline_execution.json';runs=json.loads(path.read_text());command=[sys.executable,'scripts/'+script,*args];log=W/('continued_'+script+'.log')
        row=dict(command=command,log=str(log.relative_to(ROOT)),returncode=None,state='running',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment={k:v for k,v in env.items() if k.startswith('CF_')})
        runs.append(row);path.write_text(json.dumps(runs,indent=2)+'\n')
        with log.open('w') as out:done=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        row.update(returncode=done.returncode,state='finished',ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());path.write_text(json.dumps(runs,indent=2)+'\n');print(script,done.returncode,flush=True)
        if done.returncode:raise SystemExit(done.returncode)
if __name__=='__main__':main()
