"""Compile the pinned generic HypoDD 2.1 method; no example data are used."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,requests
ROOT=Path(__file__).resolve().parents[1]

def main():
    records=json.loads((ROOT/'data/calibration_followup/hypodd21_sources.json').read_text())
    build=ROOT/'build/hypodd21';build.mkdir(exist_ok=True)
    for r in records:
        source=ROOT/r['file']
        if not source.exists():
            response=requests.get(r['url'],timeout=60);response.raise_for_status()
            source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(response.content)
        assert hashlib.sha256(source.read_bytes()).hexdigest()==r['sha256'],r['file']
        relative=source.relative_to(ROOT/'inputs/external/hypodd21')
        dest=build/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    inc=build/'include/hypoDD.inc';text=inc.read_text()
    capacities=dict(MAXEVE=1024,MAXDATA=60000,MAXEVE0=175,MAXDATA0=30000,MAXLAY=50,MAXSTA=100,MAXCL=300)
    for key,value in capacities.items():text=re.sub(r'('+key+r'\s*=\s*)\d+',lambda m:m[1]+str(value),text)
    inc.write_text(text)
    matrix=build/'src/hypoDD/matmult2.f';source=matrix.read_text()
    assert 'real\tc(n)' in source
    # The routine calculates m output rows, and the caller supplies MAXDATA0
    # elements. Its upstream dummy-array declaration incorrectly says n.
    matrix.write_text(source.replace('real\tc(n)', 'real\tc(m)'))
    version=subprocess.check_output(['gfortran','-dumpversion'],text=True).strip()
    legacy=' -fallow-argument-mismatch' if int(version.split('.')[0])>=10 else ''
    command=['make','FC=gfortran','LDFLAGS=',
             'FFLAGS=-O2 -std=legacy'+legacy+' -fcheck=bounds -I../../include']
    run=subprocess.run(command,cwd=build/'src/hypoDD',capture_output=True,text=True)
    (ROOT/'tmp/calibration_followup/hypodd_build.log').write_text(run.stdout+run.stderr)
    record=dict(command=command,returncode=run.returncode,capacities=capacities,
                commit='fb40407fb768cbdc23a11e27bc841f5d4a98abb7',
                changes='Array capacities; correct matmult2 output dummy extent n to m (m matrix rows); no equation change; bounds checks enabled.')
    if run.returncode==0:record['binary_sha256']=hashlib.sha256((build/'src/hypoDD/hypoDD').read_bytes()).hexdigest()
    (ROOT/'data/calibration_followup/hypodd_build.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2));run.check_returncode()

if __name__=='__main__':main()
