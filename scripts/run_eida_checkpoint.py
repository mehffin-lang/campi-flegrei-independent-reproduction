"""Consume the active bounded retrieval, then execute the new catalog workflow.

Run after collect_eida_followup has started. Per-file picker caches permit
resumption; the final association checkpoint freezes the successfully downloaded
files. The retrieval queue is never mistaken for observation coverage.
"""
import datetime,json,sqlite3,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';W=ROOT/'tmp/eida_continuation'

def main():
    runs=[];last=0
    def run(script,args,label):
        cmd=[str(ROOT/'.venv/bin/python'),'scripts/'+script,*args];log=W/(label+'.log')
        start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with log.open('w') as out:r=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
        runs.append(dict(command=cmd,log=str(log.relative_to(ROOT)),returncode=r.returncode,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        (D/'pipeline_execution.json').write_text(json.dumps(runs,indent=2)+'\n')
        print(label,r.returncode,flush=True)
        if r.returncode:raise SystemExit(r.returncode)
    while True:
        c=sqlite3.connect(ROOT/'inputs/continuation/acquisition.sqlite');states=dict(c.execute('select status,count(*) from jobs group by status'));c.close()
        n=states.get('downloaded',0);active=states.get('running',0)
        if n-last>=8 or not active:
            run('process_eida_followup.py',['--freeze','--pick-only','--workers','4'],'picking_'+str(n));last=n
        if not active:break
        time.sleep(15)
    run('process_eida_followup.py',[],'association')
    run('calibrate_eida_followup.py',[],'calibration')
    run('validate_eida_holdout.py',[],'heldout')

if __name__=='__main__':main()
