"""Resumable EIDA collection over the entire paper interval, without a catalog.

Availability is a retrieval guide, never counted as downloaded coverage.
Only miniSEED records read successfully enter the coverage ledger.
"""
from pathlib import Path
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import shutil
import sqlite3
import time

import requests
from obspy import read, UTCDateTime

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'inputs/continuation/acquisition.sqlite'
OUT = ROOT / 'data/continuation'
START = float(UTCDateTime('2022-01-21'))
END = float(UTCDateTime('2025-03-21'))


def connect():
    conn = sqlite3.connect(DB, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, network TEXT, station TEXT, channel TEXT,
        start REAL, end REAL, status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
        file TEXT, url TEXT, http INTEGER, bytes INTEGER, sha256 TEXT, error TEXT,
        retrieved_utc TEXT, elapsed_s REAL, segments TEXT, picked INTEGER DEFAULT 0)''')
    conn.commit()
    return conn


def plan():
    conn = connect()
    # A station's stated instrument band is metadata, not a detection result.
    preferred = {}
    for line in (ROOT / 'inputs/models/stations.csv').read_text().splitlines()[1:]:
        net, sta, loc, band = line.split(',')[0].split('.')
        preferred[(net, sta)] = band
    for file in sorted((ROOT / 'inputs/continuation/availability').glob('*.txt')):
        windows = set()
        for line in file.read_text().splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            net, sta, loc, channel, quality, fs, begin, end = line.split()[:8]
            band = preferred.get((net, sta), channel[:2])
            if channel[:2] != band:
                continue
            a, b = max(START, float(UTCDateTime(begin))), min(END, float(UTCDateTime(end))+1/float(fs))
            if b <= a:
                continue
            step = 6*3600
            first = START + int((a-START)//step)*step
            t = first
            while t < b:
                windows.add((net, sta, band+'?', t, min(t+step, END)))
                t += step
        for net, sta, band, begin, end in windows:
            ident = f'{net}_{sta}_{UTCDateTime(begin).strftime("%Y%m%dT%H%M%S")}_{UTCDateTime(end).strftime("%Y%m%dT%H%M%S")}'
            conn.execute('INSERT OR IGNORE INTO jobs(id,network,station,channel,start,end) VALUES(?,?,?,?,?,?)',
                         (ident, net, sta, band, begin, end))
        conn.commit()
    print('Planned', conn.execute('SELECT count(*) FROM jobs').fetchone()[0], 'resumable station/chunk requests.', flush=True)
    conn.close()
    summarize()


def fetch(job):
    job = dict(job)
    file = ROOT / 'inputs/continuation/waveforms' / (job['id']+'.mseed')
    file.parent.mkdir(exist_ok=True)
    part = file.with_suffix('.part')
    begin = time.monotonic()
    # Extra context supports the picker near file boundaries. The ledger records
    # actual sample spans and the processed core separately.
    params = dict(net=job['network'], sta=job['station'], loc='*', cha=job['channel'],
                  start=str(UTCDateTime(max(START,job['start']-30))),
                  end=str(UTCDateTime(min(END,job['end']+30))))
    row = dict(id=job['id'], status='failed', http=None, bytes=0, sha256=None,
               file=None, error=None, segments=None, url=None,
               retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    try:
        with requests.get('https://webservices.ingv.it/fdsnws/dataselect/1/query',
                          params=params, stream=True, timeout=(20,150)) as response:
            row.update(url=response.url, http=response.status_code)
            if response.status_code == 204:
                row['status'] = 'no_data'
            elif response.status_code != 200:
                row['error'] = response.text[:600]
            else:
                with part.open('wb') as stream:
                    for chunk in response.iter_content(1024*1024):
                        if time.monotonic()-begin > 240:
                            raise TimeoutError('240-second complete-transfer limit')
                        stream.write(chunk)
                traces = read(str(part), headonly=True)
                segments = []
                for tr in traces:
                    assert tr.stats.network == job['network'] and tr.stats.station == job['station']
                    assert tr.stats.channel.startswith(job['channel'][:2])
                    a, b = max(job['start'],float(tr.stats.starttime)), min(job['end'],float(tr.stats.endtime)+1/tr.stats.sampling_rate)
                    if b <= a:
                        continue
                    segments.append(dict(channel=tr.id, start=a, end=b, samples=tr.stats.npts,
                                         sample_rate=tr.stats.sampling_rate,
                                         raw_start=str(tr.stats.starttime), raw_end=str(tr.stats.endtime)))
                if not segments:
                    raise ValueError('Response has no records intersecting requested core')
                part.replace(file)
                row.update(status='downloaded', bytes=file.stat().st_size,
                           sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                           file=str(file.relative_to(ROOT)), segments=json.dumps(segments))
    except Exception as exc:
        row['error'] = repr(exc)
    finally:
        part.unlink(missing_ok=True)
    row['elapsed_s'] = time.monotonic()-begin
    return row


def run(args):
    conn = connect()
    conn.execute("UPDATE jobs SET status='pending' WHERE status='running'")
    conn.commit()
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        active = {}
        while True:
            # Reserve space for other workspace work. This is a local-capacity
            # stop, not a claim that any remote observation is unavailable.
            if shutil.disk_usage(ROOT).free < 20*1024**3:
                print('STOP: fewer than 20 GiB free on the shared filesystem.', flush=True)
                break
            while len(active) < args.workers and (args.max_jobs is None or completed+len(active) < args.max_jobs):
                job = conn.execute("SELECT * FROM jobs WHERE status='pending' AND attempts=0 ORDER BY (end-start), start, CASE WHEN station IN ('CAAM','COLB') THEN 0 ELSE 1 END,station LIMIT 1").fetchone()
                if job is None:
                    break
                conn.execute("UPDATE jobs SET status='running', attempts=attempts+1 WHERE id=?", (job['id'],))
                conn.commit()
                active[pool.submit(fetch, job)] = job['id']
            if not active:
                break
            done, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                active.pop(future)
                row = future.result()
                keys = [key for key in row if key != 'id']
                conn.execute('UPDATE jobs SET '+','.join(key+'=?' for key in keys)+' WHERE id=?',
                             [row[key] for key in keys]+[row['id']])
                conn.commit()
                completed += 1
                print(row['id'], row['status'], row['http'], row['bytes'], round(row['elapsed_s'],1), flush=True)
            summarize()
    conn.close()
    summarize()


def split_failed():
    """Split failed six-hour transfers into nonoverlapping half-hour cores.

    Keep the parent failure as evidence. Child success alone contributes actual
    sample coverage; request subdivision never implies continuous observations.
    """
    conn=connect();count=0
    rows=conn.execute("SELECT * FROM jobs WHERE status='failed' AND end-start>1800").fetchall()
    for r in rows:
        t=r['start']
        while t<r['end']:
            end=min(t+1800,r['end'])
            ident=f'{r["network"]}_{r["station"]}_{UTCDateTime(t).strftime("%Y%m%dT%H%M%S")}_{UTCDateTime(end).strftime("%Y%m%dT%H%M%S")}'
            count+=conn.execute('INSERT OR IGNORE INTO jobs(id,network,station,channel,start,end) VALUES(?,?,?,?,?,?)',(ident,r['network'],r['station'],r['channel'],t,end)).rowcount
            t=end
    conn.commit();conn.close();print('Added',count,'half-hour children of failed transfers.',flush=True)


def summarize():
    conn = connect()
    rows = [dict(row) for row in conn.execute("SELECT * FROM jobs WHERE status IN ('downloaded','failed','no_data') ORDER BY start,station")]
    intervals = {}
    for row in rows:
        for segment in json.loads(row['segments'] or '[]'):
            intervals.setdefault(segment['channel'], []).append((segment['start'],segment['end']))
    coverage=[]
    for channel, spans in intervals.items():
        merged=[]
        for start,end in sorted(spans):
            if merged and start <= merged[-1][1]+.001:
                merged[-1][1]=max(merged[-1][1],end)
            else:
                merged.append([start,end])
        coverage.append(dict(channel=channel, intervals=merged, hours=sum(b-a for a,b in merged)/3600))
    statuses=dict(conn.execute('SELECT status,count(*) FROM jobs GROUP BY status').fetchall())
    summary=dict(study_start=str(UTCDateTime(START)),study_end_exclusive=str(UTCDateTime(END)),
                 request_hours='6-hour full-period queue plus 0.5-hour calendar coverage checks',priority='short requests first, then chronological; no event catalog',
                 jobs_by_status=statuses,full_collection_complete=not any(statuses.get(k,0) for k in ['pending','running','failed']),
                 downloaded_bytes=sum(row['bytes'] for row in rows if row['status']=='downloaded'),
                 files=statuses.get('downloaded',0),channel_hours=sum(row['hours'] for row in coverage),
                 stations=sorted({channel.split('.')[1] for channel in intervals}),
                 accounting='Union of clipped, successfully read sample intervals. Availability metadata and failed requests do not count as coverage.')
    OUT.mkdir(exist_ok=True)
    (OUT/'acquisition_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'continuous_coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    # Exclude large per-record arrays from the portable retrieval ledger; retain
    # those in SQLite and the merged coverage record.
    portable=[{k:v for k,v in row.items() if k!='segments'} for row in rows]
    (ROOT/'docs/continuous_retrievals.json').write_text(json.dumps(portable,indent=2)+'\n')
    conn.close()
    return summary


def spread():
    """Probe all available study stations at calendar dates across the interval.

    This bounded diagnostic batch does not replace the full six-hour queue.
    It avoids spending every early acquisition batch on the last study days.
    """
    conn=connect();times=[START]
    for year in [2022,2023,2024,2025]:
        for month in [1,4,7,10]:
            t=float(UTCDateTime(f'{year}-{month:02d}-01'))
            if START<t<END:times.append(t)
    times.append(float(UTCDateTime('2025-03-01')))
    inserted=0
    for t in times:
        stations=conn.execute('SELECT DISTINCT network,station,channel FROM jobs WHERE start<=? AND end>=?',(t,t+1800)).fetchall()
        for net,sta,band in stations:
            ident=f'{net}_{sta}_{UTCDateTime(t).strftime("%Y%m%dT%H%M%S")}_{UTCDateTime(t+1800).strftime("%Y%m%dT%H%M%S")}'
            cursor=conn.execute('INSERT OR IGNORE INTO jobs(id,network,station,channel,start,end) VALUES(?,?,?,?,?,?)',(ident,net,sta,band,t,t+1800))
            inserted+=cursor.rowcount
    conn.commit();conn.close();print('Added',inserted,'half-hour calendar checks; full-period queue remains pending.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['plan','run','summary','spread','split-failed'])
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--max-jobs',type=int)
    args=parser.parse_args()
    if args.mode=='split-failed':split_failed()
    elif args.mode=='plan': plan()
    elif args.mode=='spread':spread()
    elif args.mode=='run': run(args)
    else: print(json.dumps(summarize(),indent=2))
