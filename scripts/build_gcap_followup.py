"""Build a disclosed gCAP port without proprietary numerical/filter libraries.

The unchanged grid-search/radiation code is the generic Zhu method resource.
Own Jacobi rotations replace the 3x3 curvature eigensolver; SciPy preprocessing
performs filtering before this binary is called. Internal filter calls abort.
Modified files and binary have distinct names as requested by the license.
No archive example, supplied Green function, observation or plotting code is used.
"""
from pathlib import Path
import json,hashlib,subprocess,re,tarfile
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'build/method_followup/gcap'
EIG=r'''
void principal_values(float a[]) {
  double m[3][3]={{a[0],a[3],a[4]},{a[3],a[1],a[5]},{a[4],a[5],a[2]}};
  int i,j,k,p=0,q=1;
  for(k=0;k<100;k++) {
    double best=0;
    for(i=0;i<3;i++) for(j=i+1;j<3;j++) if(fabs(m[i][j])>best) {best=fabs(m[i][j]);p=i;q=j;}
    if(best<1e-12*(1+fabs(m[0][0])+fabs(m[1][1])+fabs(m[2][2]))) break;
    double theta=.5*atan2(2*m[p][q],m[q][q]-m[p][p]);
    double c=cos(theta),s=sin(theta),pp=m[p][p],qq=m[q][q],pq=m[p][q];
    for(i=0;i<3;i++) if(i!=p && i!=q) {
      double ip=m[i][p],iq=m[i][q];m[i][p]=m[p][i]=c*ip-s*iq;m[i][q]=m[q][i]=s*ip+c*iq;
    }
    m[p][p]=c*c*pp-2*s*c*pq+s*s*qq;m[q][q]=s*s*pp+2*s*c*pq+c*c*qq;m[p][q]=m[q][p]=0;
  }
  double d[3]={m[0][0],m[1][1],m[2][2]};
  for(i=0;i<3;i++) for(j=i+1;j<3;j++) if(d[j]>d[i]) {double v=d[i];d[i]=d[j];d[j]=v;}
  for(i=0;i<3;i++) a[i]=fmax(d[i],.0001*d[0]);
}
'''
FILTER=r'''
/* Filtering is performed identically on observations and Green functions in
   the Python preparation. Fail closed if an internal filter is requested. */
void design(long int a,char *b,char *c,double d,double e,double f,double g,double h,float *i,float *j,long int *k) { fprintf(stderr,"Internal SAC filtering unavailable; externally prefilter\n"); exit(91); }
void apply(float *a,long int b,long c,float *d,float *e,long int f) { fprintf(stderr,"Internal SAC filtering unavailable; externally prefilter\n"); exit(92); }
'''
def main():
    B.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'inputs/extended/gcap.tar'
    with tarfile.open(archive) as tf:
        for member in tf.getmembers():
            if member.name.count('/')!=1:continue
            name=Path(member.name).name
            if Path(name).suffix in ['.c','.h','.f'] or name=='README':
                (B/name).write_bytes(tf.extractfile(member).read())
    h=(B/'cap.h').read_text().replace('#include "nr.h"','').replace('#include "nrutil.h"','')+'\nvoid design();\nvoid apply();\n'
    (B/'cap_followup.h').write_text(h)
    (B/'cap_followup.c').write_text((B/'cap.c').read_text().replace('"cap.h"','"cap_followup.h"'))
    sub=(B/'cap_sub.c').read_text().replace('"cap.h"','"cap_followup.h"')
    sub=re.sub(r'void principal_values\(float a\[\]\) \{.*?\n\}',lambda m:EIG.strip(),sub,flags=re.S)
    (B/'cap_sub_followup.c').write_text(sub+'\n'+FILTER)
    logs=[];objects=[]
    for name in ['cap_followup','cap_sub_followup','fft','Complex','radiats','grid3d','sacio','trap']:
        cmd=['cc','-O2','-c',name+'.c','-o',name+'.o'];r=subprocess.run(cmd,cwd=B,capture_output=True,text=True);logs.append(dict(command=cmd,returncode=r.returncode,output=r.stdout+r.stderr));objects.append(name+'.o')
        if r.returncode:break
    else:
        cmd=['gfortran','-O2','-std=legacy','-c','futterman.f'];r=subprocess.run(cmd,cwd=B,capture_output=True,text=True);logs.append(dict(command=cmd,returncode=r.returncode,output=r.stdout+r.stderr));objects.append('futterman.o')
        if not r.returncode:
            cmd=['gfortran','-o','cap_followup',*objects,'-lm'];r=subprocess.run(cmd,cwd=B,capture_output=True,text=True);logs.append(dict(command=cmd,returncode=r.returncode,output=r.stdout+r.stderr))
    (ROOT/'data/mechanism_followup/gcap_build.json').write_text(json.dumps(dict(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),modifications=__doc__,runs=logs),indent=2)+'\n')
    if r.returncode:raise RuntimeError(r.stderr)
    # Actual eigensolver consistency check against NumPy; purely mathematical,
    # not an empirical observation or paper figure.
    (B/'eigen_check.c').write_text('#include <math.h>\n'+EIG)
    subprocess.run(['cc','-shared','-fPIC','eigen_check.c','-lm','-o','eigen_check.so'],cwd=B,check=True)
    import ctypes,numpy as np
    lib=ctypes.CDLL(str(B/'eigen_check.so'));lib.principal_values.argtypes=[np.ctypeslib.ndpointer(dtype=np.float32,ndim=1,flags='C_CONTIGUOUS')]
    errors=[]
    for m in [np.diag([1.,2.,3.]),np.array([[4.,1.,.5],[1.,3.,.2],[.5,.2,2.]])]:
        a=np.array([m[0,0],m[1,1],m[2,2],m[0,1],m[0,2],m[1,2]],dtype=np.float32);lib.principal_values(a);errors.append(float(max(abs(a[:3]-np.linalg.eigvalsh(m)[::-1]))))
    assert max(errors)<1e-5
    (ROOT/'data/mechanism_followup/gcap_numerical_check.json').write_text(json.dumps(dict(test_only=True,max_eigenvalue_absolute_errors=errors),indent=2)+'\n')
    print('Built cap_followup; eigenvalue checks',errors)
if __name__=='__main__':main()
