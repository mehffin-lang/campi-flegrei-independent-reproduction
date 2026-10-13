"""Run supported downstream measurements on the separately numbered extension."""
from pathlib import Path
import os,json,datetime,subprocess
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/coverage_extension';W=ROOT/'tmp/coverage_extension'
def main():
    env=dict(os.environ,CF_GRID_BASE='data/coverage_extension/calibration',CF_GRID_WORK='tmp/coverage_extension',CF_OBSERVATIONS='data/coverage_extension')
    record=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runs=[],scientific_acceptance=False)
    for name,args in [('grid_uncertainty.py',[]),('downstream_checks.py',['--dataset','grid','--workers','6']),('magnitude_statistics.py',['--grid']),('grid_focal_attempt.py',[]),('grid_panel_data.py',[]),('grid_location_checks.py',[])]:
        command=[str(ROOT/'.venv/bin/python'),'scripts/'+name,*args];log=W/(name+'.log')
        with log.open('w') as stream:r=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record['runs'].append(dict(command=command,returncode=r.returncode,log=str(log.relative_to(ROOT))))
        (D/'downstream_execution.json').write_text(json.dumps(record,indent=2)+'\n')
        if r.returncode:record['failed_stage']=name;break
    record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['procedure_passed']='failed_stage' not in record
    (D/'downstream_execution.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
    if not record['procedure_passed']:raise SystemExit(1)
if __name__=='__main__':main()
