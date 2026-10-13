"""Portable current request ledger; actual samples, never requested coverage."""
from pathlib import Path
import datetime,gzip,hashlib,json,sqlite3,subprocess
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/coverage_extension'
def main():
    temporary=ROOT/'tmp/coverage_extension/acquisition.sqlite';temporary.parent.mkdir(exist_ok=True)
    source=sqlite3.connect(f'file:{ROOT}/inputs/continuation/acquisition.sqlite?mode=ro',uri=True)
    assert source.execute("SELECT count(*) FROM jobs WHERE status='running'").fetchone()[0]==0,'Acquisition still running'
    target=sqlite3.connect(temporary);source.backup(target);target.close();source.close()
    archive=D/'acquisition.sqlite.gz';archive.write_bytes(gzip.compress(temporary.read_bytes(),mtime=0))
    receipt=dict(file=str(archive.relative_to(ROOT)),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),role='Includes pending/failed requests. Only header-verified successful sample intervals count.')
    (D/'acquisition_snapshot.json').write_text(json.dumps(receipt,indent=2)+'\n')
    current=json.loads((ROOT/'data/continuation/acquisition_summary.json').read_text())
    (D/'acquisition_summary.json').write_text(json.dumps(current,indent=2)+'\n')
    manifest=json.loads((D/'input_jobs.json').read_text());files={r['file'] for r in manifest}
    raw=json.loads((ROOT/'docs/continuous_retrievals.json').read_text())
    receipts=[r for r in raw if r.get('file') in files and r.get('status')=='downloaded']
    (D/'retrieval_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    for script,extra in [('audit_continuation.py',[]),('acquisition_ledger.py',['--snapshot','data/coverage_extension/acquisition_snapshot.json'])]:
        subprocess.run([str(ROOT/'.venv/bin/python'),'scripts/'+script,'--data-dir','data/coverage_extension',*extra],cwd=ROOT,check=True)
    print(receipt)
if __name__=='__main__':main()
