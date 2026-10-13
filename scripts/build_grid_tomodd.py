"""Build permitted generic TomoDD with bounds checks; exclude example analyses."""
from pathlib import Path
import hashlib,json,tarfile,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def main():
    work=ROOT/'build/grid_tomodd';work.mkdir(exist_ok=True)
    source=ROOT/'inputs/external/tomodd';files=[]
    receipt=json.loads((ROOT/'docs/tomodd_source_receipt.json').read_text());archive=ROOT/receipt['file']
    if not archive.exists():
        archive.parent.mkdir(parents=True,exist_ok=True);urllib.request.urlretrieve(receipt['url'],archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256']
    prefix='USTC-tomoDD-SE-training2020/Src/tomoDD-SE/'
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.startswith(prefix):continue
            relative=Path(member.name[len(prefix):]);assert '..' not in relative.parts and not relative.is_absolute()
            if relative.suffix not in ['.f','.c','.inc','.h'] and relative.name!='Makefile':continue
            dest=source/relative;raw=tar.extractfile(member).read()
            if dest.exists():assert dest.read_bytes()==raw,'Unrecorded generic-source modification: '+str(dest)
            else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    for p in source.rglob('*'):
        if not p.is_file() or (p.suffix not in ['.f','.c','.inc','.h'] and p.name!='Makefile'):continue
        dest=work/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());files.append(dict(source=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    p=work/'getdata_SPDR.f';text=p.read_text();old='108      if (iphase.ne.2) then';assert text.count(old)==1
    p.write_text(text.replace(old,'108      close(iunit)\n         if (iphase.ne.2) then'))
    main=work/'tomoDD-SE.f';text=main.read_text();old="open(iunit,file=fn_res,status='unknown')";assert text.count(old)==1
    main.write_text(text.replace(old,"open(iunit,file=fn_res,status='unknown',position='append')"))
    r=subprocess.run(['make','-B','FFLAGS=-O2 -I./include -ffixed-line-length-none -ffloat-store -fcheck=bounds -m64 -mcmodel=medium'],cwd=work,capture_output=True,text=True)
    (ROOT/'tmp/grid_calibration/tomodd_build.log').write_text(r.stdout+r.stderr)
    receipt=dict(source_receipt='docs/tomodd_source_receipt.json',files=files,returncode=r.returncode,command=r.args,changes='No equation changes; bounds checking and O2 compilation. getdata_SPDR.f: close the absolute-arrival unit at EOF label 108. tomoDD-SE.f: append per-cluster residual tables rather than overwrite earlier clusters. The wrapper deletes old output files before each run.',patched_getdata_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),patched_main_sha256=hashlib.sha256(main.read_bytes()).hexdigest())
    (ROOT/'data/grid_calibration/tomodd_build.json').write_text(json.dumps(receipt,indent=2)+'\n');r.check_returncode()
if __name__=='__main__':main()
