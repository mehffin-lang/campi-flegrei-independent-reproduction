"""Install the checked zero-term optimization without altering active processes."""
from pathlib import Path
import datetime,hashlib,json,os,shutil
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    build=json.loads((D/'sparse_build.json').read_text());check=json.loads((D/'sparse_check.json').read_text())
    assert check['all_identical']
    assert sha(ROOT/'build/velest-portable.f')==build['source_sha256']
    assert sha(ROOT/'build/velest-sparse.f')==build['modified_source_sha256']
    original=ROOT/'tmp/eida_continuation/dense_build';original.mkdir(exist_ok=True)
    receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),method='Atomic executable replacement after six same-input observed-cohort comparisons. Running processes retain their original inode. Both precisions use the identical optimization; scientific controls unchanged.',binaries={})
    for bits in [32,64]:
        live=ROOT/f'build/velest{bits}';new=ROOT/f'build/velest{bits}_sparse'
        if not (original/live.name).exists():shutil.copyfile(live,original/live.name)
        receipt['binaries'][str(bits)]=dict(before=sha(live),after=sha(new))
        staged=ROOT/f'build/velest{bits}.pending';shutil.copyfile(new,staged);staged.chmod(0o755);os.replace(staged,live)
    receipt['existing_solver_directories']=[p.name for p in (ROOT/'tmp/eida_continuation/merged4').iterdir() if p.is_dir()]
    path=D/'sparse_adoption.json'
    if not path.exists():path.write_text(json.dumps(receipt,indent=2)+'\n')
    build['adopted']=True;(D/'sparse_build.json').write_text(json.dumps(build,indent=2)+'\n');print(receipt)
if __name__=='__main__':main()
