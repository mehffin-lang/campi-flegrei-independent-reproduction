"""Check 32-bit zero-term optimization against the preserved dense executable."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=ROOT/'tmp/eida_continuation/merged4/precision32_prelocation'
    work=ROOT/'tmp/eida_continuation/sparse32_check';work.mkdir(exist_ok=True)
    for name in ['input.mod','input.sta','input.cnv','velest.cmn']:shutil.copyfile(source/name,work/name)
    binary=ROOT/'tmp/eida_continuation/dense_build/velest32';binary.chmod(0o755);start=time.monotonic()
    r=subprocess.run([str(binary)],cwd=work,capture_output=True,text=True,timeout=300)
    (work/'console.log').write_text(r.stdout+r.stderr);r.check_returncode()
    equal={name:(source/name).read_bytes()==(work/name).read_bytes() for name in ['output.cnv','output.sta','residuals.txt']}
    equal['velocity_model']=(source/'velout.raw.mod').read_bytes()==(work/'velout.mod').read_bytes()
    receipt=dict(method=__doc__,events=552,phase_observations=9529,stage='Identical current regularized 14-iteration fixed-model prelocation',wall_seconds=time.monotonic()-start,dense_binary_sha256=sha(binary),sparse_binary_sha256=sha(ROOT/'build/velest32'),input_sha256={n:sha(work/n) for n in ['input.mod','input.sta','input.cnv','velest.cmn']},identical=equal,all_identical=all(equal.values()))
    (ROOT/'data/eida_continuation/sparse32_check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    assert receipt['all_identical'],'32-bit optimization changed numerical outputs'
if __name__=='__main__':main()
