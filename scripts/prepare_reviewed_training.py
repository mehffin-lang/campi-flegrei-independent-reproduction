"""Apply recorded visual review of original training traces, then reassociate.

The one manually measured onset below is from raw EIDA samples, not a model
prediction or published figure. Review is by Codex, not a human seismologist.
Ambiguous CUMA/CSOC observations and possible coda associations are not fitted.
"""
import json,copy,subprocess,sys
import pandas as pd,numpy as np
from obspy import UTCDateTime as U
from pyproj import Transformer
from extend_velocity_training import R,D,sha,dump

def main():
    cat=D/'catalog_ties_dec12';out=D/'qc';out.mkdir(exist_ok=True)
    p=pd.read_csv(cat/'picks.csv');a=pd.read_csv(cat/'associations.csv');events=pd.read_csv(cat/'initial_events.csv');assert (p.time<'2025-01-01').all()
    ap=a.join(p,on='pick_index');decisions=[];keep=[]
    for row in ap.itertuples():
        accept=row.event_index==0;reason='Visible first P or first S packet, consistent with the network event; retain original measured time.'
        if row.event_index!=0:accept=False;reason='Later marker lies within the established event coda; a distinct new event is not established. Preserve as uncertain, exclude from calibration.'
        elif row.trace_id=='IV.CUMA.':accept=False;reason='Raw motion is dominated by long-period background; P/S onset not resolved reliably. Preserve as uncertain.'
        elif row.trace_id=='IV.CRUS.' and row.phase=='S':accept=False;reason='Assigned S is a later strong coda peak; an earlier independently picked horizontal onset is reviewed separately.'
        elif row.trace_id=='IV.CAAM.' and row.phase=='S':accept=False;reason='Multiple horizontal increases; exact first S onset remains ambiguous.'
        decisions.append(dict(source_catalog=str(cat.relative_to(R)),original_pick_index=row.pick_index,original_event=row.event_index,station=row.trace_id,phase=row.phase,original_time=row.time,reviewed_time=row.time,decision='accepted' if accept else 'uncertain_excluded',reason=reason,reviewer='Codex visual review; not human validation',source=row.source,time_changed=False))
        if accept:keep.append(row.pick_index)
    # This earlier PhaseNet S candidate is visible on the raw three components.
    earlier=p[(p.trace_id=='IV.CRUS.')&(p.phase=='S')&(p.time>'2024-12-12T04:34:27.3')&(p.time<'2024-12-12T04:34:27.6')]
    assert len(earlier)==1
    idx=earlier.index[0];row=earlier.iloc[0];keep.append(idx)
    decisions.append(dict(source_catalog=str(cat.relative_to(R)),original_pick_index=int(idx),original_event=None,station=row.trace_id,phase='S',original_time=row.time,reviewed_time=row.time,decision='accepted_reassociated',reason='First coherent horizontal amplitude increase following the vertical P; earlier than the assigned large coda peak. Original PhaseNet time retained.',reviewer='Codex visual review; not human validation',source=row.source,time_changed=False))
    q=p.loc[keep].copy();q['original_pick_index']=q.index;q['measurement']='PhaseNet time retained after visual review';q['review_uncertainty_s']=np.nan
    # Manual P: abrupt vertical onset in raw counts at 26.21 s, with quiet
    # preceding baseline. Zero-phase filtered trace is display only, not timing.
    source=p[p.trace_id.eq('2I.CGAU.')].source.iloc[0]
    manual=dict(source=source,trace_id='2I.CGAU.',phase='P',time='2024-12-12T04:34:26.210000Z',probability=1.,original_pick_index=np.nan,measurement='Manual onset from raw samples; probability field is unit review weight, NOT a PhaseNet probability',review_uncertainty_s=.03)
    q=pd.concat([q,pd.DataFrame([manual])],ignore_index=True).sort_values('time').reset_index(drop=True)
    decisions.append(dict(source_catalog=str(cat.relative_to(R)),original_pick_index=None,original_event=None,station='2I.CGAU.',phase='P',original_time='',reviewed_time=manual['time'],decision='accepted_manual',reason='Abrupt raw vertical onset at 26.21 s, before coherent S; estimated reading uncertainty 0.03 s. Later automated P at 28.00 s is in coda.',reviewer='Codex visual review; not human validation',source=source,time_changed=True))
    for station,phase in [('2I.CSOC.','P'),('2I.CSOC.','S')]:
        decisions.append(dict(station=station,phase=phase,decision='uncertain_no_arrival',reason='No distinguishable onset above local background at the network event; no pick created.',reviewer='Codex visual review; not human validation',time_changed=False))
    pd.DataFrame(decisions).to_csv(out/'reviewed_arrivals.csv',index=False);q.to_csv(out/'picks.csv',index=False)
    stations=pd.read_csv(cat/'stations.csv');stations.to_csv(out/'stations.csv',index=False)
    config=json.loads((cat/'association_config.json').read_text());dump(out/'association_config.json',config)
    from gamma_reproducibility import install
    install()
    from gamma.utils import association
    np.random.seed(0)
    table=q.rename(columns=dict(trace_id='id',time='timestamp',phase='type',probability='prob'));table['timestamp']=pd.to_datetime(table.timestamp,utc=True,format='ISO8601')
    ev,ass=association(table,stations,copy.deepcopy(config),method='BGMM')
    trans=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    for e in ev:e.pop('magnitude',None);e['longitude'],e['latitude']=trans.transform(e['x(km)'],e['y(km)'],direction='INVERSE')
    pd.DataFrame(ev).to_csv(out/'initial_events.csv',index=False);pd.DataFrame(ass,columns=['pick_index','event_index','score']).to_csv(out/'associations.csv',index=False)
    subprocess.run([sys.executable,str(R/'scripts/prepare_observational_selection.py'),'--observations',str(out.relative_to(R))],check=True)
    selected=pd.read_csv(out/'selection/selected_initial_events.csv');selected.to_csv(out/'accepted_events.csv',index=False)
    dump(out/'review_record.json',dict(accepted_events=len(selected),reviewed_input_arrivals=len(q),manual_P_onsets=1,reassigned_existing_S=1,holdout_used=False,
        original_waveform_window_evidence='review/ties_dec12/windows.npz and onset_zoom.png; original miniSEED checksums in receipts',
        independent_human_review=False,uncertainty='Manual onset reading interval is not a statistical confidence interval; admitted event/location remains provisional.',
        final_event_gate='Unchanged pre-inversion quality screen; passing it does not validate the velocity model.',
        inputs={str(f.relative_to(R)):sha(f) for f in [cat/'picks.csv',cat/'associations.csv',cat/'initial_events.csv',D/'review/ties_dec12/windows.npz',D/'review/ties_dec12/metadata.csv',Path(__file__)]}))
    print('Reviewed arrivals',len(q),'selected events',len(selected),flush=True)

from pathlib import Path
if __name__=='__main__':main()
