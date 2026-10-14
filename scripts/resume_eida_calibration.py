"""Resume after preserving the physically inadmissible calibration attempt."""
from pathlib import Path
import datetime,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';W=ROOT/'tmp/eida_continuation'
def main():
    receipt=D/'pipeline_execution.json';runs=json.loads(receipt.read_text())
    for script,label in [('calibrate_eida_followup.py','regularized_calibration'),('validate_eida_holdout.py','heldout')]:
        command=[sys.executable,'scripts/'+script];log=W/(label+'.log')
        r=dict(command=command,log=str(log.relative_to(ROOT)),returncode=None,state='running',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='Explicit uniform velocity damping after archived negative-bulk-modulus trial; unchanged observations and gates.')
        runs.append(r);receipt.write_text(json.dumps(runs,indent=2)+'\n')
        with log.open('w') as out:done=subprocess.run(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
        r.update(returncode=done.returncode,state='finished',ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());receipt.write_text(json.dumps(runs,indent=2)+'\n');print(label,done.returncode,flush=True)
        if done.returncode:raise SystemExit(done.returncode)
if __name__=='__main__':main()
