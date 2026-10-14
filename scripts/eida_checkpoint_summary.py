"""Seal current observations, access outcomes and actual numerical changes."""
from pathlib import Path
import gzip,hashlib,json,sqlite3,zipfile
import numpy as np,pandas as pd
from pyproj import Geod
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';B=D/'calibration/merged4'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    original=sqlite3.connect(ROOT/'inputs/continuation/acquisition.sqlite');target=ROOT/'tmp/eida_continuation/acquisition_snapshot.sqlite';dest=sqlite3.connect(target);original.backup(dest);original.close();dest.close()
    gz=D/'acquisition.sqlite.gz';gz.write_bytes(gzip.compress(target.read_bytes(),mtime=0));write(D/'acquisition_snapshot.json',dict(file=str(gz.relative_to(ROOT)),sha256=sha(gz)))
    import collect_continuous as collect
    acq=collect.summarize();write(D/'acquisition_summary.json',acq)
    receipts={}
    for name in ['data/calibration_followup/expanded/processed_input_receipts.json','docs/continuous_retrievals.json']:
        receipts.update({r['file']:r for r in read(ROOT/name) if r.get('file')})
    originals=read(D/'all_observation_inputs.json')
    for r in originals:
        old=receipts.get(r['file'],{});r['url']=old.get('url');r['retrieved_utc']=old.get('retrieved_utc')
        assert old.get('sha256')==r['sha256'],'Observation receipt mismatch: '+r['file']
    write(D/'observation_retrievals.json',originals)
    cfg=read(ROOT/'config/observations.json')
    intervals=pd.read_csv(D/'hybrid/hybrid_scan_intervals.csv')
    template_files=[f'inputs/waveforms/{label}_{sta}.mseed' for label in cfg['template_times'] for sta in ['CAAM','COLB']]
    scan_files=sorted(set(intervals.caam_file)|set(intervals.colb_file))
    write(D/'hybrid/provenance.json',dict(template_times=cfg['template_times'],
        templates=[dict(file=f,sha256=sha(ROOT/f),role='Original event-selected waveform used only as a documented matching template, not independent detection or exposure') for f in template_files],
        observations=[dict(file=f,sha256=sha(ROOT/f),role='Original continuous samples searched for similarity; sparse exposure') for f in scan_files],
        inputs=[dict(file='config/observations.json',sha256=sha(ROOT/'config/observations.json'))],
        limitation='Template events are specified in the written methods. Matching scores are newly computed; the known template events are not independently discovered. No author picks, catalog or result table is used.'))
    import process_continuous as picker
    previous={r['file'] for r in read(ROOT/'data/local_extension/input_jobs.json')}
    picked=[];identity=picker.inference_identity()
    for r in read(D/'input_jobs.json'):
        if r['file'] in previous:continue
        cache=picker.CACHE/(hashlib.sha256(r['file'].encode()).hexdigest()[:20]+'.json')
        q=read(cache)
        assert q['input_sha256']==r['sha256'] and q['settings']==picker.SETTINGS and q['inference_identity']==identity,r['file']
        picked.append(dict(file=r['file'],picks=len(q['picks']),P=sum(p['phase']=='P' for p in q['picks']),S=sum(p['phase']=='S' for p in q['picks']),cache_sha256=sha(cache)))
    write(D/'new_inference_counts.json',dict(files=len(picked),picks_before_merging=sum(p['picks'] for p in picked),P=sum(p['P'] for p in picked),S=sum(p['S'] for p in picked),records=picked,scope='New continuous files relative to local_extension manifest; overlapping cache picks are merged before association. Known event-selected snippets are excluded entirely.'))
    current=read(D/'analysis_summary.json');old=read(D/'baseline.json')['previous_analysis'];u=read(B/'uncertainty/summary.json');v=read(B/'validation.json');h=read(B/'heldout/summary.json');s=read(B/'summary.json');pan=read(B/'panels/summary.json');mag=read(B/'magnitude/magnitude_statistics.json')
    v['heldout_check']=str((B/'heldout/summary.json').relative_to(ROOT));v['heldout_result']=h.get('residual_improvement_s');v['limitation']='Held-out refitting and identical-input precision diagnostics were executed on this cohort. Absolute locations and phases remain unvalidated; regional-start and precision gates are retained. See the heldout record for failures as well as successful runs.';write(B/'validation.json',v)
    new=pd.read_csv(B/'uncertainty/relocated_events.csv');prior=pd.read_csv(ROOT/'data/local_extension/calibration/merged4/uncertainty/relocated_events.csv')
    nt=pd.to_datetime(new.time,utc=True).astype('int64').to_numpy()/1e9;ot=pd.to_datetime(prior.time,utc=True).astype('int64').to_numpy()/1e9;matches=[]
    for i,t in enumerate(nt):
        close=np.flatnonzero(abs(ot-t)<2)
        if len(close)!=1:continue
        j=close[0]
        if (abs(nt-ot[j])<2).sum()!=1:continue
        a=new.iloc[i];b=prior.iloc[j];dist=Geod(ellps='WGS84').inv(a.longitude,a.latitude,b.longitude,b.latitude)[2]
        matches.append(dict(current_event=int(a.event_index),previous_event=int(b.event_index),time_difference_s=t-ot[j],horizontal_m=dist,depth_difference_km=a.depth_km-b.depth_km))
    pd.DataFrame(matches).to_csv(D/'checkpoint_location_comparison.csv',index=False)
    batches=[read(p) for p in sorted(D.glob('retrieval_batch_*.json'))];requests=[r for b in batches for r in b['requests']];states=pd.Series([r['outcome']['status'] for r in requests]).value_counts().to_dict()
    summary=dict(previous_commit=read(D/'baseline.json')['previous_commit'],new_request_outcomes={str(k):int(x) for k,x in states.items()},new_bytes=sum(r['outcome']['bytes'] for r in requests),pending_requests=acq['jobs_by_status'].get('pending',0),full_study_coverage=False,old_processing=old,current_processing=current,
        changes={k:current[k]-old[k] for k in ['files','picks','events','assigned_picks','processed_channel_hours']},calibration_candidates=s['calibration_events'],causal_events=s['whole_catalog_events'],velest_filter_passes=s['paper_filter_passing'],relocated_events=len(new),previous_relocated_events=len(prior),relocation_validation=u,precision_validation=v,heldout=h,magnitude=mag,panel_summary=pan,
        location_comparison=dict(method='Unique reciprocal own-origin matches within 2 s, no paper catalog; diagnostic only, not proof of event identity',matches=len(matches),max_horizontal_m=max([r['horizontal_m'] for r in matches],default=None),max_absolute_depth_km=max([abs(r['depth_difference_km']) for r in matches],default=None)),
        scope='All known event-selected windows excluded from the new detection catalog and coverage. Sparse calendar sampling remains. Original observations, trained weights, alternative association profile and disclosed Tan-distributed starting grid only; routine Md enters only downstream calibration. No author result tables.')
    summary['request_checks']=dict(unique_request_ids=len({r['request']['id'] for r in requests}),requests=len(requests),no_duplicate_requests=len({r['request']['id'] for r in requests})==len(requests))
    assert summary['request_checks']['no_duplicate_requests']
    summary['sampling_purposes']=[{k:b.get(k) for k in ['selection','purpose','core_start','core_end','requested_limit']} for b in batches]
    selected=pd.read_csv(B/'selected_initial_events.csv')
    summary['calibration_dates']={str(k):int(n) for k,n in pd.to_datetime(selected.time,utc=True).dt.strftime('%Y-%m-%d').value_counts().sort_index().items()}
    phase_counts=pd.read_csv(B/'tomodd/retained_picks.csv').groupby(['event_index','phase']).size().unstack(fill_value=0)
    for label,ids in [('velest',phase_counts.index),('relocated',new.event_index)]:
        counts=phase_counts.loc[ids]
        summary.setdefault('phase_support',{})[label]=dict(events=len(counts),no_P=int(counts.P.eq(0).sum()),fewer_than_four_P=int(counts.P.lt(4).sum()),no_S=int(counts.S.eq(0).sum()),P=int(counts.P.sum()),S=int(counts.S.sum()))
    summary['location_distributions']={}
    for label,frame,base in [('previous',prior,ROOT/'data/local_extension/calibration/merged4'),('current',new,B)]:
        svd=pd.read_csv(base/'uncertainty/regional_svd.csv')
        summary['location_distributions'][label]=dict(events=len(frame),years={str(k):int(n) for k,n in pd.to_datetime(frame.time,utc=True).dt.year.value_counts().sort_index().items()},depth_quantiles_km=frame.depth_km.quantile([0,.25,.5,.75,1]).to_dict(),depth_over_5_km=int(frame.depth_km.gt(5).sum()),zero_cc=int((frame.ncc_p+frame.ncc_s).eq(0).sum()),cc_ge_100=int((frame.ncc_p+frame.ncc_s).ge(100).sum()),conditional_svd_events=len(svd),median_svd_errors_m=svd[['error_x_m','error_y_m','error_z_m']].median().to_dict(),maximum_svd_errors_m=svd[['error_x_m','error_y_m','error_z_m']].max().to_dict())
    if matches:
        frame=pd.DataFrame(matches)
        summary['location_comparison'].update(median_horizontal_m=float(frame.horizontal_m.median()),median_absolute_depth_km=float(frame.depth_difference_km.abs().median()))
    write(D/'result_summary.json',summary)
    records={}
    with zipfile.ZipFile(D/'calibration/run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted((ROOT/'tmp/eida_continuation').rglob('*')):
            if p.is_file() and p.suffix not in ['.npz','.sqlite']:
                name=str(p.relative_to(ROOT/'tmp/eida_continuation'));z.write(p,name);records[name]=sha(p)
    write(D/'calibration/run_records.json',records)
    print({k:summary[k] for k in ['new_request_outcomes','new_bytes','pending_requests','changes','calibration_candidates','velest_filter_passes','relocated_events','location_comparison']})
if __name__=='__main__':main()
