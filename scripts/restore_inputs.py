"""Restore the frozen input snapshot; refuse silently changed server content."""
from pathlib import Path
import hashlib,json,subprocess,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
def restore(row):
    p=ROOT/row['file'];p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
        part=Path(str(p)+'.part')
        subprocess.run(['curl','-fLSs','--retry','2','--connect-timeout','20','--max-time','1800',row['url'],'-o',str(part)],check=True)
        if hashlib.sha256(part.read_bytes()).hexdigest()!=row['sha256']:
            raise RuntimeError('Server content differs from frozen snapshot: '+row['file']+'; expected SHA-256 '+row['sha256']+'. Supply the recorded snapshot or explicitly audit and regenerate the manifest.')
        part.replace(p)
    assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['file']
    return row['file']
if __name__=='__main__':
    rows=json.loads((ROOT/'docs/rebuild_inputs.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(restore,rows):print('Verified',name,flush=True)
