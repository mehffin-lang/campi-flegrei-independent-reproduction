"""Instrument the first divergent saved prelocation, without changing arithmetic."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/availability_extension/precision';W=ROOT/'tmp/availability_extension/precision'
def main():
    D.mkdir(parents=True,exist_ok=True);W.mkdir(parents=True,exist_ok=True)
    old=ROOT/'tmp/eida_continuation/merged4';names={64:'Pozzuoli_Solfatara_prelocation',32:'precision32_prelocation'}
    source=(ROOT/'build/velest-sparse.f').read_text()
    anchor='      call CHECKRAYPATH(rp,nrp)'
    insert='''      if (i.eq.251.and.nitt.le.4) then
         write(16,*) 'DIAG_RAY',nitt,ibackups,i,nobs,nrtn,jl,
     &    e(2,i),e(3,i),e(4,i),delta,ttt
      endif
'''
    assert source.count(anchor)==1;source=source.replace(anchor,insert+anchor)
    anchor='      call STEPLENGTHDAMP(damp)'
    insert='''      if (nitt.le.4) then
         write(16,*) 'DIAG_UPDATE',nitt,(b(j),j=1001,1004)
      endif
'''
    # Main program already declares j; no numerical expression is changed.
    assert source.count(anchor)==1;source=source.replace(anchor,insert+anchor)
    f=W/'diagnostic.f';f.write_text(source);records=[]
    for bits,name in names.items():
        binary=W/f'velest{bits}';cmd=['gfortran','-std=legacy','-O2','-fcheck=bounds','-mcmodel=medium','-I',str(ROOT/'build')]+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+[str(f),'-o',str(binary)]
        build=subprocess.run(cmd,capture_output=True,text=True);(W/f'build{bits}.log').write_text(build.stdout+build.stderr);build.check_returncode()
        run=W/str(bits);run.mkdir(exist_ok=True)
        for fn in ['input.mod','input.sta','input.cnv','velest.cmn']:(run/fn).write_bytes((old/name/fn).read_bytes())
        r=subprocess.run([str(binary)],cwd=run,capture_output=True,text=True,timeout=180);(run/'console.log').write_text(r.stdout+r.stderr);r.check_returncode()
        text=(run/'run.out').read_text();(D/f'trace{bits}.txt').write_text('\n'.join(x for x in text.splitlines() if 'DIAG_' in x)+'\n')
        assert (run/'output.cnv').read_bytes()==(old/name/'output.cnv').read_bytes(),'Diagnostic instrumentation changed result'
        records.append(dict(bits=bits,returncode=r.returncode,output_identical_to_saved=True,command=cmd,workdir=str(run.relative_to(ROOT))))
    ids=pd.read_csv(ROOT/'data/eida_continuation/calibration/merged4/selected_initial_events.csv').event_index.tolist()
    dump=dict(event_ordinal=251,event_index=int(ids[250]),runs=records,source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),original_sha256=hashlib.sha256((ROOT/'build/velest-sparse.f').read_bytes()).hexdigest())
    (D/'instrumentation.json').write_text(json.dumps(dump,indent=2)+'\n')
if __name__=='__main__':main()
