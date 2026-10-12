"""Final comparison only: never imported by observation processing or inversion."""
from pathlib import Path
import json,hashlib,zipfile,argparse
import pandas as pd
import numpy as np
from pyproj import Geod
ROOT=Path(__file__).resolve().parents[1]

def compare(dataset='extended'):
    ownfile=ROOT/('data/continuation/velest_filtered.csv' if dataset=='continuation' else 'data/extended/initial_events.csv')
    if dataset=='continuation' and not json.loads((ROOT/'data/continuation/velest_summary.json').read_text()).get('completed'):
        summary=dict(status='Not run: no successful current VELEST pilot for final comparison')
        out=ROOT/'data/comparison_continuation';out.mkdir(exist_ok=True)
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (ROOT/'report/continuation_final_comparison.tex').write_text('The current VELEST pilot did not complete; no comparison is reported.\n')
        return summary
    digest=hashlib.sha256(ownfile.read_bytes()).hexdigest()
    own=pd.read_csv(ownfile)
    archive=ROOT/'science.adw9038_data_s1_to_s3.zip'
    with zipfile.ZipFile(archive) as z:
        with z.open('science.adw9038_data_s1.csv') as f:
            ref=pd.read_csv(f,usecols=['event_index','TIME','LAT','LON'])
    epoch=pd.to_datetime(ref.TIME,utc=True,format='ISO8601').map(lambda t:t.timestamp()).to_numpy()
    geod=Geod(ellps='WGS84');rows=[]
    for r in own.to_dict('records'):
        t=pd.Timestamp(r['time']).timestamp();near=np.flatnonzero(abs(epoch-t)<=2)
        row=dict(own_event_index=r['event_index'],reference_candidates=len(near),matched=False,
            reference_event_index=None,time_difference_s=None,horizontal_difference_km=None)
        if len(near)==1:
            q=ref.iloc[near[0]]
            distance=geod.inv(r['longitude'],r['latitude'],q.LON,q.LAT)[2]/1000
            row.update(matched=True,reference_event_index=int(q.event_index),time_difference_s=t-epoch[near[0]],horizontal_difference_km=float(distance))
        rows.append(row)
    frame=pd.DataFrame(rows)
    dup=frame.loc[frame.matched,'reference_event_index'].duplicated(keep=False)
    frame.loc[dup[dup].index,'matched']=False
    out=ROOT/('data/comparison_continuation' if dataset=='continuation' else 'data/comparison');out.mkdir(exist_ok=True)
    frame.to_csv(out/'tan_s1_final_comparison.csv',index=False)
    selected=frame[frame.matched]
    summary=dict(role='FINAL COMPARISON ONLY; not an input, target, filter or calibration for the independent workflow',
        reference_file=archive.name,reference_member='science.adw9038_data_s1.csv',reference_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        reference_rows=len(ref),independent_events=len(own),time_window_s=2.,unique_matches=len(selected),
        median_absolute_time_difference_s=float(selected.time_difference_s.abs().median()) if len(selected) else None,
        median_horizontal_difference_km=float(selected.horizontal_difference_km.median()) if len(selected) else None,
        maximum_horizontal_difference_km=float(selected.horizontal_difference_km.max()) if len(selected) else None,
        independent_input_sha256=digest,limitations='Temporal coincidence is not identity proof. Unmatched events are not declared false detections. No author location changes a provisional location or panel.')
    assert hashlib.sha256(ownfile.read_bytes()).hexdigest()==digest
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    text=(f"A strictly downstream comparison against supplied Data S1 ({len(ref):,} events) finds {len(selected)} unique temporal matches within two seconds among {len(own)} provisional events. ")
    if len(selected):
        text+=f"For these matches, the median absolute origin-time difference is {summary['median_absolute_time_difference_s']:.3f} s and median horizontal difference is {summary['median_horizontal_difference_km']:.3f} km (maximum {summary['maximum_horizontal_difference_km']:.3f} km). "
    text+=('These differences describe a limited VELEST pilot without TomoDD or manual phase review. ' if dataset=='continuation' else 'These differences describe an initial, uncalibrated sample. ')
    text+='Temporal proximity alone does not prove event identity, and unmatched events are not declared false detections. The comparison changes no independent data or setting.\n'
    (ROOT/('report/continuation_final_comparison.tex' if dataset=='continuation' else 'report/final_comparison.tex')).write_text(text)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',choices=['extended','continuation'],default='extended');args=parser.parse_args()
    print(json.dumps(compare(args.dataset),indent=2))
