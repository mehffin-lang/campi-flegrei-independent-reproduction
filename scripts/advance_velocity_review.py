"""Bounded training-only continuation; old runs and the 2025 arrivals stay fixed."""
import os
os.environ['VELOCITY_REVIEW_VERSION']='sync_training_review_20261015'
import argparse, json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import UTCDateTime as U, read, read_inventory, Inventory
import extend_velocity_training as e

R,D,I=e.R,e.D,e.I
OLD=R/'data/velocity_holdout_review/training_extension_20261015'
W=R/'tmp/velocity_holdout_review'/D.name

def plan():
    assert not (D/'plan.json').exists(), 'Preserve the registered experiment'
    for p in [D,I,W]:p.mkdir(parents=True,exist_ok=True)
    prior={str(p.relative_to(R)):e.sha(p) for p in (R/'data/velocity_holdout_review').rglob('*') if p.is_file() and D not in p.parents}
    e.dump(D/'prior_hashes.json',prior)
    shutil.copy2(OLD/'holdout_lock.json',D/'holdout_lock.json')
    shutil.copy2(R/'report/document_build.json',D/'initial_pdf_sync.json')
    frames=[pd.read_csv(OLD/'pre2025_stored_intervals.csv'),pd.read_csv(OLD/'target_waveform_intervals.csv')]
    frames += [pd.read_csv(p) for p in OLD.glob('ties_*/target_waveform_intervals.csv')]
    existing=pd.concat(frames,ignore_index=True).drop_duplicates();assert (existing.end<=e.END).all()
    existing.to_csv(D/'pre2025_stored_intervals.csv',index=False)
    target=existing[existing.channel.str.split('.').str[1].isin(e.TARGET)]
    target.to_csv(D/'target_existing_intervals.csv',index=False)
    report=[]
    for ch,g in target.groupby('channel'):
        spans=e.av.union(zip(g.start,g.end));report.append(dict(channel=ch,files=g.file.nunique(),hours=sum(b-a for a,b in spans)/3600,first=str(U(min(g.start))),last=str(U(max(g.end)))))
    pd.DataFrame(report).to_csv(D/'local_target_coverage.csv',index=False)
    a=float(U('2024-12-13'));b=a+7200
    rate=json.loads((OLD/'download_plan.json').read_text())['measured_bytes_per_channel_s']
    jobs=[]
    for sta,(net,band) in e.TARGET.items():
        missing=[]
        for comp in 'ENZ':
            g=target[target.channel.eq(f'{net}.{sta}..{band}{comp}')]
            missing.extend(e.av.subtract([(a,b)],zip(g.start,g.end)))
        assert missing
        ident=f'{net}_{sta}_{band}_{U(a).strftime("%Y%m%dT%H%M%S")}_{U(b).strftime("%Y%m%dT%H%M%S")}'
        jobs.append(dict(id=ident,net=net,sta=sta,band=band,start=a,end=b,missing_channel_s=sum(y-x for x,y in missing),estimated_bytes=rate*sum(y-x for x,y in missing)))
    budget=json.loads((OLD/'storage_budget.json').read_text());reserve=budget['reserve_bytes']+budget['processing_headroom_bytes'];free=shutil.disk_usage(R).free
    estimate=sum(j['estimated_bytes'] for j in jobs);assert free-2*estimate>reserve
    e.dump(D/'storage_budget.json',budget)
    e.dump(D/'download_plan.json',dict(requests=jobs,estimated_bytes=estimate,measured_bytes_per_channel_s=rate,free_bytes=free,protected_bytes=reserve,
        selection='Next calendar day after previous December12 window, 00--02UTC; no event catalog or holdout used. Six targets only; no backlog.',uncertainty='Measured compressed rate; twofold size allowance.'))
    p=json.loads((OLD/'fit_preregistration.json').read_text())
    p.update(training_rule='Preserve preceding cap5/cap8 selections; exclude unresolved training phases/events only after raw-waveform review, reapply unchanged event screen. Add any newly reviewed eligible events. No review or selection on 2025.',
        gate_on_refitting='Only after justified training observation changes; no refit of unchanged input.',registered_before_new_inference=True,
        prior_source=str(OLD.relative_to(R)),inputs={},review_focus='Previously flagged training ambiguities in current selected events; new target-station window.')
    e.dump(D/'plan.json',p)
    decisions=pd.read_csv(R/'data/velocity_holdout_review/review/decisions.csv')
    ids=set(pd.read_csv(OLD/'fits/training_cap5.csv').event_index)|set(pd.read_csv(OLD/'fits/training_cap8.csv').event_index)
    decisions=decisions[(decisions.role=='training')&decisions.event_index.isin(ids)]
    decisions.to_csv(D/'prior_training_review.csv',index=False)
    print('Planned requests',len(jobs),'estimated bytes',int(estimate),'free',free,'reserve',reserve)
    print('Inherited review candidates',decisions[['event_index','station','phase','status']].to_dict('records'))

def review():
    """Save original pre-2025 traces, enlarged uncertain windows, and metadata."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dec=pd.read_csv(D/'prior_training_review.csv');dec=dec[dec.status=='ambiguous']
    inv=sum((read_inventory(str(p)) for p in (R/'inputs/continuation').glob('*_responses.xml')),Inventory(networks=[],source='Existing EIDA epochs'))
    arrays={};rows=[]
    out=D/'review/inherited';out.mkdir(parents=True,exist_ok=True)
    for row in dec.itertuples():
        t=U(row.time);assert t< U('2025-01-01')
        st=read(str(R/row.source),starttime=t-3,endtime=t+4).select(network=row.station.split('.')[0],station=row.station.split('.')[1])
        fig,axes=plt.subplots(3,1,figsize=(10,6),layout='constrained')
        for ax,tr in zip(axes,sorted(st,key=lambda tr:tr.id)):
            x=tr.times()+float(tr.stats.starttime-t);raw=tr.data.astype(float);raw-=raw.mean();flt=tr.copy().detrend('linear').filter('bandpass',freqmin=1,freqmax=20,corners=2,zerophase=True).data
            ax.plot(x,raw/max(abs(raw).max(),1e-20),c='.65',lw=.7);ax.plot(x,flt/max(abs(flt).max(),1e-20),c='black',lw=.7);ax.axvline(0,c='red');ax.set(title=tr.id,xlabel='Seconds from original project pick',yticks=[])
            key=f'r{row.review_id}_{tr.id}';arrays[key]=np.vstack([x,raw,flt])
            match=inv.select(network=tr.stats.network,station=tr.stats.station,location=tr.stats.location,channel=tr.stats.channel,time=t)
            channels=[ch for n in match for s in n for ch in s]
            rows.append(dict(review_id=row.review_id,event_index=row.event_index,trace=tr.id,source=row.source,sha256=e.sha(R/row.source),pick_time=row.time,phase=row.phase,metadata_matches=len(channels),response=bool(channels and channels[0].response),sample_rate=tr.stats.sampling_rate,metadata_rate=channels[0].sample_rate if channels else None,gaps=st.select(id=tr.id).get_gaps()))
        fig.suptitle(f'Training review {row.review_id}: event {row.event_index}, {row.station} {row.phase}\n{row.time}; gray raw, black 1--20Hz; no time correction')
        fig.savefig(out/f'review_{row.review_id}.png',dpi=130);plt.close(fig)
    np.savez_compressed(out/'windows.npz',**arrays);e.dump(out/'metadata.json',rows)
    print('Saved ambiguous training reviews',len(dec),'traces',len(rows))

def prepare():
    """Remove only documented uncertain training observations; reapply screen."""
    from estimate_observational_profile import canonical_cnv
    out=D/'training_catalog';out.mkdir(exist_ok=True)
    original=[pd.read_csv(OLD/f'fits/training_cap{cap}.csv') for cap in [5,8]]
    ids=set(pd.concat(original).event_index)-{100000}
    p=pd.read_csv(e.C/'picks.csv');a=pd.read_csv(e.C/'associations.csv');a=a[a.event_index.isin(ids)].copy()
    selected=sorted(a.pick_index.unique());p=p.loc[selected].copy();assert (p.time<'2025-01-01').all()
    p['original_pick_index']=p.index;p['source_catalog']=str(e.C.relative_to(R))
    mapping={old:new for new,old in enumerate(p.index)};a['pick_index']=a.pick_index.map(mapping);p=p.reset_index(drop=True)
    # Previous December12 reviewed event, with its original independent times.
    qp=pd.read_csv(OLD/'qc/picks.csv');qa=pd.read_csv(OLD/'qc/associations.csv');qa['event_index']+=100000;qa['pick_index']+=len(p)
    qp['source_catalog']=str((OLD/'qc').relative_to(R));p=pd.concat([p,qp],ignore_index=True);a=pd.concat([a,qa],ignore_index=True)
    events=pd.concat(original).drop_duplicates('event_index').sort_values('time')
    # Newly admitted records must be explicitly reviewed before this stage.
    if (D/'qc/accepted_events.csv').exists():
        npick=pd.read_csv(D/'qc/picks.csv');na=pd.read_csv(D/'qc/associations.csv');ne=pd.read_csv(D/'qc/accepted_events.csv')
        assert (npick.time<'2025-01-01').all() and (ne.time<'2025-01-01').all()
        npick['source_catalog']=str((D/'qc').relative_to(R));na['pick_index']+=len(p);na['event_index']+=200000;ne['event_index']+=200000
        p=pd.concat([p,npick],ignore_index=True);a=pd.concat([a,na],ignore_index=True);events=pd.concat([events,ne],ignore_index=True)
    decisions=pd.read_csv(D/'reviewed_arrivals.csv');uncertain=set(decisions.pick_index)
    excluded=p.index[p.source_catalog.eq(str(e.C.relative_to(R)))&p.original_pick_index.isin(uncertain)]
    before=len(a);a=a[~a.pick_index.isin(excluded)&~a.event_index.eq(1532)].copy()
    retained=sorted(a.pick_index.unique());mapping={old:new for new,old in enumerate(retained)};p=p.loc[retained].reset_index(drop=True);a['pick_index']=a.pick_index.map(mapping)
    events=events[events.event_index.isin(a.event_index)].sort_values('time')
    p.to_csv(out/'picks.csv',index=False);a.to_csv(out/'associations.csv',index=False);events.to_csv(out/'initial_events.csv',index=False)
    shutil.copy2(e.C/'stations.csv',out/'stations.csv')
    subprocess.run([sys.executable,'scripts/prepare_observational_selection.py','--observations',str(out.relative_to(R))],check=True)
    selected_events=pd.read_csv(out/'selection/selected_initial_events.csv')
    aliases=pd.read_csv(R/'data/velocity_holdout_review/station_aliases.csv');alias=dict(zip(aliases.id,aliases.alias))
    F=D/'fits';F.mkdir(exist_ok=True);counts=[]
    for cap,old in zip([5,8],original):
        permitted=set(old.event_index)|{i for i in events.event_index if i>=200000}
        sub=selected_events[selected_events.event_index.isin(permitted)].sort_values('time')
        sub.to_csv(F/f'training_cap{cap}.csv',index=False);cnv=canonical_cnv(sub,p,a,alias);(F/f'training_cap{cap}.cnv').write_text(cnv)
        assert cnv!=(OLD/f'fits/training_cap{cap}.cnv').read_text(),'No justified change: do not refit'
        counts.append(dict(cap=cap,events=len(sub),arrivals=int(a.event_index.isin(sub.event_index).sum()),removed_event_ids=sorted(set(old.event_index)-set(sub.event_index))))
    plan=json.loads((D/'plan.json').read_text());plan['inputs']={str(f.relative_to(R)):e.sha(f) for f in [D/'reviewed_arrivals.csv',D/'reviewed_events.json',*sorted(out.glob('*.csv')),*sorted(F.glob('training_cap*'))]}
    e.dump(F/'plan.json',plan);e.dump(D/'training_changes.json',dict(counts=counts,phase_and_event_exclusions=before-len(a),removed_ambiguous_phases=len(excluded),holdout_modified=False))
    subset=a[a.event_index.isin(pd.read_csv(F/'training_cap5.csv').event_index)].join(p,on='pick_index')
    gaps=[]
    for row in pd.read_csv(OLD/'training_gap_counts_after.csv').itertuples():
        g=subset[(subset.trace_id==row.station)&(subset.phase==row.phase)]
        gaps.append(dict(station=row.station,phase=row.phase,before=row.after_training_arrivals,after=len(g),events=g.event_index.nunique()))
    pd.DataFrame(gaps).to_csv(D/'training_gap_counts.csv',index=False)
    print('Updated training',counts,flush=True)

def fit_stage(stage):
    import fit_extended_training as f
    f.F=D/'fits';f.W=W/'fits';f.setup()
    getattr(f,stage)()

def diagnose():
    """Inspect saved training runs only, including the first precision divergence."""
    import calibration_chain as c
    from estimate_observational_profile import station_delta
    F=OLD/'fits';native=R/'tmp/velocity_holdout_review'/OLD.name/'fits'
    summary=json.loads((F/'training_summary.json').read_text());rows=[];inputs=[]
    for fam in ['four_regularized','three_regularized','three_zero_delays']:
        a=fam+'_base';b=fam+'_precision32'
        for name in ['input.cnv','input.mod','input.sta','velest.cmn']:
            paths=[native/(n+'_prelocation')/name for n in [a,b]]
            inputs.append(dict(family=fam,file=name,identical=paths[0].read_bytes()==paths[1].read_bytes(),sha64=e.sha(paths[0]),sha32=e.sha(paths[1])))
        for stage in ['prelocation','velocity_only','joint1','joint2','joint3','joint4','joint5']:
            loc=[pd.read_csv(F/(n+'_'+stage+'_locations.csv')) for n in [a,b]]
            model=[pd.read_csv(F/(n+'_'+stage+'_model.csv')) for n in [a,b]]
            change=c.compare(*loc)
            joined=loc[0].merge(loc[1],on='event_index',suffixes=('_64','_32'));joined['abs_depth_change']=abs(joined.depth_km_64-joined.depth_km_32)
            worst=joined.sort_values('abs_depth_change',ascending=False).iloc[0]
            rows.append(dict(family=fam,stage=stage,**change,max_velocity_km_s=float(abs(model[0][['Vp_km_s','Vs_km_s']].to_numpy()-model[1][['Vp_km_s','Vs_km_s']].to_numpy()).max()),max_station_s=station_delta((native/(a+'_'+stage)/'output.sta').read_text(),(native/(b+'_'+stage)/'output.sta').read_text()),worst_depth_event=int(worst.event_index),depth64=worst.depth_km_64,depth32=worst.depth_km_32))
    pd.DataFrame(rows).to_csv(D/'saved_precision_diagnosis.csv',index=False);e.dump(D/'saved_precision_inputs.json',inputs)
    import re
    iterations=[]
    for fam in ['three_regularized','four_regularized']:
        for bits,variant in [(64,'base'),(32,'precision32')]:
            path=native/f'{fam}_{variant}_prelocation/run.out';iteration=None
            for line in path.read_text().splitlines():
                m=re.search(r'Iteration nr\s+(\d+) obtained',line)
                if m:iteration=int(m[1])
                m=re.search(r'RMS RESIDUAL=\s+([\d.]+)',line)
                if m:iterations.append(dict(family=fam,bits=bits,iteration=iteration,native_rms_s=float(m[1]),source=str(path.relative_to(R))))
    pd.DataFrame(iterations).to_csv(D/'saved_precision_iteration_rms.csv',index=False)
    records=[];dec=pd.read_csv(D/'reviewed_arrivals.csv');aliases=pd.read_csv(R/'data/velocity_holdout_review/station_aliases.csv');alias=dict(zip(aliases.id,aliases.alias))
    bad={(int(x.event_index),alias[x.station],x.phase) for x in dec.itertuples()}
    for fam in ['four_regularized','three_regularized','three_zero_delays']:
        x=pd.read_csv(F/(fam+'_base_training_residuals.csv'));x['review_excluded']=[(i,a,p) in bad or i==1532 for i,a,p in zip(x.event_index,x.alias,x.phase)]
        for excluded,g in x.groupby('review_excluded'):
            records.append(dict(family=fam,review_excluded=bool(excluded),arrivals=len(g),rms_s=float(np.sqrt(np.mean(g.residual_s**2))),sum_squared_s2=float(sum(g.residual_s**2))))
    pd.DataFrame(records).to_csv(D/'saved_training_review_residuals.csv',index=False)
    print(pd.DataFrame(rows)[['family','stage','max_depth_km','max_velocity_km_s','max_station_s']].to_string(index=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['plan','query','retrieve','review','prepare','fit','validate','diagnose']);a=ap.parse_args()
    if a.stage in ['query','retrieve']:getattr(e,a.stage)()
    elif a.stage in ['fit','validate']:fit_stage(a.stage)
    else:globals()[a.stage]()
