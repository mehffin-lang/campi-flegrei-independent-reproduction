"""Transfer previous AI observations only when the displayed arrays are identical.

Changed or new packets are left unaccepted until explicitly visually reviewed.
This script does not make visual judgments. No human review is implied.
"""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_eida';OLD=ROOT/'data/mechanism_followup'
def main():
    prior=json.loads((ROOT/'config/mechanism_visual_decisions.json').read_text());f=pd.read_csv(D/'measurements.csv');old=pd.read_csv(OLD/'measurements.csv').set_index('key');a=np.load(D/'review_waveforms.npz');b=np.load(OLD/'review_waveforms.npz');rows=[]
    out=dict(prior);ids=sorted(str(e) for e in f.event_id.unique());out['accepted_polarities']={k:{} for k in ids};out['accepted_sp_windows']={k:[] for k in ids};out['evidence']='data/mechanism_eida/review/event_*.png; review_transfer.json and new_visual_review.json'
    for r in f.itertuples():
        key=r.key;row=dict(key=key,event_id=int(r.event_id),station=r.station,new_record=key not in old.index,polarity_window_identical=False,sp_window_identical=False)
        for field,suffixes in [('polarity_window_identical',['_raw','_z']),('sp_window_identical',['_three'])]:
            row[field]=all(key+s in a and key+s in b and np.array_equal(a[key+s],b[key+s],equal_nan=True) for s in suffixes)
        eid=str(r.event_id)
        if row['polarity_window_identical'] and r.station in prior['accepted_polarities'].get(eid,{}):out['accepted_polarities'][eid][r.station]=prior['accepted_polarities'][eid][r.station]
        if row['sp_window_identical'] and r.station in prior['accepted_sp_windows'].get(eid,[]):out['accepted_sp_windows'][eid].append(r.station)
        row['requires_new_visual_review']=not row['polarity_window_identical'] or not row['sp_window_identical']
        rows.append(row)
    pd.DataFrame(rows).to_csv(D/'review_transfer.csv',index=False)
    (ROOT/'config/mechanism_eida_decisions.json').write_text(json.dumps(out,indent=2)+'\n')
    receipt=dict(method=__doc__,records=len(rows),previous_records=len(old),new_records=sum(r['new_record'] for r in rows),identical_polarity_windows=sum(r['polarity_window_identical'] for r in rows),identical_sp_windows=sum(r['sp_window_identical'] for r in rows),unreviewed_changed_packets=sum(r['requires_new_visual_review'] for r in rows),human_reviews=0,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'measurements.csv',D/'review_waveforms.npz',OLD/'measurements.csv',OLD/'review_waveforms.npz',ROOT/'config/mechanism_visual_decisions.json']})
    receipt['review_array_hashes']={k:hashlib.sha256(a[k].tobytes()).hexdigest() for k in a.files}
    (D/'review_transfer.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
if __name__=='__main__':main()
