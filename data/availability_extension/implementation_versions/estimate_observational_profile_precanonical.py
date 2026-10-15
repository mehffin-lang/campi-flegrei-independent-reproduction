"""Independent VELEST profile with calendar-separated validation and sensitivity.

Only own phase associations, arrival observations and station metadata enter.
The Tramelli (2021) Table 1 profile is an initialization, not an observation.
Layer tops are fixed: -0.5, 0.5, 1, 3 km below sea level; the last is a halfspace.
Both P and S velocities float independently (initial Vp/Vs=1.78). No imposed
published final velocity, earthquake location or station correction is used.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil
import numpy as np
import pandas as pd
import calibration_chain as c
import run_velest as v
ROOT=c.ROOT;D=ROOT/'data/availability_extension/velocity_existing';W=ROOT/'tmp/availability_extension/velocity_existing'
base_controls=v.controls
STEP=.2
def controls(n,station_corrections=False,location_only=False,iterations=7):
    lines=base_controls(n,station_corrections,location_only,iterations).splitlines()
    lines[0]='Own observations; alternative initialization; calendar holdout'
    lines[4]=f'100.0 0 0.0 0.10 {STEP} 0'
    # Generic guide: regularize poorly resolved hypocentres; smaller steps cross
    # layer boundaries more cautiously. Gates below are not relaxed.
    lines[6]='0.01 0.10 0.10 1.0 0.10'
    return '\n'.join(lines)+'\n'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def station_delta(a,b):
    f=lambda text:np.array([[float(l[34:39]),float(l[41:46])] for l in text.splitlines()[1:] if l[:4].strip()])
    return float(abs(f(a)-f(b)).max())
def main():
    global STEP,D,W
    ap=argparse.ArgumentParser();ap.add_argument('--observations',default='data/eida_continuation');ap.add_argument('--selection',default='data/eida_continuation/calibration/merged4');ap.add_argument('--output',default='data/availability_extension/velocity_existing');args=ap.parse_args()
    D=ROOT/args.output;W=ROOT/'tmp/availability_extension'/D.name;D.mkdir(parents=True,exist_ok=True);W.mkdir(parents=True,exist_ok=True);c.OUT=D;c.WORK=W;v.controls=controls
    O=ROOT/args.observations;Q=ROOT/args.selection
    ev=pd.read_csv(Q/'selected_initial_events.csv').sort_values('time');p=pd.read_csv(O/'picks.csv');a=pd.read_csv(O/'associations.csv');stations=pd.read_csv(O/'stations.csv').sort_values('id')
    train_all=ev[ev.time<'2025-01-01'];hold=ev[ev.time>='2025-01-01'];assert len(hold)>0 and len(train_all)>0
    balanced=[]
    for _,g in train_all.groupby(train_all.time.str[:10]):
        balanced.extend(g.iloc[np.unique(np.linspace(0,len(g)-1,min(20,len(g))).round().astype(int))].event_index)
    train=train_all[train_all.event_index.isin(balanced)]
    ep=p.iloc[a[a.event_index.isin(train.event_index)].pick_index.to_numpy(int)]
    reference=ep[ep.phase=='P'].groupby('trace_id').size().idxmax()
    used=set(p.iloc[a[a.event_index.isin(ev.event_index)].pick_index.to_numpy(int)].trace_id);stations=stations[stations.id.isin(used)]
    aliases={s:f'S{i:03d}' for i,s in enumerate(stations.id)};order=[s for s in stations.id if s!=reference]+[reference];icc={s:i+1 for i,s in enumerate(order)}
    sta=['(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)']
    for r in stations.to_dict('records'):sta.append(f'{aliases[r["id"]]:4s}{r["latitude"]:7.4f}N {r["longitude"]:8.4f}E {round(-r["z(km)"]*1000):4d} 1 {icc[r["id"]]:3d} {0.:5.2f}  {0.:5.2f}')
    sta='\n'.join(sta)+'\n\n';stations.assign(alias=stations.id.map(aliases),icc=stations.id.map(icc)).to_csv(D/'station_aliases.csv',index=False)
    ev.assign(role=np.where(ev.event_index.isin(hold.event_index),'2025 holdout',np.where(ev.event_index.isin(train.event_index),'balanced training','unused in balanced fit; full-selection sensitivity'))).to_csv(D/'event_roles.csv',index=False)
    profile=pd.read_csv(O/'alternative_starting_profile.csv').iloc[:4].copy();profile.loc[0,'depth_top_km_bsl']=-.5
    profile.to_csv(D/'initialization.csv',index=False)
    result=dict(accepted=False,interpretation='Provisional independently fitted 1D models; no exact starting-model reproduction.',specification=__doc__,training_events=len(train),holdout_events=len(hold),all_eligible_training_events=len(train_all),reference_station=reference,holdout='All eligible events during 2025; no held-out arrival enters a velocity/station-correction inversion. Held-out locations and origin times are nuisance fits, so residual improvement is conditional, not absolute location accuracy.',selection='Reuse own causal >=4P, >=2S, >10 phases, azimuth gap <180 degree calibration candidates. Balance training to at most 20 evenly spaced chronological events per UTC day; compare against all training candidates. This cap is an explicit exploratory weighting choice, not Tan selection.',settings=dict(layer_tops_km=profile.depth_top_km_bsl.tolist(),last_layer='halfspace; 10-km layer omitted because calibration events are shallower',initial_ratio=1.78,layer_damping=10.,othet=.01,xythet=.1,zthet=.1,vthet=1.,stathet=.1,max_depth_step_km=.2,max_velocity_step_km_s=.1,P_weight=1.,S_weight=.5,pick_class=0,minimum_depth_km=0.,free_surface_km=-.5,station_elevations='metres above sea level, converted from own StationXML metadata',no_low_velocity_layers=True),inputs={str(f.relative_to(ROOT)):c.sha(f) for f in [Q/'selected_initial_events.csv',O/'picks.csv',O/'associations.csv',O/'stations.csv',O/'alternative_starting_profile.csv']},runs={})
    dump(D/'summary.json',result)
    fits={};configs=[('base',1.,train,64,.2),('slow',.9,train,64,.2),('fast',1.1,train,64,.2),('precision32',1.,train,32,.2),('all_training',1.,train_all,64,.2),('smaller_step',1.,train,64,.1)]
    for name,factor,subset,bits,step in configs:
        STEP=step;ids=subset.event_index.tolist();cnv=v.cnv(subset,p,a,aliases)
        lines=['Tramelli 2021 initialization scaled '+str(factor)+'; fitted independently']
        for fld in ['vp_km_s','vs_km_s']:
            lines.append('4');lines.extend(f'{r[fld]*factor:5.2f}     {r["depth_top_km_bsl"]:7.2f}  {10.:7.3f}' for r in profile.to_dict('records'))
        model='\n'.join(lines)+'\n';initial=model;current_sta=sta
        rec=dict(bits=bits,initial_velocity_factor=factor,events=len(ids),max_depth_step_km=step,runs=[],accepted=False);result['runs'][name]=rec
        try:
            w,loc,rr=c.run(name+'_prelocation',model,sta,cnv,ids,bits=bits,fixed=True,iterations=21);rec['runs'].append(rr)
            cnv=(w/'output.cnv').read_text()
            for stage in ['velocity_only','station_joint','convergence1','convergence2','convergence3']:
                prev=loc;prev_model=model;prev_sta=current_sta
                w,loc,rr=c.run(name+'_'+stage,model,current_sta,cnv,ids,bits=bits,corrections=stage!='velocity_only',iterations=14)
                model=(w/'velout.mod').read_text();current_sta=c.normalize_stations((w/'output.sta').read_text());cnv=(w/'output.cnv').read_text()
                rr.update(location_change=c.compare(prev,loc),station_change_s=station_delta(prev_sta,current_sta),max_velocity_change_km_s=float(abs(v.model_table(w/'input.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max()))
                rec['runs'].append(rr);dump(D/'summary.json',result)
            m=v.model_table(w/'velout.mod');bulk=m.Vp_km_s**2-4*m.Vs_km_s**2/3
            last=rec['runs'][-1];rec['positive_bulk_modulus']=bool((bulk>0).all());rec['last_change_gate']=bool(last['location_change']['max_horizontal_m']<=100 and last['location_change']['max_depth_km']<=.1 and last['max_velocity_change_km_s']<=.05 and last['station_change_s']<=.02)
            rec['profile']=str((D/(name+'_profile.csv')).relative_to(ROOT));m.to_csv(D/(name+'_profile.csv'),index=False);(D/(name+'_fitted.mod')).write_text(model);(D/(name+'_fitted.sta')).write_text(current_sta);loc.to_csv(D/(name+'_training_locations.csv'),index=False)
            rec['holdout']={};hcnv=v.cnv(hold,p,a,aliases)
            for tag,mod,st in [('initialization',initial,sta),('fitted',model,current_sta)]:
                hw,hl,hr=c.run(name+'_holdout_'+tag,mod,st,hcnv,hold.event_index.tolist(),bits=64,corrections=True,fixed=True,iterations=35)
                rec['holdout'][tag]=hr
                np.savetxt(D/(name+'_holdout_'+tag+'_residuals_s.csv'),np.loadtxt(hw/'residuals.txt',ndmin=2)[:,1],header='residual_s',comments='')
            rec['holdout_improvement_s']=rec['holdout']['initialization']['residual_rms_s']-rec['holdout']['fitted']['residual_rms_s'];rec['holdout_improved']=rec['holdout_improvement_s']>0
            fits[name]=dict(model=m,locations=loc,holdout=pd.read_csv(D/(name+'_holdout_fitted_locations.csv')))
        except Exception as e:rec['error']=repr(e)
        dump(D/'summary.json',result)
    comparisons={}
    if 'base' in fits:
        for name,fit in fits.items():
            if name=='base':continue
            comparisons[name]=dict(holdout_location_difference=c.compare(fits['base']['holdout'],fit['holdout']),max_velocity_difference_km_s=float(abs(fits['base']['model'][['Vp_km_s','Vs_km_s']].to_numpy()-fit['model'][['Vp_km_s','Vs_km_s']].to_numpy()).max()))
        ens=pd.concat([v['model'].assign(trial=k) for k,v in fits.items()]);ens.to_csv(D/'sensitivity_profiles.csv',index=False)
        # Spread is a sensitivity envelope, not a posterior confidence interval.
        spread=ens.groupby('layer_top_km')[['Vp_km_s','Vs_km_s']].agg(['min','max','std']);spread.to_csv(D/'profile_sensitivity_envelope.csv')
        result['preferred_provisional_model']='base_fitted.mod';result['comparisons']=comparisons
        result['accepted']=bool(result['runs']['base'].get('last_change_gate') and result['runs']['base'].get('positive_bulk_modulus') and result['runs']['base'].get('holdout_improved') and all(q['holdout_location_difference']['max_depth_km']<=.1 and q['holdout_location_difference']['max_horizontal_m']<=100 and q['max_velocity_difference_km_s']<=.05 for q in comparisons.values()) and len(fits)==len(configs))
    result['limitations']='Internal stability gates do not validate phase identities or absolute depths. Auto-picked observations remain unreviewed. Sparse stations/dates and no RAN; alternative initialization. Ensemble range is conditional model uncertainty; no calibrated statistical confidence interval.'
    result['code_sha256']=c.sha(Path(__file__));dump(D/'summary.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['runs','inputs']},indent=2),flush=True)
if __name__=='__main__':main()
