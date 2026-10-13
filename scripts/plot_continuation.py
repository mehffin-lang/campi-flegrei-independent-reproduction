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
import routine_plot_style as style

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
                a=p[part:end].copy()
                outside=(a[:,0]<13.9)|(a[:,0]>14.4)|(a[:,1]<40.65)|(a[:,1]>41.)
                a[outside]=np.nan
                x,y=PROJ.transform(a[:,0],a[:,1]);ax.plot(x,y,color='.45',lw=.6,zorder=1)


def historical(ax,lev):
    # Source reconstructions are contextual estimates, never raw surveys.
    styles=[('leveling survey','o','.35','Leveling surveys'),
            ('source-provided estimate','^','#b67720','Source estimates'),
            ('source-provided reconstruction','x','#9b3370','Source reconstruction')]
    for kind,marker,color,label in styles:
        subset=lev[lev.provenance_class==kind]
        ax.plot(pd.to_datetime(subset.date),subset.elevation_m,linestyle='none',marker=marker,
                ms=3.3 if kind!='leveling survey' else 1.8,color=color,label=label)


def combined_figure():
    lev=pd.read_csv(D/'historical_leveling.csv');g=pd.read_csv(D/'rite_gnss.csv')
    t=pd.to_datetime(g.time,utc=True,format='ISO8601');y=g.leveling_datum_m.copy();y.loc[t.diff()>pd.Timedelta(days=7)]=np.nan
    cum=pd.read_csv(D/'figure_1C_cumulative.csv');large=cum[cum.Md>=4]
    # Compact corresponding original panels in one figure for the manuscript
    # and side-by-side comparison; every artist reads the saved CSV outputs.
    cat=pd.read_csv(D/'figure_1A.csv');counts=pd.read_csv(D/'figure_1C.csv')
    fig=plt.figure(figsize=(11.5,6.3),layout='constrained')
    left,right=fig.subfigures(1,2,width_ratios=[1.4,1]);left.set_facecolor('black')
    a=left.subplots();b,cax=right.subplots(2,1)
    sc=style.map_panel(a,cat,'1A',coast,'A · Routine-catalog locations');style.depth_bar(left,a,sc)
    historical(b,lev)
    b.plot(pd.to_datetime(g.time,utc=True,format='ISO8601'),y,lw=.7,color='#176b9a',label='Daily GNSS')
    b.axvspan(pd.Timestamp('2024-01-01'),pd.Timestamp('2025-03-21'),color='#e1a63b',alpha=.2)
    b.set(ylabel='Vertical deformation (m)',title='B · Displacement\nExtended through March 2025');b.legend(fontsize=7,ncol=2)
    ct=pd.to_datetime(counts.month+'-01');cax.bar(ct,counts.events,width=counts.bin_days,align='edge',color='.5');cax.axvspan(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21'),color='#eee2c9',alpha=.5)
    twin=cax.twinx();twin.step(pd.to_datetime(cum.time,utc=True,format='ISO8601'),cum.cumulative,where='post',color='#ba3c39',lw=1.2);twin.set_ylabel(r'Cumulative $M_d>0.2$',color='#ba3c39')
    twin.scatter(pd.to_datetime(large.time,utc=True,format='ISO8601'),large.cumulative,marker='x',color='crimson',s=20,zorder=5)
    cax.set(ylabel='Events/month',title='C · Routine-catalog seismicity',xlabel='Year')
    fig.savefig(F/'figure_1_combined.pdf');plt.close(fig)


def main():
    F.mkdir(exist_ok=True)
    for name in ['figure_S6_pilot.pdf','figure_S8_pilot.pdf']:(F/name).unlink(missing_ok=True)
    style.standalone(ROOT,coast)

    lev=pd.read_csv(D/'historical_leveling.csv');g=pd.read_csv(D/'rite_gnss.csv')
    t=pd.to_datetime(g.time,utc=True,format='ISO8601')
    y=g.leveling_datum_m.copy();y.loc[t.diff()>pd.Timedelta(days=7)]=np.nan
    fig,axes=plt.subplots(1,2,figsize=(10,3.3),gridspec_kw={'width_ratios':[1.6,1]},layout='constrained')
    historical(axes[0],lev)
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

    # S6 is withdrawn. Its unverified-grid plotting recipe remains in Git
    # history; arithmetic experiments cannot reactivate it as a paper result.

    if (D/'figure_S8A.csv').exists() and len(pd.read_csv(D/'magnitudes.csv')):
        v=pd.read_csv(D/'figure_S8A.csv');hist=pd.read_csv(D/'figure_S8B.csv') if (D/'figure_S8B.csv').exists() else pd.DataFrame()
        fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
        if len(v):
            axes[0].scatter(v.Md,v.ML,s=30,color='#176b9a')
            if 'formal_sigma_ML' in v:
                subset=v[v.formal_sigma_ML.notna()]
                axes[0].errorbar(subset.Md,subset.ML,yerr=subset.formal_sigma_ML,fmt='none',color='#176b9a',lw=.6,capsize=2)
            lo=min(v.Md.min(),v.ML.min())-.1;hi=max(v.Md.max(),v.ML.max())+.1
            axes[0].plot([lo,hi],[lo,hi],color='.7',lw=.8)
        axes[0].set(xlabel='Routine duration magnitude Md',ylabel='Independent provisional ML',title=f'S8A · {len(v)} calibrated matches')
        axes[0].text(.02,.97,'Md is a calibration prior;\nthis is not independent validation.',transform=axes[0].transAxes,va='top',fontsize=8)
        if len(hist):
            axes[1].bar(hist.ML_bin,hist['count'],width=.09,color='#176b9a',label='0.1-unit bins')
            axes[1].step(hist.ML_bin,hist.cumulative,where='mid',color='#b25231',label='Cumulative')
            axes[1].set_yscale('log')
        axes[1].set(xlabel='Independent provisional ML',ylabel='Events',title='S8B · Limited-sample distribution');axes[1].legend(fontsize=8)
        statistics=json.loads((D/'magnitude_statistics.json').read_text())
        if statistics.get('b') is not None:
            axes[1].axvline(statistics['Mc'],ls=':',color='.4',lw=.8)
            error=statistics.get('b_sigma');label=(f"S8B · Limited-sample distribution\nConditional b={statistics['b']:.2f}"+(f" ± {error:.2f}" if error is not None else '')+
                f"; {statistics['events_ge_Mc']} events at/above Mc={statistics['Mc']:.1f}\nStandard error excludes selection bias.")
            axes[1].set_title(label,fontsize=8)
        fig.suptitle('Partial pilot: initial locations; incomplete magnitude sample. No full-period Mc or b claim.',fontsize=9)
        fig.savefig(F/'figure_S8_pilot.pdf');plt.close(fig)

    combined_figure()

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

    stations=pd.read_csv(D/'figure_S2.csv').sort_values('id').reset_index(drop=True)
    fig=plt.figure(figsize=(13,8),layout='constrained');grid=fig.add_gridspec(1,2,width_ratios=[1.7,1])
    ax=fig.add_subplot(grid[0]);key=fig.add_subplot(grid[1]);key.axis('off');coast(ax)
    verified=stations.coordinate_status.eq('verified official epoch')
    for keep,color,fill,label in [(verified,'#176b9a',True,'Official coordinates / epochs'),(~verified,'#b67720',False,'Released coordinates; unresolved epoch')]:
        g=stations[keep];ax.scatter(g.x_km,g.y_km,marker='^',s=32,facecolors=color if fill else 'none',edgecolors=color,label=label,zorder=3)
    ax.set(xlabel='Easting from 14.14°E (km)',ylabel='Northing from 40.82°N (km)',xlim=(-10,13),ylim=(-8,9),aspect='equal',
           title='S2 · Audited candidate stations; membership remains partial')
    ax.set_title(ax.get_title(),fontsize=14);ax.set_xlabel(ax.get_xlabel(),fontsize=14);ax.set_ylabel(ax.get_ylabel(),fontsize=14)
    ax.tick_params(labelsize=13);ax.legend(fontsize=12,loc='lower right');fig.canvas.draw()
    # Numbered labels with leader lines and a full identifier key avoid aliases
    # and overlapping station names in the densely instrumented central area.
    placed=[];marker_points=ax.transData.transform(stations[['x_km','y_km']].to_numpy())
    for i,r in stations.iterrows():
        point=ax.transData.transform((r.x_km,r.y_km));target=None
        for radius in [22,34,48,64,82,104,128,156]:
            for angle in np.linspace(0,2*np.pi,32,endpoint=False):
                candidate=point+radius*np.array([np.cos(angle),np.sin(angle)])
                inside=ax.bbox.x0+17<candidate[0]<ax.bbox.x1-17 and ax.bbox.y0+13<candidate[1]<ax.bbox.y1-13
                clear_markers=all(abs(candidate[0]-q[0])>17 or abs(candidate[1]-q[1])>13 for q in marker_points)
                if inside and clear_markers and all(abs(candidate[0]-q[0])>32 or abs(candidate[1]-q[1])>24 for q in placed):
                    target=candidate;break
            if target is not None:break
        placed.append(target);xy=ax.transData.inverted().transform(target)
        ax.annotate(str(i+1),(r.x_km,r.y_km),xytext=xy,fontsize=13,ha='center',va='center',zorder=4,
                    bbox=dict(facecolor='white',edgecolor='none',pad=.2),arrowprops=dict(arrowstyle='-',lw=.4,color='.4'))
        col=i//26;line=i%26
        key.text(col*.51,.98-line*.031,f'{i+1:2d}  {r.id}',family='monospace',fontsize=13,color='#176b9a' if verified.iloc[i] else '#996118',va='top')
    key.text(0,.12,f'{int(verified.sum())} official epoch matches; {int((~verified).sum())} unresolved.\n{len(stations)} identifiers ≠ verified 48 instruments.\nTwo coordinate-coincident pairs are retained.\nSee station_geometry_qa.csv for every entry.',fontsize=11,va='top',linespacing=1.6)
    # Include the full identifier key even when its longest labels extend
    # slightly beyond the constrained-layout axes.
    fig.savefig(F/'continuation_stations.pdf',bbox_inches='tight',pad_inches=.1);plt.close(fig)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--routine-style-only',action='store_true')
    args=parser.parse_args()
    if args.routine_style_only:
        style.standalone(ROOT,coast);combined_figure()
    else:main()
