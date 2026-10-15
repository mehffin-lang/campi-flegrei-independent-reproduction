"""Plots from saved own fits/residuals; diagnostic curves never paper panels."""
import json
from pathlib import Path
import numpy as np,pandas as pd
import publication_plots as p
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from pyproj import Transformer
ROOT=p.ROOT;D=ROOT/'data/availability_extension'
CURRENT=json.loads((D/'current_analysis.json').read_text()) if (D/'current_analysis.json').exists() else dict(catalog='data/availability_extension/catalog',profile='data/availability_extension/velocity_canonical',locations='locations_canonical')
V=ROOT/CURRENT['profile']
def main():
    p.theme();p.RECORD.clear();s=json.loads((V/'summary.json').read_text());m=pd.read_csv(V/'sensitivity_profiles.csv');initial=pd.read_csv(V/'initialization.csv')
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for fld,init,color in [('Vp_km_s','vp_km_s','black'),('Vs_km_s','vs_km_s','#0072b2')]:
        for trial,g in m.groupby('trial'):
            axes[0].step(np.r_[g[fld],g[fld].iloc[-1]],np.r_[g.layer_top_km,8],where='pre',color=color,lw=1.5 if trial=='base' else .5,alpha=1 if trial=='base' else .35,label=f'{fld[:2]} base fit' if trial=='base' else None)
        axes[0].step(np.r_[initial[init],initial[init].iloc[-1]],np.r_[initial.depth_top_km_bsl,8],where='pre',color=color,ls='--',lw=1,label=f'{fld[:2]} initialization')
    axes[0].set(xlabel='Velocity (km/s)',ylabel='Depth below sea level (km)',ylim=(8,-.5),title='Own fits and sensitivity envelope');axes[0].legend(fontsize=7)
    names=list(s['runs']);x=np.arange(len(names));a=[];b=[]
    for name in names:
        r=s['runs'][name];a.append(r['holdout']['initialization']['residual_rms_s']);b.append(r['holdout']['fitted']['residual_rms_s'])
    axes[1].plot(x,a,'o--',color='.5',label='Initialization, relocated holdout');axes[1].plot(x,b,'s-',color='#d55e00',label='Fitted, relocated holdout');axes[1].set(xticks=x,xticklabels=[n.replace('_',' ') for n in names],ylabel='Unweighted phase RMS (s)',title=f'2025 holdout: {s["holdout_events"]} events');axes[1].tick_params(axis='x',rotation=65);axes[1].legend(fontsize=7)
    u=pd.read_csv(D/'precision/updates.csv')
    for bits,marker in [(32,'s'),(64,'o')]:
        g=u[u.bits.eq(bits)];axes[2].plot(g.iteration,g.dz_km,marker=marker,label=str(bits)+' bit')
    axes[2].axhline(0,c='.7',lw=.5);axes[2].set(xlabel='Prelocation iteration',ylabel='Proposed depth update (km)',title='Event 1065: ray crossover');axes[2].legend(fontsize=8)
    fig.suptitle('Reproduction diagnostic · no accepted velocity model',fontsize=11)
    inputs=[str((V/n).relative_to(ROOT)) for n in ['sensitivity_profiles.csv','initialization.csv','summary.json']]+[str((D/'precision/updates.csv').relative_to(ROOT))]
    p.save(fig,'observational_velocity_diagnostic',inputs,'diagnostic','Software-validation diagnostic, after supplement only. Initial velocities explicitly dashed; empirical residuals and fitted velocities from own arrivals. Sensitivity envelope is not a confidence interval.',png=True)
    C=ROOT/CURRENT['catalog'];L=C/CURRENT['locations']
    coverage=json.loads((C/'processed_coverage_union.json').read_text());stations={}
    from availability_extension import union
    for row in coverage:stations.setdefault('.'.join(row['channel'].split('.')[:2]),[]).extend(row['intervals'])
    fig,ax=plt.subplots(figsize=(9,7),layout='constrained');names=sorted(stations)
    for i,station in enumerate(names):
        spans=np.asarray(union(stations[station]))/86400
        segments=np.stack([np.column_stack([spans[:,0],np.full(len(spans),i)]),np.column_stack([spans[:,1],np.full(len(spans),i)])],axis=1)
        ax.add_collection(LineCollection(segments,linewidths=2,colors='#2166ac',capstyle='butt'));ax.plot(spans[:,0],np.full(len(spans),i),'|',ms=3,mew=.5,color='#2166ac')
    ax.set(yticks=range(len(names)),yticklabels=names,xlabel='UTC; actual processed sample intervals',title='S1 · Continuous observations; large gaps remain');ax.invert_yaxis();ax.grid(axis='x',alpha=.25)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,7]));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'));ax.set_xlim(mdates.date2num(pd.Timestamp('2022-01-21')),mdates.date2num(pd.Timestamp('2025-03-21')))
    a=json.loads((C/'analysis_summary.json').read_text());fig.supxlabel(f'{a["files"]:,} files · {len(names)} stations · {a["processed_channel_hours"]:,.3f} channel-hours\nEvent-selected snippets excluded. Ticks mark starts, not duration.',fontsize=9)
    p.save(fig,'coverage_availability_extension',[str((C/'processed_coverage_union.json').relative_to(ROOT)),str((C/'analysis_summary.json').relative_to(ROOT))],'S1','Actual processed intervals, merged within each station for display. Blue timeline; fixed study dates and half-year ticks. No pending request counted as data.',png=True)
    if (L/'filtered_events.csv').exists():
        e=pd.read_csv(L/'filtered_events.csv');proj=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True);e['x_km'],e['y_km']=proj.transform(e.longitude.to_numpy(),e.latitude.to_numpy());panels=L/'panels';panels.mkdir(exist_ok=True);e.to_csv(panels/'velest.csv',index=False)
        import grid_publication_panels as gp
        old=p.save
        def save(fig,name,inputs,panel,note='',**kwargs):return old(fig,'figure_S6_availability_extension',inputs,panel,note+' New observational-fit trial; failed holdout validation, not accepted.',png=True)
        p.save=save;gp.generate(p,extension=True,base_override=str(L.relative_to(ROOT))+'/');p.save=old
    (D/'plot_inventory.json').write_text(json.dumps(p.RECORD,indent=2)+'\n')
if __name__=='__main__':main()
