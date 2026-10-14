"""Keep review labels while linking own candidates through shared observed picks.

No cross-cohort integer-ID join or author catalog. Unmatched candidates retain
explicitly labeled historical own geometry for downstream waveform checks only.
"""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_eida';OLD=ROOT/'data/coverage_extension';NEW=ROOT/'data/eida_continuation'
def keys(base):
    p=pd.read_csv(base/'picks.csv');a=pd.read_csv(base/'associations.csv');a=a.merge(p.reset_index(names='pick_index'),on='pick_index')
    return {eid:set(zip(g.trace_id,g.phase,g.time)) for eid,g in a.groupby('event_index')}
def main():
    D.mkdir(exist_ok=True);oldkeys=keys(OLD);newkeys=keys(NEW)
    old=pd.read_csv(OLD/'calibration/merged4/uncertainty/relocated_events.csv').set_index('event_index');new=pd.read_csv(NEW/'calibration/merged4/uncertainty/relocated_events.csv').set_index('event_index')
    candidates=sorted(pd.read_csv(ROOT/'data/mechanism_followup/measurements.csv').event_id.unique());rows=[];events=[]
    for eid in candidates:
        scores=sorted([(len(oldkeys[eid]&k),n) for n,k in newkeys.items() if n in new.index],reverse=True)
        matched=bool(scores and scores[0][0]>=4 and (len(scores)==1 or scores[0][0]>scores[1][0]))
        if matched:
            n=scores[0][1];row=new.loc[n].to_dict();dt=abs((pd.Timestamp(row['time'])-pd.Timestamp(old.loc[eid,'time'])).total_seconds());matched=dt<2
        if not matched:n=None;row=old.loc[eid].to_dict()
        row['event_index']=int(eid);row['current_event_index']=n;row['location_role']='Current own trial, linked by >=4 identical observed phases and unique maximum overlap, origin within 2 s' if matched else 'Historical own trial retained for downstream waveform check; not a current-catalog event'
        events.append(row);rows.append(dict(review_event=int(eid),current_event=n,matched=matched,common_phases=scores[0][0] if scores else 0,role=row['location_role']))
    # Additional candidates come only from the new own catalog and magnitudes.
    # ML is not Md: this >=2.2 screen is disclosed as an alternative to the
    # paper's duration-magnitude sample, never a routine-catalog event seed.
    magnitudes=pd.read_csv(NEW/'calibration/merged4/magnitude/magnitudes.csv')
    screen=pd.read_csv(NEW/'calibration/merged4/focal/polarity_screen.csv')
    covered={r['current_event'] for r in rows if r['matched']}
    larger=sorted(set(magnitudes.loc[magnitudes.ML>=2.2,'event_index']) & set(screen.event_id) - covered)
    for n in larger:
        eid=100000+int(n);row=new.loc[n].to_dict();row.update(event_index=eid,current_event_index=int(n),location_role='New own relocated candidate with own provisional ML>=2.2 and >=8 retained P picks; alternative to paper Md selection')
        events.append(row);rows.append(dict(review_event=eid,current_event=int(n),matched=True,common_phases=None,role=row['location_role']))
    pd.DataFrame(events).to_csv(D/'candidate_locations.csv',index=False);pd.DataFrame(rows).to_csv(D/'candidate_mapping.csv',index=False)
    (D/'candidate_mapping.json').write_text(json.dumps(dict(method=__doc__,candidates=len(rows),new_larger_candidates=len(larger),mapped=sum(r['matched'] for r in rows),model='data/eida_continuation/calibration/merged4/independent_calibrated.mod',accepted=False),indent=2)+'\n');print(rows)
if __name__=='__main__':main()
