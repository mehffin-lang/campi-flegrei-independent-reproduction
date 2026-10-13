"""S-P checks against the own fitted 1-D model, with own station delays."""
from pathlib import Path
import os,json
os.environ.update(OPENBLAS_NUM_THREADS='1',NUMBA_CACHE_DIR=str(Path(__file__).resolve().parents[1]/'tmp/numba'))
import numpy as np
import pandas as pd
from gamma.seismic_ops import initialize_eikonal,calc_time
import run_velest as v
ROOT=v.ROOT;B=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration')/'merged4';OUT=B/'location_checks'

def main():
    OUT.mkdir(exist_ok=True);events=pd.read_csv(B/'panels/relocated.csv').set_index('event_index');pairs=pd.read_csv(B/'panels/sp_measurements.csv');sta=pd.read_csv(B/'station_aliases.csv').set_index('id')
    model=v.model_table(B/'independent_calibrated.mod');z=[];vp=[];vs=[]
    for i,r in model.iterrows():
        end=float(model.layer_top_km.iloc[i+1]-.00001) if i+1<len(model) else 20.
        z.extend([r.layer_top_km,end]);vp.extend([r.Vp_km_s]*2);vs.extend([r.Vs_km_s]*2)
    cfg=dict(vel=dict(z=z,p=vp,s=vs),h=.1,xlim=[-30,30],ylim=[-30,30],zlim=[-.5,20]);eik=initialize_eikonal(cfg)
    corrections={r[:4]:(float(r[34:39]),float(r[41:46])) for r in (B/'independent_calibrated.sta').read_text().splitlines()[1:] if r[:4].strip()}
    rows=[]
    for r in pairs.itertuples():
        e=events.loc[r.event_index];s=sta.loc[r.station];loc=np.array([[e.x_km,e.y_km,e.depth_km,0.]])
        station=np.tile([s['x(km)'],s['y(km)'],s['z(km)']],(2,1));tt=calc_time(loc,station,np.array(['p','s']),eikonal=eik).ravel();pdelay,sdelay=corrections[s.alias];calculated=tt[1]-tt[0]+sdelay-pdelay
        rows.append(dict(event_index=r.event_index,station=r.station,depth_km=e.depth_km,observed_sp_s=r.sp_s,calculated_sp_s=float(calculated),sp_residual_s=float(r.sp_s-calculated),p_delay_s=pdelay,s_delay_s=sdelay,p_source=r.p_source,s_source=r.s_source))
    data=pd.DataFrame(rows);data.to_csv(OUT/'sp_consistency.csv',index=False)
    deep=data[data.depth_km>3].groupby('event_index').agg(depth_km=('depth_km','first'),stations=('station','nunique'),min_observed_sp_s=('observed_sp_s','min'),median_absolute_sp_residual_s=('sp_residual_s',lambda x:x.abs().median()),max_absolute_sp_residual_s=('sp_residual_s',lambda x:x.abs().max()))
    deep.to_csv(OUT/'deep_event_review.csv')
    summary=dict(pairs=len(data),events=data.event_index.nunique(),positive_observed_sp=bool(data.observed_sp_s.gt(0).all()),sp_rms_s=float(np.sqrt(np.mean(data.sp_residual_s**2))),deep_events_tested=len(deep),
        method='0.1 km eikonal approximation to own piecewise-constant VELEST profile plus own station delay difference, evaluated at provisional TomoDD locations. Observations are original independently picked S-P differences. Not a fixed-3D ray retracing or manual phase validation.',
        limitation='Large residuals flag inconsistencies among picks, 1-D travel-time approximation and trial locations. They do not alone prove which phase or depth is wrong. No published depth band is imposed, no event is removed by this diagnostic.')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
