"""Plot saved independent outputs and visually distinct external context."""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
plt.rcParams.update({'font.size':9,'figure.dpi':140,'axes.spines.top':False,'axes.spines.right':False})
def save(name,fig):
    fig.tight_layout()
    for suffix in ['pdf','png']:fig.savefig('figures/'+name+'.'+suffix,bbox_inches='tight')
    plt.close(fig)
def dates(values):return pd.to_datetime(values,utc=True,format='ISO8601')

lev=pd.read_csv('data/extended/historical_leveling.csv')
fig,ax=plt.subplots(figsize=(8,3));ax.plot(dates(lev.date),lev.displacement_from_1905_m,'o-',ms=2,lw=.8,color='#176b6c',label='Leveling / historical estimates')
gnss=pd.read_csv('data/extended/rite_gnss.csv');ax.plot(dates(gnss.time),gnss.displacement_from_1905_m,lw=.5,color='#be6232',label='RITE GNSS; overlap datum alignment')
endpoint=pd.read_csv('data/extended/recent_displacement_endpoint.csv');ax.scatter(dates(endpoint.time),endpoint.displacement_from_1905_m,marker='D',s=22,c='#be6232',label='Dec 2023 written monitoring estimate')
ax.set(xlabel='Year',ylabel='Elevation change from March 1905 (m)',title='Fig. 1B — partial: leveling, GNSS and written monitoring observations')
ax.legend(fontsize=7)
ax.text(.02,.04,'Daily 2020–2023 observations missing; no curve fills that gap.',transform=ax.transAxes,fontsize=8)
save('historical_leveling_partial',fig)

external=pd.read_csv('data/extended/external_routine_catalog.csv');external['time']=dates(external.time)
fig,axs=plt.subplots(1,2,figsize=(10,3.6));located=external.dropna(subset=['latitude','longitude'])
axs[0].scatter(located.longitude,located.latitude,s=2,c='#797979',rasterized=True)
large=located[located.Md>=4];axs[0].scatter(large.longitude,large.latitude,s=55,marker='*',c='#d97706',label='Md ≥ 4');axs[0].legend(fontsize=8)
axs[0].set(xlabel='Longitude (°E)',ylabel='Latitude (°N)',title='Fig. 1A context: external INGV locations');axs[0].set_aspect(1/np.cos(np.deg2rad(40.82)))
count=external[external.Md>.2].set_index('time').resample('MS').size()
axs[1].plot(count.index,count.cumsum(),color='#797979');axs[1].set(xlabel='Year',ylabel='Cumulative external events (Md > 0.2)',title='Fig. 1C context: external INGV counts')
fig.suptitle('EXTERNAL COMPARISON / CONTEXT — not independently detected earthquakes',fontsize=10)
save('historical_catalog_context',fig)
study=located[located.time>=pd.Timestamp('2022-01-21',tz='UTC')]
fig,axs=plt.subplots(1,3,figsize=(10,3.1));axs[0].scatter(study.longitude,study.latitude,s=2,c='#777',rasterized=True);axs[0].set(xlabel='Longitude (°E)',ylabel='Latitude (°N)')
axs[1].scatter(study.latitude,study.depth_km,s=2,c='#777',rasterized=True);axs[1].set(xlabel='Latitude (°N)',ylabel='Depth (km)');axs[1].invert_yaxis()
axs[2].scatter(study.longitude,study.depth_km,s=2,c='#777',rasterized=True);axs[2].set(xlabel='Longitude (°E)',ylabel='Depth (km)');axs[2].invert_yaxis()
fig.suptitle('S5 EXTERNAL COMPARISON — current routine catalog, not independent locations',fontsize=10);save('routine_catalog_context',fig)

coverage=pd.concat([pd.read_csv('data/observations/coverage.csv'),pd.read_csv('data/extended/coverage.csv')],ignore_index=True)
coverage['station']=coverage.channel.str.split('.').str[1]
names=sorted(coverage.station.unique());fig,ax=plt.subplots(figsize=(9,5))
for i,s in enumerate(names):
    g=coverage[coverage.station==s]
    for row in g.itertuples():
        a=mdates.date2num(dates([row.start])[0]);b=mdates.date2num(dates([row.end])[0]);ax.plot([a,b],[i,i],lw=1.2,color='#176b6c');ax.plot([(a+b)/2],[i],marker='|',ms=4,color='#176b6c')
ax.set_yticks(range(len(names)),names);ax.xaxis_date();ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.set(title='S1 — partial: actual retrieved waveform segments',xlabel='Date (UTC); ticks mark windows shorter than plot resolution');ax.tick_params(axis='y',labelsize=7)
save('coverage_partial',fig)

stations=pd.read_csv('data/observations/stations.csv');verified=pd.read_csv('data/extended/stations.csv').drop_duplicates('id')
fig,ax=plt.subplots(figsize=(7,5));ax.scatter(stations.longitude,stations.latitude,s=18,c='#b4b4b4',label='Released study metadata')
ax.scatter(verified.longitude,verified.latitude,s=28,marker='^',c='#176b6c',label='Retrieved response metadata')
for r in verified.itertuples():ax.annotate(r.id.split('.')[1],(r.longitude,r.latitude),fontsize=5,xytext=(2,2),textcoords='offset points')
ax.set(xlabel='Longitude (°E)',ylabel='Latitude (°N)',title='S2 — partial: station metadata, membership not fully reconciled');ax.set_aspect(1/np.cos(np.deg2rad(40.82)));ax.legend(fontsize=8);save('stations_partial',fig)

ev=pd.read_csv('data/extended/initial_events.csv');quality=pd.read_csv('data/extended/location_quality.csv')
fig,axs=plt.subplots(1,2,figsize=(9,3.5));points=axs[0].scatter(ev.longitude,ev.latitude,c=ev['z(km)'],cmap='viridis',s=30)
fig.colorbar(points,ax=axs[0],label='Provisional depth (km)',pad=.02)
axs[0].set(xlabel='Longitude (°E)',ylabel='Latitude (°N)',title='Provisional GaMMA locations');axs[0].set_aspect(1/np.cos(np.deg2rad(40.82)))
axs[1].scatter(quality.azimuthal_gap_deg,quality.rms_s,c='#176b6c');axs[1].axvline(180,color='#777',ls=':');axs[1].axhline(.25,color='#777',ls=':');axs[1].set(xlabel='Azimuthal gap (degrees)',ylabel='Travel-time RMS (s)',title='Independent quality assessment')
fig.suptitle('Diagnostic only — alternative starting profile; no VELEST or TomoDD relocation',fontsize=10);save('association_diagnostic',fig)

profiles=pd.read_csv('data/extended/background_averages.csv');fig,ax=plt.subplots(figsize=(5,4))
for name,g in profiles.groupby('region'):
    g=g[g.depth_km.between(0,7)];ax.plot(g.vp_km_s,g.depth_km,label=name+' Vp');ax.plot(g.vs_km_s,g.depth_km,'--',label=name+' Vs')
ax.invert_yaxis();ax.set(xlabel='Velocity (km/s)',ylabel='Depth below sea level (km)',title='Calculated external-background averages');ax.legend(fontsize=8);save('background_profiles',fig)
