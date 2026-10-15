"""Drain newly verified continuous observations while collection proceeds.

No event snippets or author results enter. A file is reusable only when waveform,
model, implementation, preprocessing and core-interval identities all agree.
"""
import concurrent.futures as cf,fcntl,hashlib,json,multiprocessing,os,sqlite3,time
from pathlib import Path
import process_continuous as p
ROOT=p.ROOT;D=ROOT/'data/availability_extension';I=ROOT/'inputs/availability_extension'
def main():
    identity=p.inference_identity();log=D/'incremental_picking.jsonl';state=D/'incremental_picking_status.json'
    with cf.ProcessPoolExecutor(max_workers=2,initializer=p.initialize_worker,mp_context=multiprocessing.get_context('spawn')) as pool:
        while not (I/'stop_incremental_picking').exists():
            with (I/'picking.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                conn=sqlite3.connect(I/'requests.sqlite');conn.row_factory=sqlite3.Row
                rows=list(conn.execute("SELECT * FROM requests WHERE status='downloaded' ORDER BY start,sta"));conn.close();pending=[];verified=0
                failed=set()
                if log.exists():failed={r['file'] for line in log.read_text().splitlines() if (r:=json.loads(line))['status']=='failed'}
                for row in rows:
                    r=json.loads(row['receipt']);source=r['file'];cache=p.CACHE/(hashlib.sha256(source.encode()).hexdigest()[:20]+'.json')
                    if cache.exists():
                        old=json.loads(cache.read_text())
                        if old.get('input_sha256')==r['sha256'] and old.get('settings')==p.SETTINGS and old.get('inference_identity')==identity and old.get('core_start')==row['start'] and old.get('core_end')==row['end']:verified+=1;continue
                    if source in failed:continue
                    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==r['sha256'],source
                    pending.append((source,row['start'],row['end'],r['sha256']))
                # Yield the shared lock between small batches so an association
                # checkpoint can freeze a coherent set of completed picks.
                batch=pending[:8]
                for r in pool.map(p.pick,batch):
                    with log.open('a') as out:out.write(json.dumps(r)+'\n')
                    print(json.dumps(r),flush=True)
                state.write_text(json.dumps(dict(pid=os.getpid(),verified_cached_files=verified,batch_files=len(batch),downloaded_files=len(rows),pending_before_batch=len(pending),failed_files=sorted(failed),running=True),indent=2)+'\n')
            if not batch:time.sleep(15)
    state.write_text(json.dumps(dict(pid=os.getpid(),running=False,reason='explicit stop sentinel'),indent=2)+'\n')
if __name__=='__main__':main()
