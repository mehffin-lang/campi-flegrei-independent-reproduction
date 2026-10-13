"""Prepare generic FK/gCAP resources; never extract archive example results."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
import requests
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_followup'
def main():
    manifest=json.loads((D/'method_resources.json').read_text())
    for row in manifest:
        file=ROOT/row['archive'];file.parent.mkdir(parents=True,exist_ok=True)
        if not file.exists():
            response=requests.get(row['url'],timeout=60);response.raise_for_status();assert hashlib.sha256(response.content).hexdigest()==row['sha256'];file.write_bytes(response.content)
        assert hashlib.sha256(file.read_bytes()).hexdigest()==row['sha256']
        with tarfile.open(file) as tf:
            assert tf.getnames()==row['archive_members'],'Archive contents changed'
            for member in row['extracted_method_files']:
                path=ROOT/'build/method_followup'/member;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(tf.extractfile(member).read())
    cmd=['make','-C','build/method_followup/fk','-j2','fk','trav','sachd','FC=gfortran','F77=gfortran','FFLAGS=-O2 -std=legacy -ffixed-line-length-none']
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);(D/'fk_build.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr)
    subprocess.run([str(ROOT/'.venv/bin/python'),'scripts/build_gcap_followup.py'],cwd=ROOT,check=True)
if __name__=='__main__':main()
