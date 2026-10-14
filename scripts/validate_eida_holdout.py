"""Refit without every fifth calibration event; evaluate only withheld events.

Uses the independently selected cohort and exactly the published-method pilot
sequence. No reference catalog or paper locations are used. Conditional residual
improvement does not establish absolute location accuracy or regional robustness.
"""
import json,re,os
os.environ.update(CF_GRID_BASE='data/eida_continuation/calibration',CF_GRID_WORK='tmp/eida_continuation',CF_OBSERVATIONS='data/eida_continuation')
import pandas as pd
import run_grid_velest as g

def main():
    c=g.c;root=g.ROOT;b=g.BASE/'merged4';out=b/'heldout';work=g.WORKROOT/'heldout';out.mkdir(exist_ok=True);work.mkdir(exist_ok=True);c.OUT=out;c.WORK=work
    s=json.loads((b/'summary.json').read_text());region=s['lowest_converged_phase_RMS_region'];original=g.WORKROOT/'merged4'/(region+'_prelocation')
    identity_files=[p for p in b.iterdir() if p.is_file() and p.suffix in ['.csv','.mod','.sta','.cnv','.json']]
    identity_files += [root/'scripts'/n for n in ['validate_eida_holdout.py','calibration_chain.py','run_grid_velest.py','run_velest.py']] + [root/'build'/('velest'+str(n)) for n in [32,64]]
    identity_files += [p for p in (g.WORKROOT/'merged4').rglob('*') if p.is_file() and p.name in ['input.mod','input.sta','input.cnv','velest.cmn','output.sta','velout.mod']]
    identity={str(p.relative_to(root)):c.sha(p) for p in identity_files};manifest=out/'execution_manifest.json'
    if manifest.exists():
        saved=json.loads(manifest.read_text())
        if saved['inputs']==identity and all((root/n).exists() and c.sha(root/n)==h for n,h in saved['outputs'].items()):
            print('Reused held-out result after exact input, implementation, binary and output hash checks.');return
    ids=pd.read_csv(b/'selected_initial_events.csv').event_index.tolist();hold=ids[::5];train=[i for i in ids if i not in hold]
    blocks=re.split(r'\n\s*\n',(original/'input.cnv').read_text().strip());assert len(blocks)==len(ids)
    def cnv(selected):return '\n\n'.join(x for i,x in zip(ids,blocks) if i in selected)+'\n\n'
    model=(original/'input.mod').read_text();sta=(original/'input.sta').read_text()
    result=dict(training_events=len(train),heldout_events=len(hold),training_ids=train,heldout_ids=hold,selection='Every fifth chronological candidate, excluded before velocity/station inversion',method=__doc__,runs=[])
    # Retain direct evidence that arithmetic comparisons start identically.
    other=g.WORKROOT/'merged4'/'precision32_prelocation'
    result['precision_initial_setup']={f:dict(identical=(original/f).read_bytes()==(other/f).read_bytes(),sha256=c.sha(original/f)) for f in ['input.mod','input.sta','input.cnv','velest.cmn']}
    result['precision_path_stages']=[]
    for stage in ['prelocation','round1','round2','convergence1','convergence2','convergence3']:
        left=b/(region+'_'+stage+'_locations.csv');right=b/('precision32_'+stage+'_locations.csv')
        if not (left.exists() and right.exists()):
            result['precision_path_stages'].append(dict(stage=stage,error='Missing precision-path output'))
            continue
        comparison=c.compare(pd.read_csv(left),pd.read_csv(right))
        w64=g.WORKROOT/'merged4'/(region+'_'+stage);w32=g.WORKROOT/'merged4'/('precision32_'+stage)
        comparison['max_velocity_difference_km_s']=float(abs(g.v.model_table(w64/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-g.v.model_table(w32/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max())
        comparison['max_station_delay_difference_s']=g.station_change(c.normalize_stations((w64/'output.sta').read_text()),c.normalize_stations((w32/'output.sta').read_text()))
        result['precision_path_stages'].append(dict(stage=stage,**comparison))
    pd.DataFrame(result['precision_path_stages']).to_csv(out/'precision_path_stages.csv',index=False)
    result['common_intermediate_start']=[]
    for stage in ['round1','round2']:
        start=g.WORKROOT/'merged4'/(region+'_'+stage)
        try:
            w,loc,r=c.run('common_start32_'+stage,(start/'input.mod').read_text(),(start/'input.sta').read_text(),(start/'input.cnv').read_text(),ids,bits=32,corrections=stage=='round2')
            reference=pd.read_csv(b/(region+'_'+stage+'_locations.csv'))
            result['common_intermediate_start'].append(dict(stage=stage,comparison=c.compare(reference,loc),run=r))
        except Exception as exc:result['common_intermediate_start'].append(dict(stage=stage,error=repr(exc)))
    try:
        w,loc,r=c.run('train_prelocation',model,sta,cnv(train),train,fixed=True,iterations=14);result['runs'].append(r)
        w,loc,r=c.run('train_round1',model,sta,(w/'output.cnv').read_text(),train);result['runs'].append(r)
        for name in ['round2','convergence1','convergence2','convergence3']:
            w,loc,r=c.run('train_'+name,(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),train,corrections=True);result['runs'].append(r)
        for name,mod,st in [('starting',model,sta),('fitted',(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()))]:
            _,_,r=c.run('heldout_'+name,mod,st,cnv(hold),hold,corrections=True,fixed=True,iterations=21);result[name]=r
        result['residual_improvement_s']=result['starting']['residual_rms_s']-result['fitted']['residual_rms_s']
        result['residual_improved']=result['residual_improvement_s']>0
    except Exception as exc:result['error']=repr(exc)
    result['sources']={str(p.relative_to(root)):c.sha(p) for p in [b/'selected_initial_events.csv',original/'input.mod',original/'input.sta',original/'input.cnv']}
    model_table=g.v.model_table(b/'independent_calibrated.mod')
    bulk=model_table.Vp_km_s**2-4*model_table.Vs_km_s**2/3
    result['isotropic_bulk_modulus_check']=dict(bulk_modulus_over_density_km2_s2=bulk.tolist(),positive=bool((bulk>0).all()),interpretation='Vp^2 - 4 Vs^2/3 must be positive for positive bulk modulus in an isotropic elastic reference. A diagnostic of the own trial model, not a measurement of rock properties.')
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    manifest.write_text(json.dumps(dict(inputs=identity,outputs={str(p.relative_to(root)):c.sha(p) for p in out.iterdir() if p.is_file() and p!=manifest}),indent=2)+'\n')

if __name__=='__main__':main()
