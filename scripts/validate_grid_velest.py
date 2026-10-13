"""Precision and internal checks on own grid-derived calibration; no reference events."""
import json
import numpy as np
import pandas as pd
import run_grid_velest as g
c=g.c;v=g.v;ROOT=g.ROOT;OUT=g.BASE/'merged4';WORK=ROOT/'tmp/grid_calibration/merged4'

def main():
    c.OUT=OUT;c.WORK=WORK;s=json.loads((OUT/'summary.json').read_text());region=s['lowest_converged_phase_RMS_region'];ids=pd.read_csv(OUT/'selected_initial_events.csv').event_index.tolist();records=[]
    seed=WORK/(region+'_prelocation');model=(seed/'input.mod').read_text();sta=(seed/'input.sta').read_text();cnv=(seed/'input.cnv').read_text()
    try:
        for name,fixed,correction,it in [('prelocation',True,False,14),('round1',False,False,7),('round2',False,True,7)]+[(f'convergence{i}',False,True,7) for i in range(1,4)]:
            w,loc,r=c.run('precision32_'+name,model,sta,cnv,ids,bits=32,fixed=fixed,corrections=correction,iterations=it);records.append(r)
            model=(w/'velout.mod').read_text();sta=c.normalize_stations((w/'output.sta').read_text());cnv=(w/'output.cnv').read_text()
        target=ROOT/s['regions'][region]['validated_workdir'];ref=pd.read_csv(OUT/(region+'_convergence3_locations.csv'))
        change=c.compare(ref,loc);dv=float(abs(v.model_table(target/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max());ds=g.station_change(c.normalize_stations((target/'output.sta').read_text()),sta)
        passed=change['max_horizontal_m']<=100 and change['max_depth_km']<=.1 and dv<=.05 and ds<=.02
        result=dict(runs=records,precision_difference=change,velocity_difference_km_s=dv,station_delay_difference_s=ds,precision_gate_passed=bool(passed))
    except Exception as exc:result=dict(runs=records,error=repr(exc),precision_gate_passed=False)
    # Distinguish accumulated path divergence from local arithmetic sensitivity.
    target=ROOT/s['regions'][region]['validated_workdir'];local={}
    for bits in [32,64]:
        w,loc,rr=c.run('local_precision'+str(bits),(target/'velout.mod').read_text(),c.normalize_stations((target/'output.sta').read_text()),(target/'output.cnv').read_text(),ids,bits=bits,corrections=True)
        local[bits]=(w,loc,rr)
    result['same_converged_start_precision']=c.compare(local[32][1],local[64][1])
    result['same_converged_start_velocity_difference_km_s']=float(abs(v.model_table(local[32][0]/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(local[64][0]/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max())
    result.update(accepted_scientific_catalog=False,limitation='Full 32/64-bit calibration paths compared from identical inputs; a separate common-converged-start test isolates local sensitivity. Numerical agreement is not independent location accuracy. Held-out refitting, manual phase review and external absolute-location validation have not been repeated for this grid-based run.')
    result['sources']={str(p.relative_to(ROOT)):c.sha(p) for p in [OUT/'independent_calibrated.mod',OUT/'independent_calibrated.sta',OUT/'filtered_events.csv']}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
