"""Increase generic TomoDD observation capacity for the measured EIDA cohort.

Array capacities and zero-observation diagnostic logging change relative to the previous bounds-checked build; no inverse equations change.
The existing EOF-close and per-cluster residual-append fixes are retained.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=ROOT/'inputs/external/tomodd';work=ROOT/'build/grid_tomodd';prior=ROOT/'tmp/eida_continuation/previous_tomodd';prior.mkdir(exist_ok=True)
    for name in ['tomoDD-SE','include/tomoFDD.inc']:
        p=work/name;q=prior/Path(name).name
        if p.exists() and not q.exists():shutil.copyfile(p,q)
    inputs={}
    for p in source.rglob('*'):
        if not p.is_file() or (p.suffix not in ['.f','.c','.inc','.h'] and p.name!='Makefile'):continue
        q=work/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());inputs[str(p.relative_to(ROOT))]=sha(p)
    p=work/'getdata_SPDR.f';s=p.read_text();old='108      if (iphase.ne.2) then';assert s.count(old)==1;p.write_text(s.replace(old,'108      close(iunit)\n         if (iphase.ne.2) then'))
    p=work/'tomoDD-SE.f';s=p.read_text();old="open(iunit,file=fn_res,status='unknown')";assert s.count(old)==1;p.write_text(s.replace(old,"open(iunit,file=fn_res,status='unknown',position='append')"))
    p=work/'tomoDD-SE.f';s=p.read_text()
    s=s.replace('           cohav= cohav/ncc','           if(ncc.gt.0) cohav= cohav/ncc').replace('           picav= picav/nct','           if(nct.gt.0) picav= picav/nct')
    s=s.replace("           write(log,'(\"  mean phase coherency = \",f5.3)')cohav", "           if(ncc.gt.0) then\n           write(log,'(\"  mean phase coherency = \",f5.3)')cohav\n           else\n           write(log,*) 'No waveform-correlation observations in cluster'\n           endif")
    s=s.replace('           tmpr2= 0\n           do i= 1,nsta','           tmpr2= 0\n           k=1\n           l=1\n           do i= 1,nsta')
    s=s.replace("           if(idata.eq.1.or.idata.eq.3) then\n              write(log,'(\"  station with largest cc rms", "           if((idata.eq.1.or.idata.eq.3).and.ncc.gt.0) then\n              write(log,'(\"  station with largest cc rms")
    p.write_text(s)
    p=work/'include/tomoFDD.inc';s=p.read_text();assert 'MAXDATA=  40000' in s and 'MAXCL=    50' in s
    p.write_text(s.replace('MAXDATA=  40000','MAXDATA=  150000').replace('MAXCL=    50','MAXCL=    1650'))
    cmd=['make','-B','FFLAGS=-O2 -I./include -ffixed-line-length-none -ffloat-store -fcheck=bounds -m64 -mcmodel=medium']
    run=subprocess.run(cmd,cwd=work,capture_output=True,text=True)
    log=ROOT/'tmp/eida_continuation/tomodd_capacity_build.log';log.write_text(run.stdout+run.stderr)
    record=dict(command=cmd,returncode=run.returncode,source_receipt='docs/tomodd_source_receipt.json',source_files=inputs,changes=__doc__,capacities=dict(MAXEVE=1650,MAXDATA=150000,MAXCL=1650),header_sha256=sha(p),patched_main_sha256=sha(work/'tomoDD-SE.f'),patched_getdata_sha256=sha(work/'getdata_SPDR.f'),prior_binary_sha256=sha(prior/'tomoDD-SE'),log=str(log.relative_to(ROOT)))
    if run.returncode==0:record['binary_sha256']=sha(work/'tomoDD-SE')
    (ROOT/'data/eida_continuation/tomodd_build.json').write_text(json.dumps(record,indent=2)+'\n');run.check_returncode();print(record)
if __name__=='__main__':main()
