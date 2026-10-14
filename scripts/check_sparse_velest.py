"""Compare sparse arithmetic with six saved dense runs on observed events."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    records=[]
    for stage in ['prelocation','round1','round2','convergence1','convergence2','convergence3']:
        source=ROOT/'tmp/eida_continuation/merged4'/('Pozzuoli_Solfatara_'+stage)
        work=ROOT/'tmp/eida_continuation/sparse_check'/stage;work.mkdir(parents=True,exist_ok=True)
        for name in ['input.mod','input.sta','input.cnv','velest.cmn']:shutil.copyfile(source/name,work/name)
        start=time.monotonic();r=subprocess.run([str(ROOT/'build/velest64_sparse')],cwd=work,capture_output=True,text=True,timeout=300)
        (work/'console.log').write_text(r.stdout+r.stderr);r.check_returncode()
        checks={name:(source/name).read_bytes()==(work/name).read_bytes() for name in ['output.cnv','output.sta','residuals.txt']}
        checks['velocity_model']=(source/'velout.raw.mod').read_bytes()==(work/'velout.mod').read_bytes()
        records.append(dict(stage=stage,wall_seconds=time.monotonic()-start,identical=checks,input_sha256={n:sha(work/n) for n in ['input.mod','input.sta','input.cnv','velest.cmn']}))
        print(stage,records[-1]['wall_seconds'],checks,flush=True)
    receipt=dict(method=__doc__,events=552,phase_observations=9529,all_identical=all(all(r['identical'].values()) for r in records),runs=records)
    (ROOT/'data/eida_continuation/sparse_check.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert receipt['all_identical'],'Sparse optimization rejected: outputs differ'
if __name__=='__main__':main()
