"""Process a frozen union of eligible old observations and verified new EIDA files."""
import hashlib,json,sqlite3,sys,fcntl,os
from pathlib import Path
import process_eida_followup as f
import reuse_own_associations as reuse

ROOT=f.ROOT;D=ROOT/os.environ.get('CF_AVAIL_CATALOG','data/availability_extension/catalog')
def main():
    D.mkdir(parents=True,exist_ok=True)
    jobs=[(r['file'],r['start'],r['end'],r['sha256']) for r in json.loads((ROOT/'data/eida_continuation/input_jobs.json').read_text())]
    c=sqlite3.connect(ROOT/'inputs/availability_extension/requests.sqlite');c.row_factory=sqlite3.Row
    for r in c.execute("SELECT * FROM requests WHERE status='downloaded' ORDER BY start,sta"):
        rec=json.loads(r['receipt']);p=ROOT/rec['file'];assert p.stat().st_size==rec['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256']
        jobs.append((rec['file'],r['start'],r['end'],rec['sha256']))
    c.close();assert len({j[0] for j in jobs})==len(jobs)
    # The imported entry point freezes jobs and verifies all hashes. Its own
    # event-selected exclusions and finite-score exposure rules remain active.
    f.p.jobs=lambda:jobs;f.D=D
    original=reuse.install
    reuse.install=lambda root,out,unused:original(root,out,ROOT/'data/eida_continuation')
    with (ROOT/'inputs/availability_extension/picking.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        f.main()
if __name__=='__main__':main()
