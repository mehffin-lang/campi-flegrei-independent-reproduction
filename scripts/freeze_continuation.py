"""Freeze an auditable input checkpoint; no requested interval becomes coverage."""
from pathlib import Path
import datetime,gzip,hashlib,json,sqlite3,zipfile
import process_continuous as workflow
from collect_continuous import summarize
ROOT=Path(__file__).resolve().parents[1]
receipts={}
for name in ['continuation_inputs','gnss2025_inputs','continuation_retrievals','continuation_availability','continuation_responses','chunk_probe','continuous_retrievals']:
    for r in json.loads((ROOT/'docs'/f'{name}.json').read_text()):
        if r.get('file') and (ROOT/r['file']).exists() and r.get('http',200)==200:receipts[r['file']]=r
for file,url in [('inputs/continuation/tramelli2021.html','https://pmc.ncbi.nlm.nih.gov/articles/PMC8009907/'),('inputs/continuation/coastline.zip','https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_coastline.zip'),('inputs/continuation/gnss2025_record.json','https://zenodo.org/api/records/22259337')]:
    receipts[file]=dict(file=file,url=url)
rows=[]
for file,r in sorted(receipts.items()):
    p=ROOT/file
    rows.append(dict(file=file,url=r['url'],bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),retrieved_utc=r.get('retrieved_utc','2026-10-12')))
(ROOT/'docs/continuation_rebuild_inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
jobs=[dict(file=f,start=a,end=b,sha256=h) for f,a,b,h in workflow.jobs()]
(ROOT/'docs/continuation_processed_inputs.json').write_text(json.dumps(jobs,indent=2)+'\n')
summary=summarize();summary['checkpoint_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(ROOT/'data/continuation/acquisition_checkpoint.json').write_text(json.dumps(summary,indent=2)+'\n')
database=sqlite3.connect(ROOT/'inputs/continuation/acquisition.sqlite')
snapshot=ROOT/'tmp/continuation/acquisition_checkpoint.sqlite'
target=sqlite3.connect(snapshot);database.backup(target);target.execute('PRAGMA journal_mode=DELETE');target.close();database.close()
bundle_db=ROOT/'sources/acquisition_checkpoint.sqlite.gz'
bundle_db.write_bytes(gzip.compress(snapshot.read_bytes(),mtime=0))
(ROOT/'docs/acquisition_database_snapshot.json').write_text(json.dumps(dict(file=str(bundle_db.relative_to(ROOT)),bytes=bundle_db.stat().st_size,sha256=hashlib.sha256(bundle_db.read_bytes()).hexdigest(),
    role='Frozen request/response administrative ledger, including pending jobs; not evidence that pending intervals were observed.'),indent=2)+'\n')
# Preserve the small textual/context inputs as a compressed source snapshot.
# Live routine pages change, so a future download may not reproduce their hash.
# Large continuous waveform observations remain outside Git, with exact URLs.
bundle=ROOT/'sources/continuation_context_inputs.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for r in rows:
        if not r['file'].endswith('.mseed'):z.write(ROOT/r['file'],r['file'])
(ROOT/'docs/continuation_source_bundle.json').write_text(json.dumps(dict(file=str(bundle.relative_to(ROOT)),bytes=bundle.stat().st_size,sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),contents='Original routine-catalog snapshot, GNSS observations/format notes, station/availability metadata, written alternative-model source, and Natural Earth coastlines. No Tan-derived result files or code.',members=[r['file'] for r in rows if not r['file'].endswith('.mseed')]),indent=2)+'\n')
print('Frozen',len(jobs),'continuous files and',len(rows),'input receipts; context bundle bytes',bundle.stat().st_size)
