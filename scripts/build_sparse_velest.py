"""Skip provably zero leading Cholesky entries; retain global VELEST updates.

For an SPD matrix, entries of a Cholesky row before its first nonzero input
entry remain zero. Only these zero products are omitted. Nonzero arithmetic,
global step-length/backtracking, damping and convergence controls are unchanged.
This is not separate event batching and is tested on the actual observed cohort.
"""
from pathlib import Path
import hashlib,json,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=ROOT/'build/velest-portable.f';dest=ROOT/'build/velest-sparse.f'
    original=source.read_text();start=original.index('      subroutine LUDECP');end=original.index('      subroutine luelmp',start)
    body=original[start:end].replace('integer ip,i,iq,ir,j,k,ip1','integer ip,i,iq,ir,j,k,ip1,first')
    body=body.replace('         do 40 j=1,i\n', '''         first=i
         do j=1,i
            if (a(ip+j-1).ne.zero) then
               first=j
               exit
            endif
         enddo
         do 40 j=1,i
            if (j.lt.first) then
               ul(ip)=zero
               ip1=ip
               ip=ip+1
               ir=ir+j
               goto 40
            endif
''')
    body=body.replace('            do 5  k=iq,ip1','            ir=ir+first-1\n            do 5  k=iq+first-1,ip1')
    assert 'first=i' in body and 'k=iq+first-1' in body
    dest.write_text(original[:start]+body+original[end:]);runs=[]
    for bits in [32,64]:
        binary=ROOT/f'build/velest{bits}_sparse'
        cmd=['gfortran','-std=legacy','-O2','-fcheck=bounds','-mcmodel=medium']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I','build',str(dest.relative_to(ROOT)),'-o',str(binary.relative_to(ROOT))]
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,env=dict(os.environ,TMPDIR=str(ROOT/'tmp/eida_continuation')))
        runs.append(dict(command=cmd,returncode=r.returncode,compiler_output=r.stdout+r.stderr));r.check_returncode();runs[-1]['binary_sha256']=sha(binary)
    (ROOT/'data/eida_continuation/sparse_build.json').write_text(json.dumps(dict(method=__doc__,source_sha256=sha(source),modified_source_sha256=sha(dest),header_sha256=sha(ROOT/'build/vel_com.f'),runs=runs,adopted=False),indent=2)+'\n')
if __name__=='__main__':main()
