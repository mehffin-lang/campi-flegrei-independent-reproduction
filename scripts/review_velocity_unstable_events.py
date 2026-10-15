"""Locate stability failures and display their original network waveforms."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from obspy import read,UTCDateTime
from pyproj import Geod
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'data/velocity_holdout_review';C=R/'data/availability_extension/catalog_december'
def main():
    rows=[];geod=Geod(ellps='WGS84');families=['four_regularized','three_regularized','three_zero_delays']
    for family in families:
        for role,first,last in [('training','joint3','joint5'),('holdout','holdout_fitted','holdout_fitted_extra')]:
            a=pd.read_csv(D/(family+'_base_'+first+'_locations.csv'));b=pd.read_csv(D/(family+'_base_'+last+'_locations.csv'));assert a.event_index.equals(b.event_index)
            horiz=geod.inv(a.longitude.to_numpy(),a.latitude.to_numpy(),b.longitude.to_numpy(),b.latitude.to_numpy())[2]
            for i,r in a.iterrows():rows.append(dict(family=family,role=role,event_index=int(r.event_index),initial_depth_km=float(r.depth_km),later_depth_km=float(b.iloc[i].depth_km),depth_change_km=float(abs(r.depth_km-b.iloc[i].depth_km)),horizontal_change_m=float(horiz[i]),gap_deg=int(r.azimuthal_gap_deg),arrivals=int(r.num_picks),rms_s=float(r.rms_s)))
    q=pd.DataFrame(rows);q.to_csv(D/'iteration_event_stability.csv',index=False)
    targets=q[q.family=='three_zero_delays'].assign(severity=lambda x:np.maximum(x.depth_change_km/.1,x.horizontal_change_m/100)).sort_values('severity',ascending=False).groupby('role').head(2)
    p=pd.read_csv(C/'picks.csv');a=pd.read_csv(C/'associations.csv').join(p,on='pick_index');events=pd.read_csv(C/'selection/selected_initial_events.csv').set_index('event_index');index=[]
    for row in targets.itertuples():
        origin=UTCDateTime(events.loc[row.event_index,'time']);ep=a[a.event_index==row.event_index].sort_values(['trace_id','phase']);stations=ep.trace_id.unique();fig,ax=plt.subplots(figsize=(12,max(5,len(stations)*.44)),layout='constrained')
        files=[];traces=[]
        for j,station in enumerate(stations):
            g=ep[ep.trace_id==station];source=g.iloc[0].source;files.append(source);st=read(str(R/source),starttime=origin-1,endtime=origin+15)
            for tr in st:
                if np.ma.isMaskedArray(tr.data) and np.ma.getmaskarray(tr.data).any():continue
                tr.detrend('linear');tr.filter('bandpass',freqmin=1,freqmax=min(20,.4*tr.stats.sampling_rate),zerophase=True,corners=2)
                tm=tr.times()+float(tr.stats.starttime-origin);scale=max(abs(tr.data).max(),1e-20);traces.append(tr.id)
                ax.plot(tm,tr.data/scale*.35+j,color='black' if tr.stats.channel.endswith('Z') else '#999999',lw=.6,alpha=.8)
            for pick in g.itertuples():
                x=UTCDateTime(pick.time)-origin;ax.plot([x,x],[j-.42,j+.42],color='#0072b2' if pick.phase=='P' else '#d55e00',lw=1);ax.text(x,j+.43,f'{pick.phase} {pick.probability:.2f}',fontsize=6)
        ax.set(yticks=range(len(stations)),yticklabels=stations,xlabel='Seconds from own provisional GaMMA origin; black Z, gray horizontals',xlim=(-1,15))
        ax.set_title(f'Reproduction diagnostic: {row.role} event {row.event_index}\nFurther iterations: {row.horizontal_change_m:.0f} m horizontal, {row.depth_change_km:.2f} km depth; P blue, S orange')
        fig.savefig(D/f'review/event_{row.event_index}.png',dpi=140);plt.close(fig)
        index.append(dict(event_index=row.event_index,role=row.role,origin=str(origin),source_files=files,trace_ids=traces,picks=ep[['pick_index','trace_id','phase','time','probability']].to_dict('records')))
    (D/'review/network_windows.json').write_text(json.dumps(index,indent=2)+'\n')
    print(targets.to_string(index=False))
if __name__=='__main__':main()
