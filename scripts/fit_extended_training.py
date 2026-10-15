"""Refit reviewed pre-2025 additions, then separately evaluate frozen 2025 data.

Fit stage never opens holdout observations. All three registered families and
six sensitivities finish and are hashed before validation can start. No model
selection or arrival changes are permitted during validation.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
import calibration_chain as c
import run_velest as v
import test_velocity_parameterizations as t
from estimate_observational_profile import canonical_cnv,station_delta
from extend_velocity_training import R,D,C,sha,dump

F=D/'fits';W=R/'tmp/velocity_holdout_review/training_extension_20261015/fits'
OLD=R/'data/velocity_holdout_review'

def setup():
    F.mkdir(exist_ok=True);W.mkdir(parents=True,exist_ok=True)
    c.OUT=F;c.WORK=W;t.D=F;t.W=W;v.controls=t.controls

def prepare():
    plan=json.loads((D/'fit_preregistration.json').read_text())
    new=pd.read_csv(D/'qc/accepted_events.csv');p=pd.read_csv(D/'qc/picks.csv');a=pd.read_csv(D/'qc/associations.csv')
    assert len(new) and (new.time<'2025-01-01').all() and (p.time<'2025-01-01').all()
    aliases=pd.read_csv(OLD/'station_aliases.csv');alias=dict(zip(aliases.id,aliases.alias))
    op=pd.read_csv(C/'picks.csv');oa=pd.read_csv(C/'associations.csv')
    # Eliminate all 2025 rows, then explicitly remap positional pick indices.
    op=op[op.time<'2025-01-01'];mapping={idx:i for i,idx in enumerate(op.index)}
    oa=oa[oa.pick_index.isin(mapping)].copy();oa['pick_index']=oa.pick_index.map(mapping)
    op=op.reset_index(drop=True);new['event_index']=new.event_index+100000
    assert not set(new.event_index)&set(oa.event_index)
    a['event_index']=a.event_index+100000;a['pick_index']=a.pick_index+len(op)
    allp=pd.concat([op,p],ignore_index=True);alla=pd.concat([oa,a],ignore_index=True)
    for cap in [5,8]:
        previous=pd.read_csv(OLD/f'training_cap{cap}.csv');events=pd.concat([previous,new],ignore_index=True).sort_values('time')
        assert canonical_cnv(previous,allp,alla,alias)==(OLD/f'training_cap{cap}.cnv').read_text(),'Previous training arrivals changed'
        assert (events.time<'2025-01-01').all();events.to_csv(F/f'training_cap{cap}.csv',index=False)
        cnv=canonical_cnv(events,allp,alla,alias);(F/f'training_cap{cap}.cnv').write_text(cnv)
    plan.update(added_events=len(new),inputs={str(f.relative_to(R)):sha(f) for f in [D/'qc/accepted_events.csv',D/'qc/picks.csv',D/'qc/associations.csv',D/'qc/reviewed_arrivals.csv',*list(F.glob('training_cap*'))]})
    dump(F/'plan.json',plan)

def fit():
    plan=json.loads((F/'plan.json').read_text())
    for path,digest in plan['inputs'].items():assert sha(R/path)==digest
    summary=dict(accepted=False,plan_sha256=sha(F/'plan.json'),runs={})
    if (F/'training_summary.json').exists():summary=json.loads((F/'training_summary.json').read_text());assert summary['plan_sha256']==sha(F/'plan.json')
    sta=(R/'tmp/availability_extension/velocity_december/base_prelocation/input.sta').read_text()
    for family,cfg in plan['families'].items():
        for variant,factor,cap,damp,bits in plan['variants']:
            name=family+'_'+variant
            if summary['runs'].get(name,{}).get('finished'):continue
            t.SETTINGS['velocity_damping']=damp
            sub=pd.read_csv(F/f'training_cap{cap}.csv');ids=sub.event_index.tolist();cnv=(F/f'training_cap{cap}.cnv').read_text()
            lines=['Alternative initialization; independently reviewed pre-2025 observations']
            for phase_factor in [1.,1/plan['initial_ratio']]:
                lines.append(str(len(cfg['tops'])));lines += [f'{speed*factor*phase_factor:5.2f}     {depth:7.2f}  {plan["layer_damping"]:7.3f}' for speed,depth in zip(cfg['vp'],cfg['tops'])]
            model='\n'.join(lines)+'\n';stations=sta
            (F/(name+'_initial.mod')).write_text(model)
            rec=dict(family=family,variant=variant,training_events=len(ids),bits=bits,runs=[],finished=False);summary['runs'][name]=rec
            try:
                w,loc,r=c.run(name+'_prelocation',model,stations,cnv,ids,bits=bits,fixed=True,iterations=21);rec['runs'].append(r);cnv=(w/'output.cnv').read_text();t.paired(w,sub).to_csv(F/(name+'_initial_training_residuals.csv'),index=False)
                for stage in ['velocity_only','joint1','joint2','joint3','joint4','joint5']:
                    previous=loc;ps=stations
                    w,loc,r=c.run(name+'_'+stage,model,stations,cnv,ids,bits=bits,corrections=cfg['station_fit'] and stage!='velocity_only',iterations=14)
                    model=(w/'velout.mod').read_text();stations=c.normalize_stations((w/'output.sta').read_text());cnv=(w/'output.cnv').read_text()
                    r.update(location_change=c.compare(previous,loc),station_change_s=station_delta(ps,stations),max_velocity_change_km_s=float(abs(v.model_table(w/'input.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max()))
                    rec['runs'].append(r)
                    if stage=='joint3':checkpoint=(loc.copy(),model,stations)
                profile=v.model_table(w/'velout.mod');profile.to_csv(F/(name+'_profile.csv'),index=False)
                (F/(name+'_fitted.mod')).write_text(model);(F/(name+'_fitted.sta')).write_text(stations)
                last=rec['runs'][-1];rec['last_change_gate']=bool(last['location_change']['max_horizontal_m']<=100 and last['location_change']['max_depth_km']<=.1 and last['max_velocity_change_km_s']<=.05 and last['station_change_s']<=.02)
                rec['positive_bulk_modulus']=bool((profile.Vp_km_s**2-4*profile.Vs_km_s**2/3>0).all());rec['monotonic']=bool(np.all(np.diff(profile.Vp_km_s)>=0) and np.all(np.diff(profile.Vs_km_s)>=0))
                pm=v.model_table(W/(name+'_joint3')/'velout.mod')
                rec['extra_iteration_changes']=dict(locations=c.compare(checkpoint[0],loc),station_s=station_delta(checkpoint[2],stations),velocity_km_s=float(abs(pm[['Vp_km_s','Vs_km_s']].to_numpy()-profile[['Vp_km_s','Vs_km_s']].to_numpy()).max()))
                t.paired(w,sub).to_csv(F/(name+'_training_residuals.csv'),index=False)
                if variant=='base':rec['training_rays']=t.ray_rows(w,sub,cfg['tops'])
                rec['finished']=True
            except Exception as exc:rec['error']=repr(exc)
            dump(F/'training_summary.json',summary);print(name,'finished',rec['finished'],rec.get('error',''),flush=True)
    # Freeze every training result before opening any 2025 arrivals.
    dump(F/'training_frozen.json',{str(p.relative_to(R)):sha(p) for p in sorted(F.glob('*')) if p.is_file() and p.name!='training_frozen.json'})

def validate():
    for p,h in json.loads((F/'training_frozen.json').read_text()).items():assert sha(R/p)==h,p
    plan=json.loads((F/'plan.json').read_text());summary=json.loads((F/'training_summary.json').read_text())
    lock=json.loads((D/'holdout_lock.json').read_text());assert sha(R/lock['file'])==lock['sha256'];hcnv=(R/lock['file']).read_text()
    hold=pd.read_csv(OLD/'holdout_events.csv');assert (hold.time>='2025-01-01').all()
    sta=(R/'tmp/availability_extension/velocity_december/base_prelocation/input.sta').read_text()
    common=json.loads((R/'data/availability_extension/velocity_december/summary.json').read_text())['runs']['base']['holdout']['initialization']['residual_rms_s']
    summary['common_initial_rms_s']=common;summary['comparisons']={}
    for name,rec in summary['runs'].items():
        if not rec['finished']:continue
        cfg=plan['families'][rec['family']];t.SETTINGS['velocity_damping']=1
        rec['holdout']={}
        for tag,mod,st in [('initialization',(F/(name+'_initial.mod')).read_text(),sta),('fitted',(F/(name+'_fitted.mod')).read_text(),(F/(name+'_fitted.sta')).read_text())]:
            w,loc,r=c.run(name+'_holdout_'+tag,mod,st,hcnv,hold.event_index.tolist(),corrections=cfg['station_fit'],fixed=True,iterations=35);rec['holdout'][tag]=r;t.paired(w,hold).to_csv(F/(name+'_holdout_'+tag+'_residuals.csv'),index=False)
            ew,el,er=c.run(name+'_holdout_'+tag+'_extra',mod,st,(w/'output.cnv').read_text(),hold.event_index.tolist(),corrections=cfg['station_fit'],fixed=True,iterations=35);er['location_change']=c.compare(loc,el);rec['holdout'][tag+'_extra']=er
        rec['holdout_improves']=rec['holdout']['fitted']['residual_rms_s']<rec['holdout']['initialization']['residual_rms_s'] and rec['holdout']['fitted']['residual_rms_s']<common
        rec['holdout_location_converged']=all(rec['holdout'][tag+'_extra']['location_change']['max_horizontal_m']<=100 and rec['holdout'][tag+'_extra']['location_change']['max_depth_km']<=.1 for tag in ['initialization','fitted'])
        dump(F/'validation_summary.json',summary)
    for family in plan['families']:
        base=family+'_base';checks={};rec=summary['runs'][base]
        for variant,*_ in plan['variants'][1:]:
            name=family+'_'+variant
            if not summary['runs'][name].get('finished'):checks[name]=dict(error='Incomplete fit');continue
            locs=[pd.read_csv(F/(n+'_holdout_fitted_locations.csv')) for n in [base,name]];models=[pd.read_csv(F/(n+'_profile.csv')) for n in [base,name]]
            checks[name]=dict(locations=c.compare(*locs),velocity_km_s=float(abs(models[0][['Vp_km_s','Vs_km_s']].to_numpy()-models[1][['Vp_km_s','Vs_km_s']].to_numpy()).max()),station_s=station_delta((F/(base+'_fitted.sta')).read_text(),(F/(name+'_fitted.sta')).read_text()))
        summary['comparisons'][family]=checks
        extra=rec.get('extra_iteration_changes',{})
        rec['accepted']=bool(rec.get('holdout_improves') and rec.get('last_change_gate') and rec.get('positive_bulk_modulus') and rec.get('monotonic') and rec.get('holdout_location_converged') and all('error' not in q and q['locations']['max_horizontal_m']<=100 and q['locations']['max_depth_km']<=.1 and q['velocity_km_s']<=.05 and q['station_s']<=.02 for q in checks.values()) and extra['locations']['max_horizontal_m']<=100 and extra['locations']['max_depth_km']<=.1 and extra['velocity_km_s']<=.05 and extra['station_s']<=.02)
    summary['accepted']=any(r.get('accepted',False) for r in summary['runs'].values());dump(F/'validation_summary.json',summary)
    assert sha(R/lock['file'])==lock['sha256'];print('Accepted:',summary['accepted'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','fit','validate']);a=ap.parse_args();setup();globals()[a.stage]()
