"""Plot saved observational outputs; no published pixels or figure data as input."""
from pathlib import Path
import io
import json
import zipfile
import os
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parents[1]/'tmp/matplotlib')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import shapefile
from continue_context import PROJ

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/continuation'
F=ROOT/'figures'
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})


def coast(ax):
    with zipfile.ZipFile(ROOT/'inputs/continuation/coastline.zip') as z:
        names=set(z.namelist())
        for ext in ['shp','shx','dbf']: assert 'ne_10m_coastline.'+ext in names
        reader=shapefile.Reader(**{ext:io.BytesIO(z.read('ne_10m_coastline.'+ext)) for ext in ['shp','shx','dbf']})
        for shape in reader.iterShapes(bbox=[13.9,40.65,14.4,41.]):
            p=np.asarray(shape.points)
            for part,end in zip(shape.parts,list(shape.parts[1:])+[len(p)]):
                a=p[part:end];x,y=PROJ.transform(a[:,0],a[:,1]);ax.plot(x,y,color='.45',lw=.6,zorder=1)


def spatial(ax,cat,title):
    coast(ax)
    sc=ax.scatter(cat.x_km,cat.y_km,c=cat.depth_km,s=np.where(cat.Md.notna(),np.clip(10**(.5*(cat.Md.fillna(0)-1)),1,100),1),cmap='viridis_r',vmin=0,vmax=6,alpha=.65,rasterized=True,zorder=2)
    large=cat[cat.Md>=4]
    ax.scatter(large.x_km,large.y_km,marker='*',s=75,color='crimson',edgecolor='white',linewidth=.4,zorder=3,label=r'$M_d\geq4$')
    ax.set(xlim=(-9,9),ylim=(-6,7),xlabel='Easting from reference (km)',ylabel='Northing from reference (km)',title=title)
    ax.set_aspect('equal')
    return sc


def main():
    F.mkdir(exist_ok=True)
    for name in ['figure_S6_pilot.pdf','figure_S8_pilot.pdf']:(F/name).unlink(missing_ok=True)
    c=pd.read_csv(D/'figure_1A.csv')
    fig,ax=plt.subplots(figsize=(7,4.8),layout='constrained')
    sc=spatial(ax,c,'1A · Routine-catalog data, 2005–20 March 2025')
    ax.legend(loc='upper right');fig.colorbar(sc,ax=ax,label='Depth below sea level (km)')
    fig.savefig(F/'figure_1A_routine.pdf');plt.close(fig)

    lev=pd.read_csv(D/'historical_leveling.csv');g=pd.read_csv(D/'rite_gnss.csv')
    t=pd.to_datetime(g.time,utc=True,format='ISO8601')
    y=g.leveling_datum_m.copy();y.loc[t.diff()>pd.Timedelta(days=7)]=np.nan
    fig,axes=plt.subplots(1,2,figsize=(10,3.3),gridspec_kw={'width_ratios':[1.6,1]},layout='constrained')
    axes[0].plot(pd.to_datetime(lev.date),lev.elevation_m,'o-',ms=1.5,lw=.7,color='.35',label='Published leveling observations')
    for ax in axes:
        ax.plot(t,y,color='#176b9a',lw=.6,label='RITE daily GNSS observations')
        ax.fill_between(t,y-g.up_sigma_m,y+g.up_sigma_m,color='#176b9a',alpha=.25,lw=0)
        ax.axvspan(pd.Timestamp('2024-01-01'),pd.Timestamp('2025-03-21'),color='#e1a63b',alpha=.18)
        ax.set(ylabel='Vertical deformation, leveling datum (m)');ax.grid(alpha=.2)
    axes[0].set(title='1B · Historical displacement and extension',xlim=(pd.Timestamp('1905-01-01'),pd.Timestamp('2025-03-21')))
    axes[0].legend(fontsize=7,loc='upper left')
    axes[1].set(title='Daily observations through 20 March 2025',xlim=(pd.Timestamp('2000-01-01'),pd.Timestamp('2025-03-21')),ylim=(g.leveling_datum_m.min()-.12,g.leveling_datum_m.max()+.18))
    axes[1].text(.03,.95,'Shading: extension beyond 2023',transform=axes[1].transAxes,va='top',fontsize=7)
    fig.savefig(F/'figure_1B_displacement.pdf');plt.close(fig)

    c=pd.read_csv(D/'figure_1C.csv');t=pd.to_datetime(c.month+'-01')
    fig,ax=plt.subplots(figsize=(8,3.6),layout='constrained')
    ax.axvspan(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21'),color='#eee2c9',label='Study interval')
    ax.bar(t,c.events,width=c.bin_days,align='edge',color='#777777',label='All routine events/month')
    ax.set(xlabel='Year',ylabel='Monthly event count',title='1C · Routine-catalog seismicity',xlim=(t.min(),pd.Timestamp('2025-03-31')))
    cum=pd.read_csv(D/'figure_1C_cumulative.csv');twin=ax.twinx();twin.step(pd.to_datetime(cum.time,utc=True,format='ISO8601'),cum.cumulative,where='post',color='#ba3c39',lw=1.5);twin.set_ylabel(r'Cumulative events with $M_d>0.2$',color='#ba3c39')
    large=cum[cum.Md>=4];twin.scatter(pd.to_datetime(large.time,utc=True,format='ISO8601'),large.cumulative,marker='x',color='crimson',s=25,zorder=5)
    ax.text(.02,.95,'March 2025 includes days 1–20 only',transform=ax.transAxes,va='top',fontsize=8)
    fig.savefig(F/'figure_1C_routine.pdf');plt.close(fig)

    c=pd.read_csv(D/'figure_S5.csv')
    fig=plt.figure(figsize=(9,7),layout='constrained');grid=fig.add_gridspec(2,2,width_ratios=[1.5,1],height_ratios=[1.5,1])
    a=fig.add_subplot(grid[0,0]);b=fig.add_subplot(grid[0,1]);d=fig.add_subplot(grid[1,0]);key=fig.add_subplot(grid[1,1]);key.axis('off')
    sc=spatial(a,c,'S5 · Routine-catalog locations')
    b.scatter(c.depth_km,c.y_km,s=2,c=c.depth_km,cmap='viridis_r',vmin=0,vmax=6,alpha=.65,rasterized=True)
    b.set(xlabel='Depth (km)',ylabel='Northing (km)',xlim=(0,7),ylim=(-6,7))
    d.scatter(c.x_km,c.depth_km,s=2,c=c.depth_km,cmap='viridis_r',vmin=0,vmax=6,alpha=.65,rasterized=True)
    d.set(xlabel='Easting (km)',ylabel='Depth (km)',xlim=(-9,9),ylim=(7,0))
    key.text(0,.9,f'{len(c):,} located routine events\n21 Jan 2022–20 Mar 2025\nSnapshot retrieved 12 Oct 2026\n\nExternal routine catalog;\nnot independent detections.\nDepth relative to sea level.',va='top',linespacing=1.5)
    fig.colorbar(sc,ax=key,orientation='horizontal',label='Depth (km)',fraction=.18)
    fig.savefig(F/'figure_S5_routine.pdf');plt.close(fig)

    # S6 is specifically the pre-double-difference, VELEST-filtered catalog.
    # A limited independently inverted subset is a valid partial counterpart.
    if (D/'velest_summary.json').exists() and json.loads((D/'velest_summary.json').read_text()).get('completed') and (D/'velest_filtered.csv').exists():
        v=pd.read_csv(D/'velest_filtered.csv')
        if len(v):
            v['x_km'],v['y_km']=PROJ.transform(v.longitude.to_numpy(),v.latitude.to_numpy())
            v.to_csv(D/'figure_S6.csv',index=False)
            fig=plt.figure(figsize=(9,7),layout='constrained');grid=fig.add_gridspec(2,2)
            a=fig.add_subplot(grid[0,0]);b=fig.add_subplot(grid[0,1]);d=fig.add_subplot(grid[1,0]);key=fig.add_subplot(grid[1,1]);key.axis('off')
            coast(a);sc=a.scatter(v.x_km,v.y_km,c=v.depth_km,s=22,cmap='viridis_r',vmin=0,vmax=6)
            xlim=(min(-9,v.x_km.min()-.3),max(9,v.x_km.max()+.3));ylim=(min(-6,v.y_km.min()-.3),max(7,v.y_km.max()+.3));zlim=(min(0,v.depth_km.min()-.2),max(8,v.depth_km.max()+.3))
            a.set(xlabel='Easting (km)',ylabel='Northing (km)',xlim=xlim,ylim=ylim,aspect='equal',title='S6 · Independent VELEST pilot')
            b.scatter(v.depth_km,v.y_km,c=v.depth_km,s=22,cmap='viridis_r',vmin=0,vmax=6);b.set(xlabel='Depth below sea level (km)',ylabel='Northing (km)',xlim=zlim,ylim=ylim)
            d.scatter(v.x_km,v.depth_km,c=v.depth_km,s=22,cmap='viridis_r',vmin=0,vmax=6);d.set(xlabel='Easting (km)',ylabel='Depth below sea level (km)',xlim=xlim,ylim=zlim[::-1])
            key.text(0,.95,f'{len(v)} events passing final filters\n≥6 picks; RMS ≤0.25 s; gap ≤300°\n\nPartial: limited retrieved intervals,\nalternative association model,\nphases not manually reviewed.\nNo TomoDD relocation.\n\nMarker size is uniform;\nno final magnitude is implied.',va='top',linespacing=1.5,fontsize=9)
            fig.colorbar(sc,ax=key,orientation='horizontal',label='Depth (km)',fraction=.18,extend='both')
            fig.savefig(F/'figure_S6_pilot.pdf');plt.close(fig)

    if (D/'figure_S8A.csv').exists() and len(pd.read_csv(D/'magnitudes.csv')):
        v=pd.read_csv(D/'figure_S8A.csv');hist=pd.read_csv(D/'figure_S8B.csv') if (D/'figure_S8B.csv').exists() else pd.DataFrame()
        fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
        if len(v):
            axes[0].scatter(v.Md,v.ML,s=30,color='#176b9a')
            lo=min(v.Md.min(),v.ML.min())-.1;hi=max(v.Md.max(),v.ML.max())+.1
            axes[0].plot([lo,hi],[lo,hi],color='.7',lw=.8)
        axes[0].set(xlabel='Routine duration magnitude Md',ylabel='Independent provisional ML',title=f'S8A · {len(v)} calibrated matches')
        axes[0].text(.02,.97,'Md is a calibration prior;\nthis is not independent validation.',transform=axes[0].transAxes,va='top',fontsize=8)
        if len(hist):
            axes[1].bar(hist.ML_bin,hist['count'],width=.09,color='#176b9a',label='0.1-unit bins')
            axes[1].step(hist.ML_bin,hist.cumulative,where='mid',color='#b25231',label='Cumulative')
            axes[1].set_yscale('log')
        axes[1].set(xlabel='Independent provisional ML',ylabel='Events',title='S8B · Limited-sample distribution');axes[1].legend(fontsize=8)
        fig.suptitle('Partial pilot: initial locations; incomplete magnitude sample. No full-period Mc or b claim.',fontsize=9)
        fig.savefig(F/'figure_S8_pilot.pdf');plt.close(fig)

    # Compact corresponding original panels in one figure for the manuscript
    # and side-by-side comparison; every artist reads the saved CSV outputs.
    cat=pd.read_csv(D/'figure_1A.csv');counts=pd.read_csv(D/'figure_1C.csv')
    fig=plt.figure(figsize=(11,6),layout='constrained');grid=fig.add_gridspec(2,2,width_ratios=[1,1.3])
    a=fig.add_subplot(grid[:,0]);b=fig.add_subplot(grid[0,1]);cax=fig.add_subplot(grid[1,1])
    sc=spatial(a,cat,'A · Routine-catalog locations');fig.colorbar(sc,ax=a,orientation='horizontal',fraction=.08,label='Depth (km)')
    b.plot(pd.to_datetime(lev.date),lev.elevation_m,'o-',ms=1.3,lw=.7,color='.35',label='Leveling')
    b.plot(pd.to_datetime(g.time,utc=True,format='ISO8601'),y,lw=.7,color='#176b9a',label='Daily GNSS')
    b.axvspan(pd.Timestamp('2024-01-01'),pd.Timestamp('2025-03-21'),color='#e1a63b',alpha=.2)
    b.set(ylabel='Vertical deformation (m)',title='B · Displacement, extended through March 2025');b.legend(fontsize=7,ncol=2)
    ct=pd.to_datetime(counts.month+'-01');cax.bar(ct,counts.events,width=counts.bin_days,align='edge',color='.5');cax.axvspan(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21'),color='#eee2c9',alpha=.5)
    twin=cax.twinx();twin.step(pd.to_datetime(cum.time,utc=True,format='ISO8601'),cum.cumulative,where='post',color='#ba3c39',lw=1.2);twin.set_ylabel(r'Cumulative $M_d>0.2$',color='#ba3c39')
    twin.scatter(pd.to_datetime(large.time,utc=True,format='ISO8601'),large.cumulative,marker='x',color='crimson',s=20,zorder=5)
    cax.set(ylabel='Events/month',title='C · Routine-catalog seismicity',xlabel='Year')
    fig.savefig(F/'figure_1_combined.pdf');plt.close(fig)

    coverage_file=D/'processed_coverage_union.json'
    if coverage_file.exists():
        cov=json.loads(coverage_file.read_text());by_station={}
        for row in cov:by_station.setdefault('.'.join(row['channel'].split('.')[:2]),[]).extend(row['intervals'])
        fig,ax=plt.subplots(figsize=(9,6),layout='constrained')
        for i,(station,spans) in enumerate(sorted(by_station.items())):
            for start,end in spans:
                a=mdates.date2num(pd.Timestamp(start,unit='s',tz='UTC'));b=mdates.date2num(pd.Timestamp(end,unit='s',tz='UTC'))
                ax.plot([a,b],[i,i],color='#176b9a',lw=2)
            ax.plot([],[],label=station)
        ax.set_yticks(range(len(by_station)),sorted(by_station),fontsize=7);ax.xaxis_date();ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.set(xlim=(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21')),title='S1 · Actual processed intervals; gaps are not filled',xlabel='UTC date')
        fig.savefig(F/'continuation_coverage.pdf');plt.close(fig)

    stations=pd.read_csv(ROOT/'inputs/models/stations.csv').rename(columns={'Unnamed: 0':'id'})
    stations['x_km'],stations['y_km']=PROJ.transform(stations.longitude.to_numpy(),stations.latitude.to_numpy())
    stations.to_csv(D/'figure_S2.csv',index=False)
    fig,ax=plt.subplots(figsize=(8,6),layout='constrained');coast(ax)
    for network,group in stations.groupby(stations.id.str.split('.').str[0]):
        ax.scatter(group.x_km,group.y_km,marker='^',s=24,label=network)
        for row in group.itertuples():ax.annotate(row.id.split('.')[1],(row.x_km,row.y_km),xytext=(3,3),textcoords='offset points',fontsize=5)
    ax.set(xlabel='Easting (km)',ylabel='Northing (km)',title=f'S2 · Released metadata: {len(stations)} station identifiers',aspect='equal');ax.legend()
    fig.savefig(F/'continuation_stations.pdf');plt.close(fig)


if __name__=='__main__': main()
