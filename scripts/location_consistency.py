"""S--P consistency of own provisional associations, not relocated-sector validation."""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'),OMP_NUM_THREADS='2',MPLCONFIGDIR=str(ROOT/'tmp/matplotlib'))
import numpy as np
import pandas as pd
from obspy import UTCDateTime
from gamma.seismic_ops import initialize_eikonal,calc_time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path('data/extended')
picks=pd.read_csv(OUT/'picks.csv');assign=pd.read_csv(OUT/'associations.csv')
events=pd.read_csv(OUT/'initial_events.csv').set_index('event_index')
stations=pd.read_csv(OUT/'stations.csv').set_index('id')
config=json.loads(Path('config/association.json').read_text());eik=initialize_eikonal(config['eikonal'])
paired=assign.merge(picks,left_on='pick_index',right_index=True)
rows=[]
for (event,station),g in paired.groupby(['event_index','trace_id']):
    pp=g[g.phase=='P'];ss=g[g.phase=='S']
    if len(pp)!=1 or len(ss)!=1:continue
    e=events.loc[event];loc=np.array([[e['x(km)'],e['y(km)'],e['z(km)'],0.]])
    xyz=np.repeat(stations.loc[[station],config['dims']].to_numpy(),2,axis=0)
    predicted=calc_time(loc,xyz,np.array(['p','s']),eikonal=eik).ravel()
    observed=float(UTCDateTime(ss.time.iloc[0])-UTCDateTime(pp.time.iloc[0]))
    rows.append(dict(event_index=int(event),station=station,observed_sp_s=observed,calculated_sp_s=float(predicted[1]-predicted[0]),residual_s=observed-float(predicted[1]-predicted[0]),p_file=pp.source.iloc[0],s_file=ss.source.iloc[0]))
table=pd.DataFrame(rows);table.to_csv(OUT/'sp_consistency.csv',index=False)
eligible=paired[(paired.trace_id.str.split('.').str[1]=='CPOZ')&(paired.phase=='P')]
summary=dict(paired_observations=len(rows),nonpositive_sp=int((table.observed_sp_s<=0).sum()),rms_sp_residual_s=float(np.sqrt(np.mean(table.residual_s**2))),associated_cpoz_p_picks=len(eligible),sector_gathers_generated=0,
    scope='Same independently fitted provisional travel-time model: internal consistency only, not independent location accuracy. No author picks or locations used. No associated CPOZ P arrivals exist in this sample.')
(OUT/'location_consistency.json').write_text(json.dumps(summary,indent=2)+'\n')
# Plot the saved table, including failed/large-residual observations.
saved=pd.read_csv(OUT/'sp_consistency.csv');fig,ax=plt.subplots(figsize=(5,4))
ax.scatter(saved.calculated_sp_s,saved.observed_sp_s,c='#176b6c',s=24)
limits=[min(0,saved.observed_sp_s.min(),saved.calculated_sp_s.min()),max(saved.observed_sp_s.max(),saved.calculated_sp_s.max())*1.05]
ax.plot(limits,limits,c='#777',ls=':');ax.set(xlabel='Calculated S–P (s)',ylabel='Observed S–P (s)',xlim=limits,ylim=limits,title='Provisional associations: S–P consistency\nNot the relocated S12 sector validation')
fig.tight_layout();fig.savefig('figures/sp_consistency.pdf');fig.savefig('figures/sp_consistency.png',dpi=160);plt.close(fig)
print(summary)
