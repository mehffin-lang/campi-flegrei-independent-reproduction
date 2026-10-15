"""Check whole-file duplicates and trace-interval overlap for a frozen cohort."""
import json
from pathlib import Path
import pandas as pd
from availability_extension import union
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/availability_extension'
def main():
    current=json.loads((D/'current_analysis.json').read_text());C=ROOT/current['catalog']
    files=pd.DataFrame(json.loads((C/'all_observation_inputs.json').read_text()));allowed=set(files.file)
    files[files.duplicated('sha256',keep=False)].to_csv(C/'duplicate_file_hashes.csv',index=False)
    rows=pd.read_csv(D/'baseline_trace_intervals.csv').to_dict('records')
    for p in sorted((D/'receipts').glob('*.json')):
        r=json.loads(p.read_text())
        if r.get('status')=='downloaded' and r['file'] in allowed:rows.extend(dict(s,file=r['file']) for s in r['segments'])
    frame=pd.DataFrame(rows);frame=frame[frame.file.isin(allowed)].copy()
    duplicates=frame[frame.duplicated(['channel','start','end','sample_rate'],keep=False)]
    duplicates.to_csv(C/'identical_trace_intervals.csv',index=False)
    raw=float((frame.end-frame.start).sum());unique=sum(sum(y-x for x,y in union(zip(g.start,g.end))) for _,g in frame.groupby('channel'))
    result=dict(files=len(files),whole_file_duplicate_rows=int(files.duplicated('sha256',keep=False).sum()),trace_rows=len(frame),identical_trace_interval_rows=len(duplicates),raw_channel_hours=raw/3600,union_channel_hours=unique/3600,overlapping_channel_hours=(raw-unique)/3600,interpretation='Hashes identify repeated complete files; channel/time/sample-rate keys identify repeated trace segments. All interval overlaps count once. Context overlaps are expected. This does not certify equality of every overlapping waveform sample or equate raw trace time with finite inference-score exposure.',inputs=[str((C/'all_observation_inputs.json').relative_to(ROOT)),'data/availability_extension/baseline_trace_intervals.csv','data/availability_extension/receipts/'])
    (C/'overlap_check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
