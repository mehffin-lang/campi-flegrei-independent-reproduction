"""Versioned pre-2025 training coverage experiment; never opens holdout picks.

Only the six user-specified stations and two calendar-selected six-hour windows
are eligible for new retrieval. December 12 is the first complete calendar day
after all six stations have advertised simultaneous coverage; December 19 adds
a second day one week later. These dates do not use catalog/holdout outcomes.
"""
import argparse, json, hashlib, shutil, sqlite3, concurrent.futures, os
from pathlib import Path
import numpy as np, pandas as pd, requests
from obspy import UTCDateTime as U, read
import availability_extension as av

R=Path(__file__).resolve().parents[1]
VERSION=os.environ.get('VELOCITY_REVIEW_VERSION','training_extension_20261015')
assert '/' not in VERSION and VERSION not in ('.','..')
D=R/'data/velocity_holdout_review'/VERSION
I=R/'inputs/velocity_holdout_review'/VERSION
C=R/'data/availability_extension/catalog_december'
TARGET={'CGAU':('2I','HH'),'CLAC':('2I','HH'),'CREM':('2I','HH'),
        'CSOC':('2I','EH'),'CRUS':('IV','EH'),'CUMA':('IV','HH')}
END=float(U('2025-01-01'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2)+'\n')

def inventory():
    rows=pd.read_csv(R/'data/availability_extension/baseline_trace_intervals.csv').to_dict('records')
    con=sqlite3.connect(R/'inputs/availability_extension/requests.sqlite');con.row_factory=sqlite3.Row
    for r in con.execute("select receipt from requests where status='downloaded'"):
        q=json.loads(r['receipt']);rows.extend(dict(s,file=q['file']) for s in q['segments'])
    con.close()
    f=pd.DataFrame(rows);f=f[(f.start<END)&(f.end>float(U('2022-01-21')))].copy();f['end']=f.end.clip(upper=END)
    # Context spilling backward from 2025 is not training acquisition.
    jobs=json.loads((C/'input_jobs.json').read_text())
    eligible={j['file'] for j in jobs if j['start']<END}
    con=sqlite3.connect(R/'inputs/availability_extension/requests.sqlite')
    for rec, in con.execute("select receipt from requests where status='downloaded' and start<?",(END,)):
        eligible.add(json.loads(rec)['file'])
    con.close();f=f[f.file.isin(eligible)]
    f.to_csv(D/'pre2025_stored_intervals.csv',index=False)
    target=f[f.channel.str.split('.').str[1].isin(TARGET)]
    target.to_csv(D/'target_existing_intervals.csv',index=False)
    adv=pd.read_csv(R/'data/availability_extension/advertised_intervals.csv')
    adv=adv[adv.channel.str.split('.').str[1].isin(TARGET)&(adv.start<END)].copy();adv['end']=adv.end.clip(upper=END)
    adv.to_csv(D/'target_advertised_intervals_snapshot.csv',index=False)
    report=[]
    for sta,(net,band) in TARGET.items():
        for component in 'ENZ':
            ch=f'{net}.{sta}..{band}{component}';g=target[target.channel.eq(ch)];h=adv[adv.channel.eq(ch)]
            spans=av.union(zip(g.start,g.end));available=av.union(zip(h.start,h.end));missing=av.subtract(available,spans)
            report.append(dict(channel=ch,existing_files=g.file.nunique(),existing_channel_hours=sum(b-a for a,b in spans)/3600,
                first_advertised=str(U(min(h.start))) if len(h) else '',last_advertised=str(U(max(h.end))) if len(h) else '',
                missing_available_hours=sum(b-a for a,b in missing)/3600))
    pd.DataFrame(report).to_csv(D/'target_coverage_before.csv',index=False)
    budget=json.loads((R/'data/availability_extension/storage_budget.json').read_text());dump(D/'storage_budget.json',budget)
    # Estimate from actual target-station compressed files, not request counts.
    totals=[]
    for file,g in target.groupby('file'):
        path=R/file;totals.append(dict(file=file,bytes=path.stat().st_size,sha256=sha(path),channel_s=sum(b-a for ch,h in g.groupby('channel') for a,b in av.union(zip(h.start,h.end)))))
    pd.DataFrame(totals).to_csv(D/'existing_waveform_checksums.csv',index=False)
    rate=sum(r['bytes'] for r in totals)/sum(r['channel_s'] for r in totals)
    plan=[]
    for day in ['2024-12-12','2024-12-19']:
        a=float(U(day));b=a+21600
        for sta,(net,band) in TARGET.items():
            coverage=[]
            for comp in 'ENZ':
                ch=f'{net}.{sta}..{band}{comp}';g=f[f.channel.eq(ch)]
                coverage.append(sum(y-x for x,y in av.subtract([(a,b)],zip(g.start,g.end))))
            assert max(coverage)>0,'Already covered: no request allowed'
            ident=f'{net}_{sta}_{band}_{U(a).strftime("%Y%m%dT%H%M%S")}_{U(b).strftime("%Y%m%dT%H%M%S")}'
            plan.append(dict(id=ident,net=net,sta=sta,band=band,start=a,end=b,missing_channel_s=sum(coverage),estimated_bytes=rate*sum(coverage)))
    reserve=budget['reserve_bytes']+budget['processing_headroom_bytes'];free=shutil.disk_usage(R).free
    estimate=sum(j['estimated_bytes'] for j in plan)
    dump(D/'download_plan.json',dict(requests=plan,measured_bytes_per_channel_s=rate,estimated_bytes=estimate,
        free_bytes=free,protected_bytes=reserve,estimated_size_uncertainty='Compressed rate varies by station; allow twice the measured estimate before retrieval.',
        selection='First complete day after simultaneous advertised six-station deployment, then one week later; 00:00–06:00 UTC; no 2025 information.',
        authorization='Only targeted pre-2025 training gaps; broad queue stopped.'))
    assert free-2*estimate>reserve
    print(pd.DataFrame(report).to_string(index=False));print('Estimated bytes',round(estimate),'free',free,'reserve',reserve,flush=True)

def query():
    for job in json.loads((D/'download_plan.json').read_text())['requests']:
        receipt=D/'availability'/(job['id']+'.json');receipt.parent.mkdir(exist_ok=True)
        if receipt.exists():continue
        params=dict(net=job['net'],sta=job['sta'],cha=job['band']+'?',start=str(U(job['start'])),end=str(U(job['end'])),format='text',show='latestupdate')
        rec=dict(parameters=params,status='failed',utc=str(U()))
        try:
            r=requests.get(av.BASE+'availability/1/query',params=params,timeout=(20,45));rec.update(http=r.status_code,url=r.url)
            file=I/(job['id']+'_availability.txt');file.write_bytes(r.content);rec.update(file=str(file.relative_to(R)),sha256=sha(file))
            segments=[]
            if r.status_code==200:
                for line in r.text.splitlines():
                    if not line or line.startswith('#'):continue
                    t=line.split();fs=float(t[5]);a=max(job['start'],float(U(t[6])));b=min(job['end'],float(U(t[7]))+1/fs)
                    if b>a:segments.append(dict(channel=f'{t[0]}.{t[1]}.{"" if t[2]=="--" else t[2]}.{t[3]}',start=a,end=b,sample_rate=fs))
                rec['status']='available' if segments else 'empty'
            elif r.status_code==204:rec['status']='empty'
            else:rec['error']=r.text[:1000]
            rec['segments']=segments
        except Exception as e:rec['error']=repr(e)
        dump(receipt,rec);print(job['id'],rec['status'],rec.get('http'),flush=True)

def retrieve():
    av.D=D;av.I=I;av.B=END
    todo=[];(D/'receipts').mkdir(exist_ok=True)
    for j in json.loads((D/'download_plan.json').read_text())['requests']:
        p=D/'receipts'/(j['id']+'.json')
        if p.exists():
            r=json.loads(p.read_text())
            if r['status']=='downloaded':assert sha(R/r['file'])==r['sha256']
            continue # Do not repeat identical failed/empty requests.
        q=json.loads((D/'availability'/(j['id']+'.json')).read_text())
        if q['status']!='available':dump(p,dict(request=j['id'],status='not_downloaded',reason='Availability '+q['status'],bytes=0));continue
        todo.append(j)
    for k in range(0,len(todo),2):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for r in pool.map(av.fetch,todo[k:k+2]):
                dump(D/'receipts'/(r['request']+'.json'),r);print(r['request'],r['status'],r.get('http'),r['bytes'],r.get('error',''),flush=True)
        coverage()

def coverage():
    receipts=[json.loads(p.read_text()) for p in sorted((D/'receipts').glob('*.json'))]
    rows=pd.read_csv(D/'target_existing_intervals.csv').to_dict('records');jobs=[]
    plan={j['id']:j for j in json.loads((D/'download_plan.json').read_text())['requests']}
    for r in receipts:
        if r['status']!='downloaded':continue
        j=plan[r['request']];rows.extend(dict(s,file=r['file']) for s in r['segments'])
        jobs.append(dict(file=r['file'],start=j['start'],end=j['end'],sha256=r['sha256']))
    f=pd.DataFrame(rows);f.to_csv(D/'target_waveform_intervals.csv',index=False)
    union=[dict(channel=ch,start=a,end=b,hours=(b-a)/3600) for ch,g in f.groupby('channel') for a,b in av.union(zip(g.start,g.end))]
    pd.DataFrame(union).to_csv(D/'coverage_ledger.csv',index=False);dump(D/'new_input_jobs.json',jobs)
    pd.DataFrame([dict(request=r['request'],status=r['status'],http=r.get('http'),bytes=r.get('bytes'),file=r.get('file'),error=r.get('error',r.get('reason',''))) for r in receipts]).to_csv(D/'request_ledger.csv',index=False)
    dump(D/'coverage_summary.json',dict(downloaded_files=len(jobs),downloaded_bytes=sum(r.get('bytes',0) for r in receipts),
        union_target_channel_hours=sum(r['hours'] for r in union),free_bytes=shutil.disk_usage(R).free,
        statuses={s:sum(r['status']==s for r in receipts) for s in sorted({r['status'] for r in receipts})}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['inventory','query','retrieve','coverage']);a=ap.parse_args()
    D.mkdir(parents=True,exist_ok=True);I.mkdir(parents=True,exist_ok=True)
    globals()[a.stage]()
