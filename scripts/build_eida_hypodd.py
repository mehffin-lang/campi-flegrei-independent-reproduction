"""Guard zero-correlation diagnostic logging in the generic HypoDD solver."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    work=ROOT/'build/hypodd21/src/hypoDD';prior=ROOT/'tmp/eida_continuation/previous_hypodd';prior.mkdir(exist_ok=True)
    if not (prior/'hypoDD').exists():shutil.copyfile(work/'hypoDD',prior/'hypoDD')
    source=ROOT/'inputs/external/hypodd21/src/hypoDD/hypoDD.f'
    manifest=json.loads((ROOT/'data/calibration_followup/hypodd21_sources.json').read_text())
    expected=next(r['sha256'] for r in manifest if r['file']==str(source.relative_to(ROOT)));assert sha(source)==expected
    s=source.read_text();s=s.replace('      cohav= cohav/ncc','      if(ncc.gt.0) cohav= cohav/ncc').replace('      picav= picav/nct','      if(nct.gt.0) picav= picav/nct')
    s=s.replace('      tmpr2= 0\n      do i= 1,nsta','      tmpr2= 0\n      k=1\n      l=1\n      do i= 1,nsta')
    s=s.replace("      if(idata.eq.1.or.idata.eq.3) then\n         write(log,'(\"  station with largest cc rms", "      if((idata.eq.1.or.idata.eq.3).and.ncc.gt.0) then\n         write(log,'(\"  station with largest cc rms")
    s=s.replace("      write(log,'(\"  mean phase coherency = \",f5.3)')cohav", "      if(ncc.gt.0) then\n      write(log,'(\"  mean phase coherency = \",f5.3)')cohav\n      else\n      write(log,*) 'No waveform-correlation observations in cluster'\n      endif")
    p=work/'hypoDD.f';p.write_text(s)
    cmd=['make','FC=gfortran','LDFLAGS=','FFLAGS=-O2 -std=legacy -fcheck=bounds -I../../include']
    r=subprocess.run(cmd,cwd=work,capture_output=True,text=True);(ROOT/'tmp/eida_continuation/hypodd_logging_build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    receipt=dict(method=__doc__,command=cmd,returncode=r.returncode,original_source_sha256=expected,patched_main_sha256=sha(p),prior_binary_sha256=sha(prior/'hypoDD'),binary_sha256=sha(work/'hypoDD'),changes='Only guards for missing observations in diagnostic averages/station-index reporting. Existing capacities, matmult2 dummy extent correction, bounds checks, equations and controls unchanged.')
    (ROOT/'data/eida_continuation/hypodd_build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
if __name__=='__main__':main()
