"""Reuse an own daily solve only for an identical multiset of numerical inputs.

This is an optimization of repeated inference extensions, not a catalog seed.
Changed days run GaMMA normally. Parent event and pick IDs are explicitly
remapped. Identical-time row permutations reuse the recorded original solve;
this does not assert bitwise equality for a fresh solve in a different order.
Comparison uses precisely id, timestamp, type and probability, the columns
consumed with use_amplitude=False. Source filenames for duplicate recordings
are not association inputs; the current original-waveform identity is retained.
"""
from pathlib import Path
import hashlib,json,io,copy
import pandas as pd

def install(root, output, parent, strict_reuse=False):
    import gamma.utils as gu
    from gamma_reproducibility import install as deterministic
    deterministic()
    checkpoint=json.loads((parent/'processing_checkpoint.json').read_text())
    for name,digest in checkpoint['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    original=gu.association
    cfg=json.loads((root/'config/continuation_association.json').read_text())
    stations=pd.read_csv(parent/'stations.csv')
    picks=pd.read_csv(parent/'picks.csv',float_precision='round_trip').rename(columns=dict(trace_id='id',time='timestamp',phase='type',probability='prob'))
    picks.timestamp=pd.to_datetime(picks.timestamp,utc=True,format='ISO8601')
    picks=picks[picks.id.isin(stations.id)]
    events=pd.read_csv(parent/'initial_events.csv',float_precision='round_trip')
    assignments=pd.read_csv(parent/'associations.csv',float_precision='round_trip')
    receipt=[]
    columns=['id','timestamp','type','prob']
    def canonical(frame):
        return frame.sort_values(list(frame.columns)).to_csv(index=False).encode()
    station_bytes=canonical(stations)
    def association(frame,station,config,method='BGMM',**kwargs):
        day=frame.timestamp.iloc[0].date()
        old=picks[picks.timestamp.dt.date==day]
        same=(canonical(old[columns])==canonical(frame[columns]) and canonical(station)==station_bytes and json.dumps(config,sort_keys=True)==json.dumps(cfg,sort_keys=True) and method=='BGMM' and not kwargs)
        record=dict(day=str(day),picks=len(frame),reused=bool(same),input_sha256=hashlib.sha256(canonical(frame[columns])).hexdigest())
        if same:
            used=assignments[assignments.pick_index.isin(old.index)].copy()
            event_ids=sorted(used.event_index.unique())
            idmap={event:i for i,event in enumerate(event_ids)}
            assert not old.duplicated(columns).any() and not frame.duplicated(columns).any()
            joined=old[columns].reset_index(names='old_index').merge(frame[columns].reset_index(names='new_index'),on=columns,validate='one_to_one')
            assert len(joined)==len(frame)
            indexmap=dict(zip(joined.old_index,joined.new_index))
            ev=events[events.event_index.isin(event_ids)].to_dict('records')
            for row in ev:row['event_index']=idmap[row['event_index']]
            ass=[(indexmap[r.pick_index],idmap[r.event_index],r.score) for r in used.itertuples()]
        else:
            assert not strict_reuse,'Probe found changed association inputs; no solve launched'
            ev,ass=original(frame,station,config,method=method,**kwargs)
        record['events']=len(ev);receipt.append(record)
        (output/'association_reuse.json').write_text(json.dumps(dict(parent=str(parent.relative_to(root)),parent_checkpoint_sha256=hashlib.sha256((parent/'processing_checkpoint.json').read_bytes()).hexdigest(),policy=__doc__,days=receipt),indent=2)+'\n')
        return ev,ass
    gu.association=association
