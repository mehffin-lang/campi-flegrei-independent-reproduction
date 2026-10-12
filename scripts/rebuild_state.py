"""Hash-verified resumption after a failed stage; never skip a changed result."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/continuation'
STATE=D/'resume_checkpoint.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(logs):
    passed=[]
    for row in logs:
        if row['returncode']:break
        passed.append(row)
    files=set()
    for row in passed:
        for arg in row['command']:
            p=Path(arg);p=p if p.is_absolute() else ROOT/p
            if p.is_file() and p.is_relative_to(ROOT):files.add(p)
    for directory in ['data','config']:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and p.name not in ['rebuild_log.json','rebuild_status.json','resume_checkpoint.json','rebuild_attempts.json','manifest.sha256'] and 'failed_attempt' not in p.name:files.add(p)
    state=dict(passed_commands=[r['command'] for r in passed],sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})
    STATE.write_text(json.dumps(state,indent=2)+'\n');return state
def verify():
    state=json.loads(STATE.read_text())
    for name,digest in state['sha256'].items():assert sha(ROOT/name)==digest,'Changed completed-stage dependency: '+name
    return state
