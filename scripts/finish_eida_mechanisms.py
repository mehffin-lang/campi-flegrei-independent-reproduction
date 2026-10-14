"""Run reviewed mechanism trials after explicit inspection of changed packets."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/eida_continuation'
M = ROOT / 'data/mechanism_eida'

def main():
    review = json.loads((M / 'new_visual_review.json').read_text())
    assert review['human_reviews'] == 0
    assert review['measurements_sha256'] == hashlib.sha256((M / 'measurements.csv').read_bytes()).hexdigest()
    env = dict(os.environ, CF_MECH_OUT='data/mechanism_eida',
               CF_MECH_OBSERVATIONS='data/eida_continuation',
               CF_MECH_WORK='tmp/mechanism_eida',
               CF_MECH_DECISIONS='config/mechanism_eida_decisions.json',
               CF_MECH_LOCATIONS='data/mechanism_eida/candidate_locations.csv',
               CF_MECH_MODEL='data/eida_continuation/calibration/merged4/independent_calibrated.mod')
    for script, args in [('run_reviewed_skhash.py', []), ('run_gcap_followup.py', []),
                         ('run_gcap_followup.py', ['--high-band']),
                         ('validate_mechanism_followup.py', [])]:
        path = D / 'pipeline_execution.json'
        records = json.loads(path.read_text())
        command = [sys.executable, 'scripts/' + script, *args]
        log = ROOT / 'tmp/eida_continuation' / (script + ('_high' if args else '') + '.log')
        row = dict(command=command, log=str(log.relative_to(ROOT)), state='running',
                   started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   environment={k: v for k, v in env.items() if k.startswith('CF_')})
        records.append(row)
        path.write_text(json.dumps(records, indent=2) + '\n')
        with log.open('w') as out:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT)
        row.update(returncode=result.returncode, state='finished',
                   ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        path.write_text(json.dumps(records, indent=2) + '\n')
        print(script, args, result.returncode, flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
