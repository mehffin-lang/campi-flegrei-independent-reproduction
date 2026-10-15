"""Three predeclared observational 1D experiments; frozen 2025 validation.

Uses only the December checkpoint's own picks/associations, station metadata,
and published alternative initialization. No new waveform or author result
enters this experiment. Holdout membership, arrivals, weights and gates do not
change. Model families are selected for resolution/identifiability, not by
searching the holdout score. All failures are retained.
"""
import argparse, json, re, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import calibration_chain as c
import run_velest as v
from estimate_observational_profile import canonical_cnv, station_delta
import validate_observational_profile as vr

R=c.ROOT;D=R/'data/velocity_holdout_review';W=R/'tmp/velocity_holdout_review/runs'
C=R/'data/availability_extension/catalog_december';OLD=R/'data/availability_extension/velocity_december'
DEFAULT_CONTROLS=v.controls
SETTINGS={}
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def controls(n,station_corrections=False,location_only=False,iterations=7):
    lines=DEFAULT_CONTROLS(n,station_corrections,location_only,iterations).splitlines()
    lines[0]='Own observations; frozen 2025 holdout; parameterization test'
    lines[4]='100.0 0 0.0 0.10 0.20 0'
    lines[6]=f'0.01 0.10 0.10 {SETTINGS.get("velocity_damping",1.)} 10.0'
    # Native per-ray vertices, in actual observation order. Do not use the
    # generic aggregate ray table: its two-model layer counters are inconsistent.
    lines[9]='1 0 0 0 0 0 1'
    return '\n'.join(lines)+'\n'

def selection(events,picks,assoc,cap):
    chosen=[]
    # Chronological strata within each day and provisional 1 km depth interval.
    # These depths come from this project's association, not a reference catalog.
    for _,g in events.groupby([events.time.str[:10],np.floor(events['z(km)']).astype(int)]):
        chosen.extend(g.iloc[np.unique(np.linspace(0,len(g)-1,min(cap,len(g))).round().astype(int))].event_index)
    # Cover every station/phase available in the training pool, at least 3 events
    # when they exist. Selection uses pre-2025 observations only.
    a=assoc[assoc.event_index.isin(events.event_index)].join(picks,on='pick_index')
    for _,g in sorted(a.groupby(['trace_id','phase']),key=lambda x:len(x[1])):
        ids=g.sort_values(['probability','event_index'],ascending=[False,True]).event_index.drop_duplicates().tolist()
        target=min(3,len(ids));present=sum(i in chosen for i in ids)
        for i in ids:
            if present>=target:break
            if i not in chosen:chosen.append(i);present+=1
    return events[events.event_index.isin(chosen)]

def paired(work,events):
    vr.W=W;rows=vr.residuals(work.name)
    rows['event_index']=rows.event_ordinal.map(dict(enumerate(events.event_index)))
    # Check against input token order, not just cardinality.
    blocks=re.split(r'\n\s*\n',(work/'input.cnv').read_text().strip())
    tokens=[(ei,t[:4],t[4]) for ei,b in enumerate(blocks) for line in b.splitlines()[1:] for t in [line[j:j+12] for j in range(0,len(line),12)] if t.strip()]
    assert list(rows[['event_ordinal','alias','phase']].itertuples(index=False,name=None))==tokens
    return rows

def ray_rows(work,events,tops):
    """Read last-iteration ray vertices and sum geometric length per layer."""
    residual=paired(work,events)
    text=(work/'velout.ray').read_text()
    pattern=r'event\s*=\s*(\d+)\s+station\s+(\S+)\s+num\. raypoints=\s*(\d+)'
    matches=list(re.finditer(pattern,text));assert len(matches)==len(residual),(len(matches),len(residual))
    rows=[]
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        points=np.array([float(z) for z in text[m.end():end].split()]).reshape(-1,3)
        assert len(points)==int(m[3]);r=residual.iloc[i]
        assert int(m[1])==r.event_ordinal+1 and m[2]==r.alias
        lengths=np.zeros(len(tops));head=np.zeros(len(tops))
        for a,b in zip(points[:-1],points[1:]):
            dz=b[2]-a[2];cuts=[0.,1.]
            if abs(dz)>1e-12:cuts+=list((z-a[2])/dz for z in tops[1:] if 0<(z-a[2])/dz<1)
            cuts=sorted(cuts)
            for l,u in zip(cuts[:-1],cuts[1:]):
                depth=(a[2]+dz*(l+u)/2);layer=max(0,min(len(tops)-1,np.searchsorted(tops,depth,side='right')-1))
                length=np.linalg.norm(b-a)*(u-l);lengths[layer]+=length
                if abs(dz)<.015:head[layer]+=length
        for k,length in enumerate(lengths):
            rows.append(dict(event_index=int(r.event_index),alias=r.alias,phase=r.phase,layer_top_km=float(tops[k]),ray_length_km=float(length),horizontal_segment_km=float(head[k]),source_depth_km=float(points[0,2]),deepest_point_km=float(points[:,2].max())))
    pd.DataFrame(rows).to_csv(D/(work.name+'_rays.csv'),index=False)
    return dict(arrivals=len(residual),ray_count=len(matches),vertices_resolution_km=.01,interpretation='Actual native ray vertices rounded to 0.01 km. Layer intersections are independently summed; horizontal segments are not automatically identified as head waves.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--run',action='store_true');args=ap.parse_args()
    D.mkdir(exist_ok=True);W.mkdir(parents=True,exist_ok=True);c.OUT=D;c.WORK=W;v.controls=controls
    events=pd.read_csv(OLD/'event_roles.csv').sort_values('time');p=pd.read_csv(C/'picks.csv');a=pd.read_csv(C/'associations.csv')
    train=events[events.time<'2025-01-01'];hold=events[events.time>='2025-01-01']
    aliases=pd.read_csv(OLD/'station_aliases.csv');alias=dict(zip(aliases.id,aliases.alias))
    sta=(R/'tmp/availability_extension/velocity_december/base_prelocation/input.sta').read_text()
    hcnv=canonical_cnv(hold,p,a,alias)
    oldh=R/'tmp/availability_extension/velocity_december/base_holdout_initialization/input.cnv'
    assert hcnv==oldh.read_text(),'Changed holdout!'
    families={
        'four_regularized':dict(tops=[-.5,.5,1.,3.],vp=[1.7,2.,3.,5.5],station_fit=True),
        'three_regularized':dict(tops=[-.5,1.,3.],vp=[1.8,3.,5.5],station_fit=True),
        'three_zero_delays':dict(tops=[-.5,1.,3.],vp=[1.8,3.,5.5],station_fit=False)}
    variants=[('base',1.,5,1.,64),('slow',.95,5,1.,64),('fast',1.05,5,1.,64),('selection',1.,8,1.,64),('damping',1.,5,10.,64),('precision32',1.,5,1.,32)]
    plan=dict(families=families,variants=variants,holdout_events=len(hold),holdout_arrivals=1065,holdout_sha256=hashlib.sha256(hcnv.encode()).hexdigest(),holdout_baseline_source=str(oldh.relative_to(R)),initial_ratio=1.78,layer_damping=10,station_damping=10,initial_station_corrections_s=0,reference_station='IV.CSOB.',weights=dict(P=1,S=.5),selection='Pre-2025 only; at most five (sensitivity eight) chronologically spaced events per day and 1-km provisional depth bin; supplement rare training station/phase pairs to three events where possible.',rationale='Merge shallow layers with similar initial speeds to reduce tradeoffs; increase station damping to limit unsupported station-specific extrapolation; test zero delays as a restricted alternative. Three predeclared families, no holdout-driven search. Depths and delays are nuisance parameters; this is conditional arrival validation.',iteration_schedule='21 fixed prelocation, 14 velocity-only, then five joint 14-iteration blocks; compare blocks 3 and 5 for extra-iteration sensitivity. Holdout 35 fixed-model iterations then another 35 solely to check nuisance-location convergence.',gates=dict(holdout_rms_improves=True,max_horizontal_m=100,max_depth_km=.1,max_velocity_km_s=.05,max_station_s=.02,positive_bulk_modulus=True,monotonic_velocities=True),inputs={str(f.relative_to(R)):c.sha(f) for f in [C/'picks.csv',C/'associations.csv',C/'stations.csv',OLD/'event_roles.csv',OLD/'station_aliases.csv',oldh,R/'inputs/extended/velest_guide.pdf',Path(__file__)]},holdout_exposure='Prior failure diagnostics were inspected, so this is a previously examined validation set, not a pristine final test set. No holdout arrivals, residuals, or locations fit velocity or delays; all registered families and outcomes are reported.')
    if args.prepare:
        dump(D/'experiment_plan.json',plan);(D/'frozen_holdout.cnv').write_text(hcnv)
        for cap in [5,8]:
            sub=selection(train,p,a,cap);sub.to_csv(D/f'training_cap{cap}.csv',index=False)
            canonical=canonical_cnv(sub,p,a,alias);(D/f'training_cap{cap}.cnv').write_text(canonical)
        aliases.to_csv(D/'station_aliases.csv',index=False);hold.to_csv(D/'holdout_events.csv',index=False)
        print('Prepared frozen experiment; training counts',[(cap,len(pd.read_csv(D/f'training_cap{cap}.csv'))) for cap in [5,8]])
    if not args.run:return
    assert json.loads((D/'experiment_plan.json').read_text())==json.loads(json.dumps(plan)),'Experiment changed after registration'
    summary=dict(accepted=False,plan_sha256=c.sha(D/'experiment_plan.json'),runs={},comparisons={})
    if (D/'summary.json').exists():summary=json.loads((D/'summary.json').read_text());assert summary['plan_sha256']==c.sha(D/'experiment_plan.json')
    # Fixed, common reference score is the original unmodified 2025 evaluation.
    oldsummary=json.loads((OLD/'summary.json').read_text());common=oldsummary['runs']['base']['holdout']['initialization']['residual_rms_s']
    summary['original_holdout_rms_s']=common
    for family,cfg in families.items():
        for variant,factor,cap,damp,bits in variants:
            name=family+'_'+variant
            if name in summary['runs'] and summary['runs'][name].get('finished'):continue
            SETTINGS['velocity_damping']=damp
            sub=pd.read_csv(D/f'training_cap{cap}.csv');ids=sub.event_index.tolist();cnv=(D/f'training_cap{cap}.cnv').read_text()
            model=['Provisional initialization; no author-fitted velocity']
            for phase_factor in [1.,1/1.78]:
                model.append(str(len(cfg['tops'])))
                model += [f'{speed*factor*phase_factor:5.2f}     {depth:7.2f}  {10.:7.3f}' for speed,depth in zip(cfg['vp'],cfg['tops'])]
            model='\n'.join(model)+'\n';initial=model;stations=sta
            rec=dict(family=family,variant=variant,training_events=len(ids),bits=bits,runs=[],accepted=False,finished=False);summary['runs'][name]=rec;dump(D/'summary.json',summary)
            try:
                w,loc,r=c.run(name+'_prelocation',model,stations,cnv,ids,bits=bits,fixed=True,iterations=21);rec['runs'].append(r);cnv=(w/'output.cnv').read_text()
                for stage in ['velocity_only','joint1','joint2','joint3','joint4','joint5']:
                    prev=loc;pm=model;ps=stations
                    w,loc,r=c.run(name+'_'+stage,model,stations,cnv,ids,bits=bits,corrections=cfg['station_fit'] and stage!='velocity_only',iterations=14)
                    model=(w/'velout.mod').read_text();stations=c.normalize_stations((w/'output.sta').read_text());cnv=(w/'output.cnv').read_text()
                    r.update(location_change=c.compare(prev,loc),station_change_s=station_delta(ps,stations),max_velocity_change_km_s=float(abs(v.model_table(w/'input.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max()))
                    rec['runs'].append(r)
                    if stage=='joint3':checkpoint=(loc.copy(),model,stations)
                    dump(D/'summary.json',summary)
                fitted=v.model_table(w/'velout.mod');fitted.to_csv(D/(name+'_profile.csv'),index=False)
                (D/(name+'_fitted.mod')).write_text(model);(D/(name+'_fitted.sta')).write_text(stations)
                last=rec['runs'][-1];rec['last_change_gate']=bool(last['location_change']['max_horizontal_m']<=100 and last['location_change']['max_depth_km']<=.1 and last['max_velocity_change_km_s']<=.05 and last['station_change_s']<=.02)
                rec['positive_bulk_modulus']=bool((fitted.Vp_km_s**2-4*fitted.Vs_km_s**2/3>0).all())
                rec['monotonic']=bool(np.all(np.diff(fitted.Vp_km_s)>=0) and np.all(np.diff(fitted.Vs_km_s)>=0))
                rec['extra_iteration_changes']=dict(locations=c.compare(checkpoint[0],loc),station_s=station_delta(checkpoint[2],stations))
                before=v.model_table(W/(name+'_joint3')/'velout.mod')
                rec['extra_iteration_changes']['velocity_km_s']=float(abs(before[['Vp_km_s','Vs_km_s']].to_numpy()-fitted[['Vp_km_s','Vs_km_s']].to_numpy()).max())
                tr=paired(w,sub);tr.to_csv(D/(name+'_training_residuals.csv'),index=False)
                if variant=='base':rec['training_rays']=ray_rows(w,sub,cfg['tops'])
                rec['holdout']={}
                for tag,mod,st in [('initialization',initial,sta),('fitted',model,stations)]:
                    hw,hl,hr=c.run(name+'_holdout_'+tag,mod,st,hcnv,hold.event_index.tolist(),corrections=cfg['station_fit'],fixed=True,iterations=35)
                    rec['holdout'][tag]=hr;paired(hw,hold).to_csv(D/(name+'_holdout_'+tag+'_residuals.csv'),index=False)
                    # Same extra location iterations for initialization and fit;
                    # the original 35-iteration score remains the primary gate.
                    ew,el,er=c.run(name+'_holdout_'+tag+'_extra',mod,st,(hw/'output.cnv').read_text(),hold.event_index.tolist(),corrections=cfg['station_fit'],fixed=True,iterations=35)
                    er['location_change']=c.compare(hl,el);rec['holdout'][tag+'_extra']=er
                    if variant=='base' and tag=='fitted':rec['holdout_rays']=ray_rows(hw,hold,cfg['tops'])
                rec['holdout_improvement_s']=rec['holdout']['initialization']['residual_rms_s']-rec['holdout']['fitted']['residual_rms_s']
                rec['improves_common_initialization']=rec['holdout']['fitted']['residual_rms_s']<common
                rec['holdout_location_converged']=all(rec['holdout'][tag+'_extra']['location_change']['max_horizontal_m']<=100 and rec['holdout'][tag+'_extra']['location_change']['max_depth_km']<=.1 for tag in ['initialization','fitted'])
                rec['finished']=True
            except Exception as exc:rec['error']=repr(exc)
            dump(D/'summary.json',summary)
        base=family+'_base';checks={}
        if summary['runs'][base].get('finished'):
            for variant,*_ in variants[1:]:
                name=family+'_'+variant
                if not summary['runs'][name].get('finished'):checks[name]=dict(error='Incomplete trial');continue
                lm=[pd.read_csv(D/(n+'_holdout_fitted_locations.csv')) for n in [base,name]]
                vm=[pd.read_csv(D/(n+'_profile.csv')) for n in [base,name]]
                checks[name]=dict(locations=c.compare(*lm),velocity_km_s=float(abs(vm[0][['Vp_km_s','Vs_km_s']].to_numpy()-vm[1][['Vp_km_s','Vs_km_s']].to_numpy()).max()))
            summary['comparisons'][family]=checks
            rec=summary['runs'][base]
            rec['accepted']=bool(rec['holdout_improvement_s']>0 and rec['improves_common_initialization'] and rec['last_change_gate'] and rec['positive_bulk_modulus'] and rec['monotonic'] and rec['holdout_location_converged'] and all('error' not in q and q['locations']['max_horizontal_m']<=100 and q['locations']['max_depth_km']<=.1 and q['velocity_km_s']<=.05 for q in checks.values()) and rec['extra_iteration_changes']['locations']['max_horizontal_m']<=100 and rec['extra_iteration_changes']['locations']['max_depth_km']<=.1 and rec['extra_iteration_changes']['velocity_km_s']<=.05 and rec['extra_iteration_changes']['station_s']<=.02)
        dump(D/'summary.json',summary)
    summary['accepted']=any(r.get('accepted',False) for r in summary['runs'].values());dump(D/'summary.json',summary)
    assert (D/'frozen_holdout.cnv').read_text()==oldh.read_text()
    print('Accepted:',summary['accepted'],flush=True)

if __name__=='__main__':main()
