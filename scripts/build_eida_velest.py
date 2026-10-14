"""Increase generic VELEST array capacity for the expanded observed cohort.

The upstream common block explicitly permits changing array sizes. Arithmetic,
equations and inversion controls remain unchanged in both precision builds.
"""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    header=ROOT/'build/vel_com.f';source=ROOT/'build/velest-portable.f'
    saved=ROOT/'tmp/eida_continuation/prior_build';saved.mkdir(parents=True,exist_ok=True)
    for name in ['vel_com.f','velest32','velest64']:
        p=ROOT/'build'/name
        if p.exists() and not (saved/name).exists():shutil.copyfile(p,saved/name)
    text=header.read_text();text,n=re.subn(r'parameter\(ieq=\d+\)', 'parameter(ieq=4096)',text,count=1);assert n==1
    header.write_text(text)
    runs=[]
    for bits in [32,64]:
        cmd=['gfortran','-std=legacy','-O2','-fcheck=bounds','-mcmodel=medium']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I','build','build/velest-portable.f','-o',f'build/velest{bits}']
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,env=dict(os.environ,TMPDIR=str(ROOT/'tmp/eida_continuation')))
        runs.append(dict(bits=bits,command=cmd,returncode=r.returncode,compiler_output=r.stdout+r.stderr))
        print(r.stdout+r.stderr,flush=True)
        (ROOT/'tmp/eida_continuation/build_attempts.json').write_text(json.dumps(runs,indent=2)+'\n')
        r.check_returncode();runs[-1]['binary_sha256']=sha(ROOT/f'build/velest{bits}')
    record=dict(event_capacity=4096,previous_capacity=1024,reason='Expanded continuous-waveform event cohort may exceed the previous compiled capacity; generic upstream header allows array-size changes.',source_sha256=sha(source),header_sha256=sha(header),upstream_source='data/extended/velest_build.json',prior_header_sha256=sha(saved/'vel_com.f'),runs=runs,compiler=subprocess.check_output(['gfortran','--version'],text=True).splitlines()[0],scientific_equations_changed=False)
    p=ROOT/'data/eida_continuation/velest_build.json';p.write_text(json.dumps(record,indent=2)+'\n');print(record)
if __name__=='__main__':main()
