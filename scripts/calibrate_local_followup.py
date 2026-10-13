"""Run independent calibration and relocation on the new frozen local cohort."""
from pathlib import Path
import os,json,subprocess,shutil,datetime
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/local_extension';B=D/'calibration';W=ROOT/'tmp/local_extension'
def main():
    B.mkdir(exist_ok=True);W.mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'data/grid_calibration/source_access.json',B/'source_access.json')
    env=dict(os.environ,CF_GRID_BASE=str(B.relative_to(ROOT)),CF_GRID_WORK=str(W.relative_to(ROOT)),CF_OBSERVATIONS=str(D.relative_to(ROOT)))
    receipt=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scientifically_accepted=False,runs=[])
    stages=[('prepare_grid_calibration.py',[]),('run_grid_velest.py',['--coarse-four']),('validate_grid_velest.py',[]),('run_grid_tomodd.py',[]),('grid_uncertainty.py',[]),('downstream_checks.py',['--dataset','grid','--workers','4']),('magnitude_statistics.py',['--grid']),('grid_panel_data.py',[]),('grid_location_checks.py',[])]
    for script,args in stages:
        command=[str(ROOT/'.venv/bin/python'),'scripts/'+script,*args];log=W/(script+'.log')
        with log.open('w') as out:r=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        receipt['runs'].append(dict(command=command,environment={k:v for k,v in env.items() if k.startswith('CF_')},returncode=r.returncode,log=str(log.relative_to(ROOT))))
        (D/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(script,r.returncode,flush=True)
        if r.returncode:receipt['failed_stage']=script;break
        if script=='run_grid_velest.py' and not (B/'merged4/filtered_events.csv').exists():receipt['failed_stage']='No usable full-cohort VELEST output';break
    receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(D/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if 'failed_stage' in receipt:raise SystemExit(1)
if __name__=='__main__':main()
