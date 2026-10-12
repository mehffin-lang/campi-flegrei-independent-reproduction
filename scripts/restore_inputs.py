"""Restore the frozen input snapshot; refuse silently changed server content."""
from pathlib import Path
import argparse,hashlib,json,subprocess,concurrent.futures,zipfile
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--continuation',action='store_true');args=parser.parse_args()
    rows=json.loads((ROOT/'docs/rebuild_inputs.json').read_text())
    if args.continuation:
        more=json.loads((ROOT/'docs/continuation_rebuild_inputs.json').read_text());known={r['file'] for r in rows};rows += [r for r in more if r['file'] not in known]
        meta=json.loads((ROOT/'docs/continuation_source_bundle.json').read_text());bundle=ROOT/meta['file']
        assert hashlib.sha256(bundle.read_bytes()).hexdigest()==meta['sha256']
        with zipfile.ZipFile(bundle) as z:
            assert set(z.namelist())==set(meta['members']) and z.testzip() is None
            for name in z.namelist():
                p=(ROOT/name).resolve();assert p.is_relative_to(ROOT/'inputs/continuation')
                if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        meta=json.loads((ROOT/'docs/revision_source_bundle.json').read_text());bundle=ROOT/meta['file']
        assert hashlib.sha256(bundle.read_bytes()).hexdigest()==meta['sha256']
        known={r['file'] for r in rows}
        rows += [r for r in meta.get('external_sources',[]) if r['file'] not in known]
        with zipfile.ZipFile(bundle) as z:
            assert set(z.namelist())=={r['file'] for r in meta['members']} and z.testzip() is None
            for row in meta['members']:
                p=(ROOT/row['file']).resolve();assert p.is_relative_to(ROOT/'inputs/revision')
                raw=z.read(row['file']);assert hashlib.sha256(raw).hexdigest()==row['sha256']
                if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(restore,rows):print('Verified',name,flush=True)
