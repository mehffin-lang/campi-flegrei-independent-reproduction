"""Preserve inspected public sources and the small caption-based waveform example."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for record in json.loads((ROOT/'docs/resumption_sources.json').read_text()):
    if record.get('http')!=200 or not record.get('file'):continue
    p=ROOT/record['file'];raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    rows.append(dict(file=record['file'],url=record.get('url',record.get('source')),bytes=record['bytes'],sha256=record['sha256']))
bundle=ROOT/'sources/resumption_inputs.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for r in rows:z.write(ROOT/r['file'],r['file'])
(ROOT/'docs/resumption_rebuild_inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
(ROOT/'docs/resumption_source_bundle.json').write_text(json.dumps(dict(file=str(bundle.relative_to(ROOT)),sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),members=rows,
    role='Original S4A waveform example; official source pages/format notes; authorized written methods and metadata listings. No author code or derived numerical results.'),indent=2)+'\n')
print('Frozen',len(rows),'small observational and written-source inputs')
