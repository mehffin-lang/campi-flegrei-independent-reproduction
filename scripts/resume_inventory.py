"""Freeze exact rebuild inputs and quantify retrieved coverage without filling gaps."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,collections
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
receipts={}
for name in ['observation_inputs.json','extended_sources.json','extended_responses.json','method_retrieval.json','velest_source.json','gnss_supplement_followup.json','gnss_recent_sources.json','baseline_model_inputs.json']+[p.name for p in (ROOT/'docs').glob('extended_windows_*.json')]+['extended_day_2024-01-01.json']:
    p=ROOT/'docs'/name
    if not p.exists():continue
    rows=json.loads(p.read_text());rows=rows if isinstance(rows,list) else [rows]
    for row in rows:
        if 'sha256' in row and (ROOT/row['file']).exists():receipts[row['file']]=row
# The offline rebuild requires raw waveforms, response metadata, model metadata,
# original leveling table, routine HTML, and generic VELEST source.
needed=set()
for p in (ROOT/'inputs/waveforms').glob('*.mseed'):needed.add(str(p.relative_to(ROOT)))
for p in (ROOT/'inputs/extended/waveforms').glob('*.mseed'):needed.add(str(p.relative_to(ROOT)))
for p in (ROOT/'inputs/extended/responses').glob('*.xml'):needed.add(str(p.relative_to(ROOT)))
for p in (ROOT/'inputs/extended').glob('routine_*.html'):needed.add(str(p.relative_to(ROOT)))
needed.update(['inputs/models/phasenet_retrained.pt','inputs/models/phasenet_retrained.json','inputs/models/stations.csv','inputs/metadata/channels.txt','inputs/metadata/response.xml','inputs/extended/background_3d_vmod','inputs/extended/delgaudio2010_table.doc','inputs/extended/velest.tar'])
needed.add('inputs/extended/demartino_supp.zip')
needed.add('inputs/extended/monthly_2023_12.pdf')
needed.update(['inputs/models/original.json.v1','inputs/models/original.pt.v1'])
rows=[]
for name in sorted(needed):
    row=receipts[name];p=ROOT/name
    assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],name
    rows.append({k:row[k] for k in ['file','url','bytes','sha256']})
(ROOT/'docs/rebuild_inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
source=[]
for item in json.loads((ROOT/'docs/file_inventory.json').read_text()):
    p=ROOT/item['file'];row=dict(item)
    assert p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
    if p.suffix=='.pdf':
        text=subprocess.check_output(['pdftotext','-layout',str(p),'-'],text=True)
        if p.name=='tanmodelsupp.pdf':assert all('Figure S'+str(i)+':' in text for i in range(1,16))
        row['readable']=True
    else:
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            row['members']=[dict(name=i.filename,bytes=i.file_size) for i in z.infolist()]
            row['executed']=False;row['readable']=True
    source.append(row)
(ROOT/'docs/resumed_source_check.json').write_text(json.dumps(source,indent=2)+'\n')
coverage=pd.concat([pd.read_csv(ROOT/'data/observations/coverage.csv'),pd.read_csv(ROOT/'data/extended/coverage.csv')],ignore_index=True)
out=[]
for chan,g in coverage.groupby('channel'):
    # pandas can use microseconds or nanoseconds internally; timestamp() is
    # explicitly seconds and avoids a factor-of-1000 coverage error.
    starts=pd.to_datetime(g.start,utc=True,format='ISO8601').map(lambda t:t.timestamp())
    ends=pd.to_datetime(g.end,utc=True,format='ISO8601').map(lambda t:t.timestamp())+1/g.sample_rate
    intervals=sorted(zip(starts,ends))
    merged=[]
    for a,b in intervals:
        if merged and a<=merged[-1][1]+.011:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    out.append(dict(channel=chan,first=g.start.min(),last=g.end.max(),retrieved_hours=sum(b-a for a,b in merged)/3600,disjoint_intervals=len(merged)))
    assert out[-1]['retrieved_hours']+1e-6 >= max(g.samples/g.sample_rate)/3600,chan
pd.DataFrame(out).to_csv(ROOT/'data/extended/coverage_summary.csv',index=False)
summary=dict(rebuild_input_files=len(rows),rebuild_input_bytes=sum(r['bytes'] for r in rows),waveform_files=coverage.file.nunique(),waveform_stations=sorted(coverage.channel.str.split('.').str[1].unique()),channel_hours=sum(r['retrieved_hours'] for r in out),coverage_note='Union of actual returned segments, not requested duration or metadata epochs; three components count separately.')
(ROOT/'data/extended/access_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
