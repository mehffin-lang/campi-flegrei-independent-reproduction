"""Independent grid-derived VELEST experiments, full usable cohort, explicit gates."""
from pathlib import Path
import argparse
import json,hashlib,shutil,os
import numpy as np
import pandas as pd
import calibration_chain as c
import run_velest as v
ROOT=c.ROOT;BASE=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration');OUT=BASE;D=ROOT/os.environ.get('CF_OBSERVATIONS','data/calibration_followup/expanded');WORKROOT=ROOT/os.environ.get('CF_GRID_WORK','tmp/grid_calibration');WORK=WORKROOT/'velest'
c.OUT=OUT;c.WORK=WORK
base_controls=v.controls

def controls(n,station_corrections=False,location_only=False,iterations=7):
    lines=base_controls(n,station_corrections,location_only,iterations).splitlines()
    lines[0]='Independent VELEST; authorized Tan grid regional start; no author fitted results'
    fields=lines[4].split();fields[-1]='0';lines[4]=' '.join(fields) # Guide: avoid low-velocity inversions initially.
    return '\n'.join(lines)+'\n'
v.controls=controls
old_normalize=c.normalize_model
def normalize(text):return old_normalize(text).replace('Independent alternative-profile VELEST fit; not Battaglia/Tan model','Independent fit; Tan-distributed Battaglia-attributed starting grid')
c.normalize_model=normalize

def station_change(a,b):
    def values(t):return np.array([[float(r[34:39]),float(r[41:46])] for r in t.splitlines()[1:] if r[:4].strip()])
    return float(np.max(abs(values(a)-values(b))))

def main():
    global OUT,WORK
    parser=argparse.ArgumentParser();parser.add_argument('--coarse-four',action='store_true');args=parser.parse_args()
    if args.coarse_four:
        OUT=BASE/'merged4';WORK=WORKROOT/'merged4';OUT.mkdir(exist_ok=True);c.OUT=OUT;c.WORK=WORK
    ev=pd.read_csv(D/'initial_events.csv');p=pd.read_csv(D/'picks.csv');a=pd.read_csv(D/'associations.csv');q=pd.read_csv(BASE/'input_quality.csv');s=pd.read_csv(D/'stations.csv')
    ev=ev[ev.event_index.isin(q.loc[q.causal,'event_index'])].sort_values('time');a=a[a.event_index.isin(ev.event_index)]
    selected=ev[ev.event_index.isin(q.loc[q.calibration,'event_index'])];selected.to_csv(OUT/'selected_initial_events.csv',index=False)
    used=set(p.iloc[a.pick_index].trace_id);s=s[s.id.isin(used)].sort_values('id');aliases={ident:f'S{i:03d}' for i,ident in enumerate(s.id)}
    pp=p.iloc[a.loc[a.event_index.isin(selected.event_index),'pick_index']];reference=pp[pp.phase=='P'].groupby('trace_id').size().idxmax()
    order=[x for x in s.id if x!=reference]+[reference];icc={ident:i+1 for i,ident in enumerate(order)}
    sta=['(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)']
    for r in s.to_dict('records'):sta.append(f'{aliases[r["id"]]:4s}{r["latitude"]:7.4f}N {r["longitude"]:8.4f}E {round(-r["z(km)"]*1000):4d} 1 {icc[r["id"]]:3d} {0.:5.2f}  {0.:5.2f}')
    sta='\n'.join(sta)+'\n\n';s.assign(alias=s.id.map(aliases),icc=s.id.map(icc)).to_csv(OUT/'station_aliases.csv',index=False)
    cnv=v.cnv(selected,p,a,aliases);ids=selected.event_index.tolist();profiles=pd.read_csv(BASE/'starting_profiles.csv')
    if args.coarse_four:
        rows=[]
        for region,g in pd.read_csv(BASE/'regional_node_means.csv').groupby('region'):
            for top,bottom in [(-.5,1.),(1.,3.),(3.,5.),(5.,5.)]:
                a0=max(.1,top);sample=np.unique(np.r_[a0,g.loc[g.depth_node_km_bsl.between(a0,bottom),'depth_node_km_bsl'],bottom])
                values=np.array([np.interp(sample,g.depth_node_km_bsl,g[f]) for f in ['vp_km_s','vs_km_s']]);v0=np.trapezoid(values,sample,axis=1)/(bottom-a0) if bottom>a0 else values[:,0]
                rows.append(dict(region=region,layer_top_km=top,Vp_km_s=v0[0],Vs_km_s=v0[1],VpVs=v0[0]/v0[1]))
        profiles=pd.DataFrame(rows);profiles.to_csv(OUT/'starting_profiles.csv',index=False)
    record=dict(status='running',accepted=False,calibration_events=len(selected),whole_catalog_events=len(ev),reference_station=reference,
      regions={},selection=json.loads((BASE/'input_inventory.json').read_text())['selection'],
      corrections=['Grid-derived solid-earth regional profiles, with disclosed coarse layering; previous alternative profile not used.','LOWVELOCLAY=0 per generic guide, instead of previous 1.','Fixed-model prelocation (14 iterations) before two seven-iteration calibration rounds, guide p7.'],
      acceptance='Physical layers; extra seven-iteration change <=100 m in every horizontal/depth location, <=0.05 km/s velocity and <=0.02 s station delays; these are numerical stability gates, not absolute location accuracy. Held-out checks and waveform review are separate.')
    def save():(OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    if args.coarse_four:record['corrections'].append('Merge similar layers to four tops -0.5,1,3,5 km; deepest velocity damping 100 instead of 1, per guide pp8 and appendix: shallow calibration events do not resolve deeper velocities. Not an exact Tan discretization.')
    damping_override=os.environ.get('CF_VELEST_LAYER_DAMPING')
    if damping_override:
        damping_override=float(damping_override);assert damping_override>0
        record['velocity_layer_damping_override']=damping_override
        record['corrections'].append('Uniform velocity-layer damping '+str(damping_override)+' after the unconstrained new-cohort fit produced negative isotropic bulk modulus. One disclosed regularization alternative; no observation, event selection, or numerical gate relaxed. Not Tan\'s documented setting.')
    save();fits={}
    for region,prof in profiles.groupby('region',sort=False):
        r=record['regions'][region]=dict(runs=[],accepted=False);save()
        lines=['Tan-distributed grid regional start; '+region]
        for field in ['Vp_km_s','Vs_km_s']:
            lines.append(str(len(prof)));lines.extend(f'{row[field]:5.2f}     {row["layer_top_km"]:7.2f}  {damping_override if damping_override else 100. if args.coarse_four and row["layer_top_km"]>=5 else 1.:7.3f}' for row in prof.to_dict('records'))
        model='\n'.join(lines)+'\n';(OUT/f'{region}_starting.mod').write_text(model)
        try:
            w,loc,rr=c.run(region+'_prelocation',model,sta,cnv,ids,fixed=True,iterations=14);r['runs'].append(rr)
            w,loc,rr=c.run(region+'_round1',model,sta,(w/'output.cnv').read_text(),ids);r['runs'].append(rr)
            w,loc,rr=c.run(region+'_round2',(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),ids,corrections=True);r['runs'].append(rr)
            fit=(w,loc);fits[region]=fit
            last=w;previous=loc
            for n in range(1,4):
                wn,ln,rr=c.run(region+f'_convergence{n}',(last/'velout.mod').read_text(),c.normalize_stations((last/'output.sta').read_text()),(last/'output.cnv').read_text(),ids,corrections=True)
                delta=c.compare(previous,ln);dv=float(np.max(abs(v.model_table(last/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(wn/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy())))
                ds=station_change(c.normalize_stations((last/'output.sta').read_text()),c.normalize_stations((wn/'output.sta').read_text()))
                rr.update(location_change=delta,max_velocity_change_km_s=dv,max_station_delay_change_s=ds);r['runs'].append(rr)
                r['converged']=bool(delta['max_horizontal_m']<=100 and delta['max_depth_km']<=.1 and dv<=.05 and ds<=.02)
                last,previous=wn,ln;save()
            r['accepted']=False;r['local_change_gate_passed']=r['converged'];r['validated_workdir']=str(last.relative_to(ROOT));r['status']='executed; local-change gate is not scientific acceptance'
            fits[region]=(last,previous)
            physical=v.model_table(last/'velout.mod')
            bulk=physical.Vp_km_s**2-4*physical.Vs_km_s**2/3
            r['bulk_over_density_km2_s2']=bulk.tolist();r['positive_isotropic_bulk_modulus']=bool((bulk>0).all())
        except Exception as exc:r.update(status='failed validation or solver',error=repr(exc))
        save()
    if not fits:
        record.update(status='no physical two-round fit',accepted=False);save();return
    fits={name:fit for name,fit in fits.items() if record['regions'][name].get('positive_isotropic_bulk_modulus',False)}
    if not fits:
        record.update(status='No physically admissible final fit; negative isotropic bulk modulus',accepted=False);save();return
    eligible={name:fit for name,fit in fits.items() if record['regions'][name].get('converged',False)}
    best=min(eligible or fits,key=lambda name:record['regions'][name]['runs'][-1]['residual_rms_s']);w,loc=fits[best]
    record['lowest_converged_phase_RMS_region']=best;record['iteration_stability_passed']=bool(eligible)
    record['accepted']=False
    record['selection_note']=('Lowest phase RMS among converged, physically admissible regional fits.' if eligible else 'No regional fit passes the iteration-stability gate. Lowest phase RMS among physically admissible fits retained only as a provisional calculation.')+' Declared extra iterations included; independent precision and location validation remain separate.'
    record['starting_model_dependence']=c.compare(fits['caldera'][1],fits['Pozzuoli_Solfatara'][1]) if len(fits)==2 else None
    fixed_model=(w/'velout.mod').read_text();fixed_sta=c.normalize_stations((w/'output.sta').read_text())
    (OUT/'independent_calibrated.mod').write_text(fixed_model);(OUT/'independent_calibrated.sta').write_text(fixed_sta)
    for obsolete in ['independent_round2.mod','independent_round2.sta']:(OUT/obsolete).unlink(missing_ok=True)
    record['whole_catalog_runs']=[];text=v.cnv(ev,p,a,aliases);allids=ev.event_index.tolist()
    try:
        for n in range(1,6):
            if n in [4,5]:
                text,allids,reject=v.reject_residuals(w,allids,.4 if n==4 else .3);record.setdefault('rejections',[]).append(reject)
            w,located,rr=c.run(f'whole_catalog_pass{n}',fixed_model,fixed_sta,text,allids,corrections=True,fixed=True);record['whole_catalog_runs'].append(rr);text=(w/'output.cnv').read_text();save()
        located['paper_filter_pass']=(located.num_picks>=6)&(located.rms_s<=.25)&(located.azimuthal_gap_deg<=300)
        located.to_csv(OUT/'located_events.csv',index=False);located[located.paper_filter_pass].to_csv(OUT/'filtered_events.csv',index=False);(OUT/'located_events.cnv').write_text(text)
        record.update(status='executed full usable-cohort grid-derived trial',paper_filter_passing=int(located.paper_filter_pass.sum()))
    except Exception as exc:record.update(status='whole catalog failed',error=repr(exc),accepted=False)
    record['downstream_gate']='No accepted scientific catalog without stable calibration, response/phase checks and relocation validation. Filter passage alone is insufficient.'
    save();print(json.dumps(record,indent=2))
if __name__=='__main__':main()
