"""Continue independent checks after the current numerical checkpoint finishes.

Stops before mechanism inversion so newly available packets can be visually
reviewed. Human review is not replaced by this command.
"""
from pathlib import Path
import datetime,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';W=ROOT/'tmp/eida_continuation'
def main():
    def wait_for(path):
        while not path.exists():
            receipt=D/'pipeline_execution.json'
            if receipt.exists():
                runs=json.loads(receipt.read_text())
                if runs and runs[-1]['returncode']:raise RuntimeError('Numerical pipeline failed; inspect '+str(receipt))
            time.sleep(15)
    wait_for(D/'eligibility.json') # Written after final observation assembly.
    records=[]
    def run(script,*args,env=None):
        cmd=[str(ROOT/'.venv/bin/python'),'scripts/'+script,*args];log=W/('post_'+script+'.log')
        with log.open('w') as out:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        records.append(dict(command=cmd,returncode=r.returncode,log=str(log.relative_to(ROOT))));(D/'post_execution.json').write_text(json.dumps(records,indent=2)+'\n');print(script,r.returncode,flush=True)
        if r.returncode:raise RuntimeError(str(log))
    run('extend_hybrid_scan.py','--dataset','grid','--output','data/eida_continuation/hybrid','--input-manifest','data/eida_continuation/input_jobs.json')
    run('hybrid_eida_followup.py')
    wait_for(D/'analysis_summary.json')
    run('audit_continuation.py','--data-dir','data/eida_continuation')
    env=dict(os.environ,CF_GRID_BASE='data/eida_continuation/calibration',CF_GRID_WORK='tmp/eida_continuation',CF_OBSERVATIONS='data/eida_continuation')
    run('catalog_frequency_index.py',env=env)
    wait_for(D/'calibration/merged4/heldout/summary.json')
    run('grid_focal_attempt.py',env=env)
    run('link_eida_candidates.py')
    env.update(CF_MECH_OUT='data/mechanism_eida',CF_MECH_OBSERVATIONS='data/eida_continuation',CF_MECH_WORK='tmp/mechanism_eida',CF_MECH_DECISIONS='config/mechanism_eida_decisions.json',CF_MECH_LOCATIONS='data/mechanism_eida/candidate_locations.csv',CF_MECH_MODEL='data/eida_continuation/calibration/merged4/independent_calibrated.mod')
    run('mechanism_measurements.py',env=env);run('mechanism_unpicked.py',env=env);run('prepare_eida_mechanism_review.py')
if __name__=='__main__':main()
