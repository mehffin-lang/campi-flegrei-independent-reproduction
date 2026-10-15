"""Check saved fits, observations and ray paths; never fit the held-out data."""
import argparse,json,hashlib,re
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read_inventory,UTCDateTime
import calibration_chain as c,run_velest as v
import estimate_observational_profile as old
from test_velocity_parameterizations import ray_rows,paired

R=c.ROOT;D=R/'data/velocity_holdout_review';W=R/'tmp/velocity_holdout_review/runs'
C=R/'data/availability_extension/catalog_december';V=R/'data/availability_extension/velocity_december'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))

def ablations():
    c.OUT=D;c.WORK=R/'tmp/velocity_holdout_review/ablations';c.WORK.mkdir(exist_ok=True);v.controls=old.controls
    ids=pd.read_csv(D/'holdout_events.csv').event_index.tolist();cnv=(D/'frozen_holdout.cnv').read_text()
    original=R/'tmp/availability_extension/velocity_december/base_prelocation'
    zero=(original/'input.sta').read_text();initial=(original/'input.mod').read_text();fit=(V/'base_fitted.mod').read_text();delays=(V/'base_fitted.sta').read_text();out=[]
    for name,model,sta in [('old_velocity_zero_delays',fit,zero),('initial_velocity_old_delays',initial,delays)]:
        _,_,r=c.run(name,model,sta,cnv,ids,corrections=True,fixed=True,iterations=35);out.append(r)
    dump(D/'ablation_summary.json',out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ablations',action='store_true');args=ap.parse_args()
    if args.ablations:ablations()
    summary=json.loads((D/'summary.json').read_text());assert len(summary['runs'])==18 and all(r.get('finished') for r in summary['runs'].values())
    plan=json.loads((D/'experiment_plan.json').read_text())
    for f,h in plan['inputs'].items():assert c.sha(R/f)==h,f
    assert c.sha(D/'frozen_holdout.cnv')==plan['holdout_sha256']
    picks=pd.read_csv(C/'picks.csv');ass=pd.read_csv(C/'associations.csv');aliases=pd.read_csv(D/'station_aliases.csv').set_index('alias').id
    hold=pd.read_csv(D/'holdout_events.csv');statistics=[];stationrows=[];dayrows=[];raychecks=[];raystats=[];supports=[];profiles=[]
    for name,rec in summary['runs'].items():
        cap=8 if rec['variant']=='selection' else 5
        train=pd.read_csv(D/f'training_cap{cap}.csv');tr=pd.read_csv(D/(name+'_training_residuals.csv'))
        counts=tr.groupby(['alias','phase']).size();a=pd.read_csv(D/(name+'_holdout_initialization_residuals.csv'));b=pd.read_csv(D/(name+'_holdout_fitted_residuals.csv'))
        keys=['event_ordinal','event_index','alias','phase'];assert a[keys].equals(b[keys]);a['fitted_residual_s']=b.residual_s
        a['training_count']=[int(counts.get((r.alias,r.phase),0)) for r in a.itertuples()];a['station']=a.alias.map(aliases)
        a['date']=a.event_index.map(hold.set_index('event_index').time.str[:10]);a.to_csv(D/(name+'_paired_holdout.csv'),index=False)
        for label,mask in [('represented',a.training_count.gt(0)),('unrepresented',a.training_count.eq(0))]:
            g=a[mask];supports.append(dict(trial=name,support=label,arrivals=len(g),station_phase_pairs=len(g[['station','phase']].drop_duplicates()),initial_rms_s=rms(g.residual_s),fitted_rms_s=rms(g.fitted_residual_s)))
        for (station,phase),g in a.groupby(['station','phase']):stationrows.append(dict(trial=name,station=station,phase=phase,training_count=int(g.training_count.iloc[0]),holdout_count=len(g),initial_rms_s=rms(g.residual_s),fitted_rms_s=rms(g.fitted_residual_s),mean_fitted_s=float(g.fitted_residual_s.mean())))
        for date,g in a.groupby('date'):dayrows.append(dict(trial=name,date=date,events=g.event_index.nunique(),arrivals=len(g),initial_rms_s=rms(g.residual_s),fitted_rms_s=rms(g.fitted_residual_s)))
        m=pd.read_csv(D/(name+'_profile.csv'));profiles.append(m.assign(trial=name,family=rec['family']))
        statistics.append(dict(trial=name,family=rec['family'],variant=rec['variant'],training_events=len(train),training_arrivals=len(tr),training_initial_rms_s=rec['runs'][0]['residual_rms_s'],training_fitted_rms_s=rec['runs'][-1]['residual_rms_s'],holdout_initial_rms_s=rec['holdout']['initialization']['residual_rms_s'],holdout_fitted_rms_s=rec['holdout']['fitted']['residual_rms_s'],holdout_extra_rms_s=rec['holdout']['fitted_extra']['residual_rms_s'],iteration_gate=rec['last_change_gate'],physical=rec['positive_bulk_modulus'] and rec['monotonic'],holdout_location_converged=rec['holdout_location_converged'],accepted=rec['accepted']))
        if rec['variant']!='base':continue
        for role,stage,ev in [('training','joint5',train),('holdout','holdout_fitted',hold)]:
            work=W/(name+'_'+stage);rays=pd.read_csv(D/(work.name+'_rays.csv'));res=paired(work,ev)
            locations=pd.read_csv(D/(work.name+'_locations.csv')).set_index('event_index')
            depthdiff=(rays.source_depth_km-rays.event_index.map(locations.depth_km)).abs()
            # Independent travel-time sum along rounded native ray segments.
            speed={(phase,float(t)):float(speed) for phase,field in [('P','Vp_km_s'),('S','Vs_km_s')] for t,speed in zip(m.layer_top_km,m[field])}
            rays['travel_s']=[r.ray_length_km/speed[(r.phase,r.layer_top_km)] for r in rays.itertuples()]
            travel=rays.groupby(['event_index','alias','phase']).travel_s.sum()
            st=(work/'output.sta').read_text();delay={(l[:4],ph):float(l[start:end]) for l in st.splitlines()[1:] if l[:4].strip() for ph,start,end in [('P',34,39),('S',41,46)]}
            blocks=re.split(r'\n\s*\n',(work/'output.cnv').read_text().strip())
            tt=[float(t[6:12]) for block in blocks for line in block.splitlines()[1:] for t in [line[j:j+12] for j in range(0,len(line),12)] if t.strip()]
            differences=[]
            for r,obs in zip(res.itertuples(),tt):differences.append(obs-travel[(r.event_index,r.alias,r.phase)]-delay[(r.alias,r.phase)]-r.residual_s)
            raychecks.append(dict(trial=name,role=role,arrivals=len(res),max_ray_vs_output_depth_km=float(depthdiff.max()),travel_time_check_rms_s=rms(differences),travel_time_check_max_abs_s=float(np.max(abs(np.array(differences)))),note='Vertices and output CNV are rounded to 0.01 km and 0.01 s; this is a consistency check, not additional measured arrivals.'))
            for (phase,top),g in rays.groupby(['phase','layer_top_km']):raystats.append(dict(trial=name,role=role,phase=phase,layer_top_km=top,rays_crossing=int(g.ray_length_km.gt(0).sum()),total_rays=len(g),total_length_km=float(g.ray_length_km.sum()),horizontal_segment_km=float(g.horizontal_segment_km.sum()),source_events=int(g[g.source_depth_km.ge(top)&g.source_depth_km.lt(m.layer_top_km[m.layer_top_km.gt(top)].min() if any(m.layer_top_km.gt(top)) else np.inf)].event_index.nunique())))
    pd.DataFrame(statistics).to_csv(D/'experiment_results.csv',index=False);pd.DataFrame(supports).to_csv(D/'holdout_support.csv',index=False);pd.DataFrame(stationrows).to_csv(D/'station_phase_residuals.csv',index=False);pd.DataFrame(dayrows).to_csv(D/'holdout_day_residuals.csv',index=False);pd.concat(profiles).to_csv(D/'all_profiles.csv',index=False);pd.DataFrame(raystats).to_csv(D/'ray_coverage.csv',index=False);dump(D/'ray_consistency.json',raychecks)
    # Source waveform/epoch audit for the actual windows inspected in this turn.
    rows=json.loads((D/'review/window_index.json').read_text());metadata=[];cache={};metadata_sources={}
    for row in rows:
        net,sta,*_=row['station'].split('.');path=R/f'inputs/extended/responses/{net}_{sta}.xml'
        if path not in cache:cache[path]=read_inventory(str(path));metadata_sources[str(path.relative_to(R))]=c.sha(path)
        for ident in row['trace_ids']:
            nn,ss,ll,cc=ident.split('.');inv=cache[path].select(network=nn,station=ss,location=ll,channel=cc,time=UTCDateTime(row['time']));ch=[ch for n in inv for s in n for ch in s]
            metadata.append(dict(review_id=row['review_id'],trace_id=ident,metadata=str(path.relative_to(R)),epoch_matches=len(ch),sample_rate=ch[0].sample_rate if ch else None,azimuth=ch[0].azimuth if ch else None,dip=ch[0].dip if ch else None,response_present=bool(ch and ch[0].response),epoch_start=str(ch[0].start_date) if ch else None))
    pd.DataFrame(metadata).to_csv(D/'review/metadata.csv',index=False)
    # Exact station/phase and calendar support, including zero-training pairs.
    ap=ass.join(picks,on='pick_index');ap=ap[ap.event_index.isin(pd.read_csv(V/'event_roles.csv').event_index)]
    ap['role']=np.where(ap.time<'2025-01-01','training_pool','holdout');ap.groupby(['role','trace_id','phase']).size().rename('arrivals').to_csv(D/'pool_support.csv')
    missing=pd.DataFrame(stationrows);missing=missing[(missing.trial=='three_zero_delays_base')&(missing.training_count==0)]
    missing.to_csv(D/'missing_training_pairs.csv',index=False)
    overlap=max(len(set(pd.read_csv(D/f'training_cap{cap}.csv').event_index)&set(hold.event_index)) for cap in [5,8]);assert overlap==0
    dump(D/'verification.json',dict(holdout_hash_unchanged=True,fit_event_overlap_with_holdout=overlap,all_plan_input_hashes_verified=True,completed_trials=len(statistics),accepted_models=summary['accepted'],raw_review_windows=len(rows),reviewed_channel_epochs=len(metadata),metadata_sources=metadata_sources,ray_checks=raychecks,notes='Phase identity is not validated by residual consistency. Model sensitivity is not a statistical confidence interval. Background downloads/picks are excluded from this frozen experiment.'))
    print(pd.DataFrame(statistics).to_string(index=False));print('Ray checks',raychecks)

if __name__=='__main__':main()
