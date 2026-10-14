"""Bounded resume of the existing calendar-based EIDA queue, without catalogs.

Complete the last three study days first (also useful for downstream waveform
review), then alternate years and months. This is incomplete calendar sampling,
not a completeness experiment. No attempted request is retried.
"""
import argparse,concurrent.futures,datetime,json,shutil
import collect_continuous as c

D=c.ROOT/'data/eida_continuation'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--max-jobs',type=int,default=256);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--core-start');ap.add_argument('--core-end');ap.add_argument('--purpose',default='Calendar-based full-period queue');a=ap.parse_args()
    db=c.connect();rows=[dict(r) for r in db.execute("SELECT * FROM jobs WHERE status='pending' AND attempts=0")]
    if a.core_start or a.core_end:
        assert a.core_start and a.core_end
        start=float(c.UTCDateTime(a.core_start));end=float(c.UTCDateTime(a.core_end));rows=[r for r in rows if r['start']==start and r['end']==end]
    def order(r):
        t=datetime.datetime.fromtimestamp(r['start'],datetime.timezone.utc)
        return (0 if r['start']>=c.END-3*86400 else 1,t.day,t.hour,t.month,t.year,r['station'])
    rows.sort(key=order);selected=rows[:a.max_jobs]
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
    receipt={'selection':__doc__,'purpose':a.purpose,'core_start':a.core_start,'core_end':a.core_end,'requested_limit':a.max_jobs,'requests':[]}
    target=D/('retrieval_batch_'+stamp+'.json')
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        active={};it=iter(selected);exhausted=False
        while active or not exhausted:
            while len(active)<a.workers and not exhausted:
                if shutil.disk_usage(c.ROOT).free<20*1024**3:
                    receipt['stop']='Shared filesystem has fewer than 20 GiB free';exhausted=True;break
                r=next(it,None)
                if r is None:exhausted=True;break
                assert db.execute('SELECT status,attempts FROM jobs WHERE id=?',(r['id'],)).fetchone()[:]==('pending',0)
                db.execute("UPDATE jobs SET status='running',attempts=attempts+1 WHERE id=?",(r['id'],));db.commit()
                active[pool.submit(c.fetch,r)]=r
            if not active:break
            done,_=concurrent.futures.wait(active,return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done:
                request=active.pop(f);r=f.result();keys=[k for k in r if k!='id']
                db.execute('UPDATE jobs SET '+','.join(k+'=?' for k in keys)+' WHERE id=?',[r[k] for k in keys]+[r['id']]);db.commit()
                receipt['requests'].append(dict(request={k:request[k] for k in ['id','network','station','channel','start','end']},outcome={k:v for k,v in r.items() if k!='segments'}))
                target.write_text(json.dumps(receipt,indent=2)+'\n')
                print(r['id'],r['status'],r['http'],r['bytes'],round(r['elapsed_s'],1),flush=True)
    db.close();receipt['summary']=c.summarize();target.write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':main()
