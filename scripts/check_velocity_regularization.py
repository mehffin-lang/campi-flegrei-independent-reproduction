"""One controlled velocity-damping trial on the same observed calibration set.

Use layer damping 100 (already used for the deepest unresolved layer) in all
velocity layers. This is a disclosed regularization departure, not a recovered
Tan setting or a search for agreement with a published result. No observation,
phase, event-selection or acceptance criterion is changed.
"""
import json,os
os.environ.update(CF_GRID_BASE='data/eida_continuation/calibration',CF_GRID_WORK='tmp/eida_continuation',CF_OBSERVATIONS='data/eida_continuation')
import numpy as np,pandas as pd
import run_grid_velest as g

def main():
    out=g.BASE.parent/'velocity_regularization';out.mkdir(exist_ok=True);g.c.OUT=out;g.c.WORK=g.WORKROOT/'velocity_regularization';g.c.WORK.mkdir(exist_ok=True)
    ids=pd.read_csv(g.BASE/'merged4/selected_initial_events.csv').event_index.tolist();records={}
    for region in ['Pozzuoli_Solfatara','caldera']:
        source=g.WORKROOT/'merged4'/(region+'_prelocation');lines=(source/'input.mod').read_text().splitlines()
        for i,line in enumerate(lines):
            if len(line.split())==3:
                vp,dep,_=map(float,line.split());lines[i]=f'{vp:5.2f}     {dep:7.2f}  {100.:7.3f}'
        model='\n'.join(lines)+'\n';sta=(source/'input.sta').read_text();cnv=(source/'input.cnv').read_text();r=dict(runs=[],accepted=False)
        records[region]=r
        w,loc,rr=g.c.run(region+'_prelocation',model,sta,cnv,ids,fixed=True,iterations=14);r['runs'].append(rr)
        w,loc,rr=g.c.run(region+'_round1',model,sta,(w/'output.cnv').read_text(),ids);r['runs'].append(rr)
        for stage in ['round2','convergence1','convergence2','convergence3']:
            before=w;previous=loc
            w,loc,rr=g.c.run(region+'_'+stage,(w/'velout.mod').read_text(),g.c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),ids,corrections=True)
            rr['location_change']=g.c.compare(previous,loc)
            rr['max_velocity_change_km_s']=float(abs(g.v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-g.v.model_table(before/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()).max())
            rr['max_station_delay_change_s']=g.station_change(g.c.normalize_stations((w/'output.sta').read_text()),g.c.normalize_stations((before/'output.sta').read_text()))
            r['runs'].append(rr)
        m=g.v.model_table(w/'velout.mod');bulk=m.Vp_km_s**2-4*m.Vs_km_s**2/3
        r.update(bulk_over_density_km2_s2=bulk.tolist(),positive_bulk=bool(bulk.gt(0).all()),
            local_change_gate=bool(rr['location_change']['max_horizontal_m']<=100 and rr['location_change']['max_depth_km']<=.1 and rr['max_velocity_change_km_s']<=.05 and rr['max_station_delay_change_s']<=.02),model=m.to_dict('records'))
        (out/'summary.json').write_text(json.dumps(dict(method=__doc__,events=len(ids),regions=records,scientifically_accepted=False),indent=2)+'\n');print(region,r,flush=True)
if __name__=='__main__':main()
