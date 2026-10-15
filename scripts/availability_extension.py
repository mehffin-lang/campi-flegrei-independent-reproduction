"""Availability-led, storage-bounded acquisition; observations only, no event list.

Detailed FDSN availability is a target, never evidence of downloaded coverage.
Requests cover six-hour station/band blocks with missing advertised samples.
Small gaps may be inside a block; actual trace union, not request duration, counts.
Earlier successful, empty and failed request receipts are retained unchanged.
"""
from pathlib import Path
import argparse, bisect, concurrent.futures as cf, datetime as dt, hashlib, json, shutil, sqlite3, time, fcntl, os
import numpy as np
import pandas as pd
import requests
from obspy import read, read_inventory, UTCDateTime as U

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/availability_extension';I=ROOT/'inputs/availability_extension'
A=float(U('2022-01-21'));B=float(U('2025-03-21'))
BASE='https://webservices.ingv.it/fdsnws/'
def dump(p,x):
    temp=p.with_name(p.name+f'.{os.getpid()}.tmp');temp.write_text(json.dumps(x,indent=2)+'\n');temp.replace(p)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def union(spans):
    out=[]
    for a,b in sorted(spans):
        if b<=a:continue
        if out and a<=out[-1][1]+1e-6:out[-1][1]=max(out[-1][1],b)
        else:out.append([a,b])
    return out
def subtract(spans,covered):
    out=[];covered=union(covered);ends=[y for _,y in covered]
    for a,b in union(spans):
        for j in range(bisect.bisect_right(ends,a),len(covered)):
            x,y=covered[j]
            if y<=a:continue
            if x>=b:break
            if x>a:out.append([a,min(x,b)])
            a=max(a,y)
            if a>=b:break
        if a<b:out.append([a,b])
    return out
def seconds(spans):return sum(b-a for a,b in union(spans))
def database():
    c=sqlite3.connect(I/'requests.sqlite',timeout=60);c.row_factory=sqlite3.Row
    c.execute('CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,net TEXT,sta TEXT,band TEXT,start REAL,end REAL,missing_s REAL,status TEXT,receipt TEXT)');c.commit();return c
def inventory():
    source=json.loads((ROOT/'data/eida_continuation/all_observation_inputs.json').read_text())
    rows=[];files=[]
    for r in source:
        p=ROOT/r['file'];h=sha(p);assert h==r['sha256'],p
        files.append(dict(file=r['file'],bytes=p.stat().st_size,sha256=h))
        for tr in read(str(p),headonly=True):
            a=max(A,float(tr.stats.starttime));b=min(B,float(tr.stats.endtime)+tr.stats.delta)
            if b>a:rows.append(dict(file=r['file'],channel=tr.id,start=a,end=b,sample_rate=tr.stats.sampling_rate))
    pd.DataFrame(rows).to_csv(D/'baseline_trace_intervals.csv',index=False)
    pd.DataFrame(files).to_csv(D/'baseline_files.csv',index=False)
    dup=pd.DataFrame(files);dup[dup.duplicated('sha256',keep=False)].to_csv(D/'duplicate_content_files.csv',index=False)
    q=pd.read_csv(ROOT/'data/continuation/station_geometry_qa.csv')
    epochs=[]
    for f in sorted((ROOT/'inputs/continuation').glob('*_responses.xml')):
        digest=sha(f)
        for net in read_inventory(str(f)):
            for sta in net:
                for ch in sta:
                    if ch.code[:2] not in ['HH','EH']:continue
                    epochs.append(dict(network=net.code,station=sta.code,location=ch.location_code,channel=ch.code,start=str(ch.start_date),end=str(ch.end_date),latitude=ch.latitude,longitude=ch.longitude,elevation_m=ch.elevation,sample_rate=ch.sample_rate,response=ch.response is not None,source=str(f.relative_to(ROOT)),source_sha256=digest))
    pd.DataFrame(epochs).drop_duplicates().to_csv(D/'response_epochs.csv',index=False)
    q['scope']=np.where(q.network.isin(['IV','2I'])&q.band.isin(['HH','EH']),'seismometer candidate','deferred accelerometer')
    q['membership_note']='Released station metadata candidate; 51 identifiers do not establish membership of the written 48 instruments.'
    q.to_csv(D/'station_crosswalk.csv',index=False)
    dump(D/'source_specification.json',dict(period=['2022-01-21T00:00:00Z','2025-03-21T00:00:00Z'],end_convention='exclusive; includes March 20',paper='tanmodel.pdf',supplement='tanmodelsupp.pdf',paper_sha256=sha(ROOT/'tanmodel.pdf'),supplement_sha256=sha(ROOT/'tanmodelsupp.pdf'),written_counts=dict(broadband=23,short_period=9,accelerometer=16),candidate_source='inputs/models/stations.csv',candidate_sha256=sha(ROOT/'inputs/models/stations.csv'),classes={'waveforms':'original observations','StationXML':'public metadata','released station list':'permitted metadata; membership uncertainty retained'},baseline_files=len(files),baseline_bytes=sum(r['bytes'] for r in files),raw_s=sum(r['end']-r['start'] for r in rows),union_s=sum(seconds(zip(g.start,g.end)) for _,g in pd.DataFrame(rows).groupby('channel'))))
def availability():
    q=pd.read_csv(D/'station_crosswalk.csv');q=q[q.scope=='seismometer candidate']
    def get(r):
        stem=f'{r.network}_{r.station}_{r.band}';p=I/(stem+'.txt');receipt=D/(stem+'_availability.json')
        if receipt.exists():return json.loads(receipt.read_text())
        params=dict(net=r.network,sta=r.station,cha=r.band+'?',start=str(U(A)),end=str(U(B)),format='text',show='latestupdate')
        result=dict(parameters=params,utc=dt.datetime.now(dt.timezone.utc).isoformat(),file=str(p.relative_to(ROOT)))
        try:
            z=requests.get(BASE+'availability/1/query',params=params,timeout=(20,100));p.write_bytes(z.content)
            result.update(url=z.url,http=z.status_code,bytes=len(z.content),sha256=sha(p))
        except Exception as e:result.update(error=repr(e))
        dump(receipt,result);print(stem,result.get('http',result.get('error')),flush=True);return result
    with cf.ThreadPoolExecutor(max_workers=2) as pool:res=list(pool.map(get,q.itertuples()))
    dump(D/'availability_receipts.json',res)
    rows=[]
    for r in res:
        if r.get('http')!=200:continue
        for line in (ROOT/r['file']).read_text().splitlines():
            if not line or line.startswith('#'):continue
            t=line.split();net,sta,loc,ch=t[:4];fs=float(t[5]);a=max(A,float(U(t[6])));b=min(B,float(U(t[7]))+1/fs)
            if b>a:rows.append(dict(channel=f'{net}.{sta}.{"" if loc=="--" else loc}.{ch}',start=a,end=b,sample_rate=fs,source=r['file']))
    pd.DataFrame(rows).to_csv(D/'advertised_intervals.csv',index=False)
def plan():
    a=pd.read_csv(D/'advertised_intervals.csv');old=pd.read_csv(D/'baseline_trace_intervals.csv')
    covered={ch:union(zip(g.start,g.end)) for ch,g in old.groupby('channel')}
    conn=database();legacy=sqlite3.connect(ROOT/'inputs/continuation/acquisition.sqlite');legacy.row_factory=sqlite3.Row
    attempted={(r['network'],r['station'],r['start'],r['end']):dict(r) for r in legacy.execute("SELECT * FROM jobs WHERE status IN ('failed','no_data','downloaded')")};legacy.close()
    tasks={};missing=[]
    for ch,g in a.groupby('channel'):
        for x,y in subtract(zip(g.start,g.end),covered.get(ch,[])):
            missing.append(dict(channel=ch,start=x,end=y))
            net,sta,loc,band=ch.split('.');t=A+np.floor((x-A)/21600)*21600
            while t<y:
                end=min(B,t+21600);key=(net,sta,band[:2],float(t),float(end))
                tasks[key]=tasks.get(key,0)+max(0,min(y,end)-max(x,t));t=end
    for (net,sta,band,x,y),s in tasks.items():
        ident=f'{net}_{sta}_{band}_{U(x).strftime("%Y%m%dT%H%M%S")}_{U(y).strftime("%Y%m%dT%H%M%S")}'
        status='pending';receipt=None
        if (net,sta,x,y) in attempted:
            r=attempted[net,sta,x,y]
            if r['status']=='downloaded':
                if r['file'] in set(old.file):
                    status='prior_success_unverified_gaps';receipt=json.dumps(dict(legacy_request_id=r['id'],file=r['file'],sha256=r['sha256'],reason='Exact whole-window request already succeeded; remaining advertised internal gaps are unverified, not new files.'))
            else:
                status='prior_'+r['status'];receipt=json.dumps(dict(legacy_request_id=r['id'],error=r['error'],http=r['http']))
        conn.execute('INSERT OR IGNORE INTO requests VALUES(?,?,?,?,?,?,?,?,?)',(ident,net,sta,band,x,y,s,status,receipt))
    conn.commit();conn.close();pd.DataFrame(missing).to_csv(D/'initial_missing_available_intervals.csv',index=False)
    # Classify all legacy requests by actual advertised and stored intersections.
    legacy=sqlite3.connect(ROOT/'inputs/continuation/acquisition.sqlite');legacy.row_factory=sqlite3.Row;classify=[]
    av={};cv={}
    for ch,g in a.groupby('channel'):av.setdefault('.'.join(ch.split('.')[:2])+'.'+ch.split('.')[-1][:2],[]).extend(zip(g.start,g.end))
    for ch,g in old.groupby('channel'):cv.setdefault('.'.join(ch.split('.')[:2])+'.'+ch.split('.')[-1][:2],[]).extend(zip(g.start,g.end))
    av={k:union(v) for k,v in av.items()};cv={k:union(v) for k,v in cv.items()}
    def indexed(d):
        return {k:(np.array(v),np.array([b for _,b in v])) for k,v in d.items()}
    av=indexed(av);cv=indexed(cv)
    for r in legacy.execute('SELECT id,network,station,channel,start,end,status FROM jobs'):
        key=f'{r["network"]}.{r["station"]}.{r["channel"][:2]}';x=max(A,r['start']);y=min(B,r['end'])
        def overlap(d):
            if key not in d:return 0.
            spans,ends=d[key];j=int(np.searchsorted(ends,x,side='right'));k=int(np.searchsorted(spans[:,0],y,side='left'))
            return float(np.maximum(0,np.minimum(y,spans[j:k,1])-np.maximum(x,spans[j:k,0])).sum())
        avail=overlap(av);local=overlap(cv)
        cls='outside scope' if y<=x else 'no advertised availability' if not avail else 'covered at station-band union (channel gaps checked separately)' if local>=y-x-.02 else 'available missing or partial'
        classify.append(dict(r,classification=cls,advertised_station_s=avail,stored_station_s=local))
    pd.DataFrame(classify).to_csv(D/'legacy_ledger_classification.csv.gz',index=False);legacy.close();summarize()
def fetch(job):
    p=I/'waveforms'/(job['id']+'.mseed');p.parent.mkdir(exist_ok=True);part=p.with_suffix('.part')
    budget=json.loads((D/'storage_budget.json').read_text());reserve=budget['reserve_bytes']+budget.get('processing_headroom_bytes',0);started=time.monotonic()
    params=dict(net=job['net'],sta=job['sta'],loc='*',cha=job['band']+'?',start=str(U(max(A,job['start']-30))),end=str(U(min(B,job['end']+30))))
    rec=dict(request=job['id'],parameters=params,utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='failed',bytes=0)
    try:
        with requests.get(BASE+'dataselect/1/query',params=params,stream=True,timeout=(20,90)) as r:
            rec.update(http=r.status_code,url=r.url)
            if r.status_code==204:rec['status']='empty'
            elif r.status_code!=200:rec['error']=r.text[:1500]
            else:
                with part.open('wb') as f:
                    for block in r.iter_content(1048576):
                        if shutil.disk_usage(ROOT).free-len(block)<reserve+8*1048576:raise OSError('storage reserve reached during stream')
                        if time.monotonic()-started>240:raise TimeoutError('240 s transfer limit')
                        f.write(block)
                st=read(str(part),headonly=True);segments=[]
                for tr in st:
                    assert tr.stats.network==job['net'] and tr.stats.station==job['sta'] and tr.stats.channel[:2]==job['band']
                    x=max(A,float(tr.stats.starttime));y=min(B,float(tr.stats.endtime)+tr.stats.delta)
                    if y>x:segments.append(dict(channel=tr.id,start=x,end=y,sample_rate=tr.stats.sampling_rate))
                if not segments:raise ValueError('No in-scope trace samples')
                part.replace(p);rec.update(status='downloaded',file=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p),segments=segments)
    except Exception as e:rec['error']=repr(e)
    finally:part.unlink(missing_ok=True)
    rec['elapsed_s']=time.monotonic()-started;return rec
def summarize():
    conn=database();jobs=[dict(r) for r in conn.execute('SELECT * FROM requests')];conn.close()
    rows=pd.read_csv(D/'baseline_trace_intervals.csv').to_dict('records');new=[]
    for r in jobs:
        x=json.loads(r['receipt']) if r['receipt'] else {}
        if r['status']=='downloaded':
            new.append(x)
            rows.extend(dict(s,file=x['file']) for s in x['segments'])
    f=pd.DataFrame(rows);cov=[];available=pd.read_csv(D/'advertised_intervals.csv');av={ch:union(zip(g.start,g.end)) for ch,g in available.groupby('channel')};seen={}
    for ch,g in f.groupby('channel'):
        spans=union(zip(g.start,g.end));seen[ch]=spans
        cov.extend(dict(channel=ch,start=x,end=y) for x,y in spans)
    pd.DataFrame(cov).to_csv(D/'coverage_intervals.csv',index=False)
    missing=[dict(channel=ch,start=x,end=y) for ch,spans in av.items() for x,y in subtract(spans,seen.get(ch,[]))]
    pd.DataFrame(missing,columns=['channel','start','end']).to_csv(D/'remaining_available_intervals.csv',index=False)
    monthly={}
    for r in cov:
        x=r['start'];end=r['end']
        while x<end:
            d=U(x);n=U(d.year+int(d.month==12),d.month%12+1,1);y=min(end,float(n));key=(r['channel'],d.strftime('%Y-%m'));monthly[key]=monthly.get(key,0)+(y-x)/3600;x=y
    pd.DataFrame([dict(channel=ch,month=m,hours=h) for (ch,m),h in sorted(monthly.items())]).to_csv(D/'station_channel_month.csv',index=False)
    slim=[{k:v for k,v in r.items() if k!='receipt'} for r in jobs];pd.DataFrame(slim).to_csv(D/'request_ledger.csv.gz',index=False)
    dump(D/'download_receipts.json',new)
    states={s:sum(r['status']==s for r in jobs) for s in sorted(set(r['status'] for r in jobs))}
    base=json.loads((D/'source_specification.json').read_text());new_union=sum(r['end']-r['start'] for r in cov)-base['union_s'];nb=sum(x['bytes'] for x in new)
    rate=nb/new_union if new_union>0 else None
    summary=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),states=states,downloaded_bytes=nb,new_union_channel_hours=new_union/3600,union_channel_hours=sum(r['end']-r['start'] for r in cov)/3600,remaining_available_channel_hours=sum(r['end']-r['start'] for r in missing)/3600,measured_bytes_per_new_channel_second=rate,estimated_remaining_bytes=rate*sum(r['end']-r['start'] for r in missing) if rate else None,free_bytes=shutil.disk_usage(ROOT).free,estimate_note='Measured compressed bytes per incremental channel second; includes transfer context and overlaps; station/epoch variability is not a confidence interval.',scope='Original continuous EIDA observations; availability gaps and unavailable station epochs remain excluded.')
    dump(D/'coverage_summary.json',summary);return summary
def retrieve(sample=False):
    conn=database()
    verification=[]
    for r in conn.execute("SELECT * FROM requests WHERE status='downloaded'"):
        rec=json.loads(r['receipt']);p=ROOT/rec['file'];valid=p.exists() and p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256']
        verification.append(dict(file=rec['file'],valid=valid,sha256=rec['sha256']))
        if not valid:raise RuntimeError('Previously downloaded file failed verification: '+rec['file'])
    dump(D/'resume_verification.json',verification)
    rows=[dict(r) for r in conn.execute("SELECT * FROM requests WHERE status='pending'")]
    # Round-robin calendar months retain multiyear scope if storage fills.
    # No earthquake times, published counts or prior detections enter priority.
    priority_a=float(U('2024-12-01'));priority_b=priority_a+21600
    rows.sort(key=lambda r:(not(priority_a<=r['start']<priority_b),U(r['start']).day,U(r['start']).hour,U(r['start']).year,U(r['start']).month,r['net'],r['sta']))
    if sample:
        chosen=[];seen=set()
        for r in sorted(rows,key=lambda r:(U(r['start']).year,r['sta'],r['start'])):
            key=(U(r['start']).year,r['band'])
            if key not in seen:chosen.append(r);seen.add(key)
        rows=chosen
    budget=json.loads((D/'storage_budget.json').read_text());reserve=budget['reserve_bytes']+budget.get('processing_headroom_bytes',0);reason='eligible request queue exhausted';consecutive=0
    for k in range(0,len(rows),4):
        if shutil.disk_usage(ROOT).free<reserve+128*1048576:reason='storage reserve reached';break
        batch=[r for r in rows[k:k+4] if conn.execute('SELECT status FROM requests WHERE id=?',(r['id'],)).fetchone()[0]=='pending']
        with cf.ThreadPoolExecutor(max_workers=2) as pool:
            for rec in pool.map(fetch,batch):
                conn.execute('UPDATE requests SET status=?,receipt=? WHERE id=?',(rec['status'],json.dumps(rec),rec['request']));conn.commit()
                (D/'receipts').mkdir(exist_ok=True);dump(D/'receipts'/(rec['request']+'.json'),rec)
                print(rec['request'],rec['status'],rec.get('http'),rec['bytes'],rec.get('error','')[:120],flush=True)
                consecutive=consecutive+1 if rec['status']=='failed' else 0
        summary=summarize()
        print(json.dumps(summary),flush=True)
        if consecutive>=8:reason='service safeguard: eight consecutive transfer failures across batches; receipts retained';break
    conn.close();summary=summarize();dump(D/('sample_result.json' if sample else 'retrieval_result.json'),dict(stop_reason='representative sample complete' if sample else reason,**summary))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['inventory','availability','plan','sample','retrieve','summary']);a=p.parse_args()
    D.mkdir(exist_ok=True);I.mkdir(exist_ok=True)
    with (I/'collector.lock').open('a') as lock:
        if a.stage in ['sample','retrieve']:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        {'inventory':inventory,'availability':availability,'plan':plan,'sample':lambda:retrieve(True),'retrieve':retrieve,'summary':summarize}[a.stage]()
