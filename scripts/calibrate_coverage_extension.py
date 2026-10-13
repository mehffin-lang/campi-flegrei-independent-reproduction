"""Run the same independent calibration/relocation on the separately frozen extension.

Never join its integer event IDs to the original 1,015-association cohort.
"""
from pathlib import Path
import os,json,subprocess,shutil,datetime
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/coverage_extension';OUT=D/'calibration';WORK=ROOT/'tmp/coverage_extension'
def main():
    OUT.mkdir(exist_ok=True);WORK.mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'data/grid_calibration/source_access.json',OUT/'source_access.json')
    env=dict(os.environ,CF_GRID_BASE=str(OUT.relative_to(ROOT)),CF_GRID_WORK=str(WORK.relative_to(ROOT)),CF_OBSERVATIONS=str(D.relative_to(ROOT)))
    record=dict(cohort='data/coverage_extension',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,runs=[])
    for script,args in [('prepare_grid_calibration.py',[]),('run_grid_velest.py',['--coarse-four']),('validate_grid_velest.py',[]),('run_grid_tomodd.py',[])]:
        command=[str(ROOT/'.venv/bin/python'),'scripts/'+script,*args];log=WORK/(script+'.log')
        with log.open('w') as output:r=subprocess.run(command,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
        record['runs'].append(dict(command=command,returncode=r.returncode,log=str(log.relative_to(ROOT))))
        if r.returncode:record['failed_stage']=script;break
        if script=='run_grid_velest.py' and not (OUT/'merged4/filtered_events.csv').exists():record['failed_stage']='No physical full-cohort location output; see calibration summary';break
    record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['input_scope']=json.loads((D/'analysis_summary.json').read_text())
    (OUT/'execution.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
