"""Provisional counterparts; every plotted number comes from saved own outputs."""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scipy.stats import gaussian_kde
from pyproj import Transformer
ROOT=None;D='data/grid_calibration/merged4/panels/';U='data/grid_calibration/merged4/uncertainty/'
PROJ=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)

def generate(p,extension=False,base_override=None):
    global ROOT,D,U
    ROOT=p.ROOT
    base=base_override or ('data/coverage_extension/calibration/merged4/' if extension else 'data/grid_calibration/merged4/')
    D=base+'panels/';U=base+'uncertainty/'
    def table(path):return pd.read_csv(ROOT/path)
    def save(fig,name,inputs,panels,note):
        if extension:name=name.replace('_provisional','')+('_local_followup' if base_override else '_extension');note='Separately frozen extended cohort; independent identifiers. '+note
        p.save(fig,name,inputs,panels,note)
    norm=Normalize(0,5,clip=False);cm=p.style.depth_cmap();limits=[]
    def scatter(ax,d,x,y,constant=False):
        if constant:
            ax.scatter(d[x],d[y],s=3,c=d.depth_km,cmap=cm,norm=norm,lw=0,zorder=2)
            return
        known=d.ML.notna() if 'ML' in d else pd.Series(False,index=d.index)
        sizes=p.style.areas(d.loc[known,'ML']) if known.any() else []
        ax.scatter(d.loc[known,x],d.loc[known,y],s=sizes,c=d.loc[known,'depth_km'],cmap=cm,norm=norm,alpha=.8,lw=0,zorder=2)
        if (~known).any():ax.scatter(d.loc[~known,x],d.loc[~known,y],s=8,c=d.loc[~known,'depth_km'],cmap=cm,norm=norm,marker='x',lw=.45,zorder=2)
    def maps(d,title,name,path):
        fig=plt.figure(figsize=(9,8),facecolor='black',layout='constrained');gs=fig.add_gridspec(2,2,width_ratios=[1.7,1],height_ratios=[1.4,1])
        a=fig.add_subplot(gs[0,0]);b=fig.add_subplot(gs[0,1]);c=fig.add_subplot(gs[1,0]);bar=fig.add_subplot(gs[1,1]);bar.axis('off')
        p.coast(a)
        for line in a.lines:line.set_color('white')
        constant=title=='S6'
        scatter(a,d,'x_km','y_km',constant);scatter(b,d,'depth_km','y_km',constant);scatter(c,d,'x_km','depth_km',constant)
        # Keep all locations on the axes; fixed color limits never hide deep points.
        xmin=min(-6.,d.x_km.min()-.2);xmax=max(3.5,d.x_km.max()+.2);ymin=min(-3.5,d.y_km.min()-.2);ymax=max(3.5,d.y_km.max()+.2);zmax=max(5.,d.depth_km.max()+.2);zmin=min(0.,d.depth_km.min()-.1)
        a.set(xlim=(xmin,xmax),ylim=(ymin,ymax),xlabel='Easting (km)',ylabel='Northing (km)',aspect='equal')
        b.set(xlim=(zmin,zmax),ylim=(ymin,ymax),xlabel='Depth (km)');b.xaxis.tick_top();b.xaxis.set_label_position('bottom')
        c.set(xlim=(xmin,xmax),ylim=(zmax,zmin),xlabel='Easting (km)',ylabel='Depth (km)')
        for ax in [a,b,c]:p.style.frame(ax,True);ax.grid(color='white',alpha=.25,lw=.45)
        sm=ScalarMappable(norm=norm,cmap=cm);cb=fig.colorbar(sm,ax=bar,location='left',shrink=.95,extend='both' if d.depth_km.lt(0).any() else 'max' if d.depth_km.gt(5).any() else 'neither',ticks=range(6));cb.ax.invert_yaxis();cb.set_label('Depth (km); magenta >5 km',color='white');cb.ax.tick_params(colors='white');cb.outline.set_edgecolor('.8')
        if not constant:
            for m in [2,3,4]:a.scatter([],[],s=p.style.areas(m),c='.7',label=rf'$M_L={m}$')
            a.scatter([],[],marker='x',s=8,c='.7',label=r'$M_L$ unavailable');a.legend(facecolor='black',edgecolor='none',labelcolor='white',fontsize=7,loc='lower left')
        fig.suptitle(title+f' · {len(d)} events · provisional',color='white',fontsize=11)
        fig.supxlabel('Own locations; sparse exposure, calibration path dependence; coarse coastline, no relief raster.',color='white',fontsize=8)
        size_note='Uniform 3-point-squared symbols for S6; exact printed area unspecified.' if constant else 'Own ML sizes where available; crosses otherwise. Published size formula unspecified: 0.7+3*10**(ML-2) points squared is explicit display assumption.'
        save(fig,name,[path,'inputs/continuation/coastline.zip'],title,'Depth 0–5 km, integer ticks, jet_r; magenta above 5, white below 0. Full location axes. '+size_note)
        limits.append(dict(figure=title,depth_limits_km=[0,5],ticks=list(range(6)),under=int((d.depth_km<0).sum()),over=int((d.depth_km>5).sum()),depth_range=[d.depth_km.min(),d.depth_km.max()],clip=False,plotted=len(d)))
    maps(table(D+'velest.csv'),'S6','figure_S6_provisional',D+'velest.csv')
    if extension and not (ROOT/(D+'relocated.csv')).exists():return
    e=table(D+'relocated.csv');maps(e,'3','figure_3_provisional',D+'relocated.csv')
    if extension and not (ROOT/(D+'summary.json')).exists():return
    # Figure 2 retains a weekly count axis; no unobserved interval is joined as zero.
    counts=table(D+'weekly_counts.csv');sectors=table(D+'sectors.csv');t=pd.to_datetime(sectors.time,utc=True)
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained',sharex=True)
    x=pd.to_datetime(counts.start,utc=True)
    # Sampling exists at stations in some otherwise empty weeks, but event
    # non-detection cannot establish a regional zero: draw only nonzero counts.
    for col,color,label in [('independent_events','black','Own provisional subset'),('other','#1f77b4','Other (alternative central selection)'),('geographic_sectors','#ff7f0e','Geographic sectors (alternative masks)')]:
        y=counts[col].astype(float);y.loc[counts.independent_events==0]=np.nan;axes[0].plot(x,y,'.-',color=color,ms=3,label=label)
    ax2=axes[0].twinx();ax2.plot(x,counts.context_routine_events,c='#2ca02c',lw=.55,alpha=.6);ax2.set_ylabel('External routine events/week',color='#2ca02c');ax2.tick_params(axis='y',colors='#2ca02c')
    axes[0].set(ylabel='Own subset events/week',title='A · Partial weekly counts; external context on separate scale');axes[0].legend(fontsize=7)
    for label,color in [('Other','#1f77b4'),('North','#ff7f0e'),('East','#ff7f0e'),('Southwest','#ff7f0e')]:
        z=sectors[sectors.sector==label];known=z.ML.notna();axes[1].scatter(pd.to_datetime(z.loc[known,'time'],utc=True),z.loc[known,'depth_km'],s=p.style.areas(z.loc[known,'ML']),c=color,lw=0,alpha=.8)
        axes[1].scatter(pd.to_datetime(z.loc[~known,'time'],utc=True),z.loc[~known,'depth_km'],s=9,c=color,lw=.45,marker='x')
    axes[1].set(ylabel='Depth below sea level (km)',xlabel='Date (UTC)',title='B · Provisional depths; magnitude size where measured, crosses otherwise');axes[1].invert_yaxis()
    fig.suptitle('Figure 2 · Partial; no exposure correction or confirmed hybrid markers',fontsize=10)
    save(fig,'figure_2_provisional',[D+'weekly_counts.csv',D+'sectors.csv'],'2A–B','Weekly counts; no false zeros in unobserved weeks. Alternative masks. External routine counts distinct axis. No invented hybrid timings or magnitudes.')
    # Supplement S7, conditional SVD covariance; original regional masks unknown.
    svd=table(U+'regional_svd.csv');svd['x'],svd['y']=PROJ.transform(svd.longitude.to_numpy(),svd.latitude.to_numpy())
    fig=plt.figure(figsize=(12,7.5),layout='constrained');grid=fig.add_gridspec(3,3,width_ratios=[1.5,1,1]);a=fig.add_subplot(grid[:2,0]);az=fig.add_subplot(grid[2,0]);p.coast(a)
    colors={'Central':'#167bd4','North':'#ff7f0e','Southwest':'#2ca02c','East':'red'};labels={'Central':'NW alternative','North':'NE alternative','Southwest':'SW alternative','East':'SE alternative'}
    for region,z in svd.groupby('region'):
        color=colors[region];a.errorbar(z.x,z.y,xerr=z.error_x_m/1000,yerr=z.error_y_m/1000,fmt='.',ms=2,elinewidth=.4,c=color,label=labels[region]);az.errorbar(z.x,z.depth_km,xerr=z.error_x_m/1000,yerr=z.error_z_m/1000,fmt='.',ms=2,elinewidth=.4,c=color)
    a.set(xlabel='Easting (km)',ylabel='Northing (km)',title='A · SVD locations and 2σ errors',xlim=(min(-6.,(svd.x-svd.error_x_m/1000).min()-.2),max(3.5,(svd.x+svd.error_x_m/1000).max()+.2)),ylim=(min(-3.5,(svd.y-svd.error_y_m/1000).min()-.2),max(3.5,(svd.y+svd.error_y_m/1000).max()+.2)));a.legend(fontsize=7);az.set(xlabel='Easting (km)',ylabel='Depth (km)');az.invert_yaxis()
    for i,key in enumerate(['x','y','z']):
        ax=fig.add_subplot(grid[i,1]);density=fig.add_subplot(grid[i,2])
        for region,z in svd.groupby('region'):
            y=z[f'error_{key}_m']/1000;n=z.ncc_p+z.ncc_s;valid=(y>0)&(n>0);ax.scatter(n[valid],y[valid],s=4,c=colors[region],lw=0)
            positive=y[y>0]
            if len(positive)>2 and np.std(positive)>0:
                xx=np.geomspace(max(1e-5,positive.min()/2),positive.max()*2,300);yy=gaussian_kde(np.log10(positive))(np.log10(xx));density.plot(xx,yy,c=colors[region],lw=.7);density.fill_between(xx,yy,color=colors[region],alpha=.15)
        ax.set(xscale='log',yscale='log',xlabel='NCCP + NCCS',ylabel=f'E{key.upper()} (km)',title='BDF'[i]);density.set(xscale='log',xlabel=f'E{key.upper()} (km)',ylabel='Density in log10(error)',title='CEG'[i])
    fig.suptitle(f'S7 · Partial: {len(svd)} conditional SVD estimates; alternative quadrants, sparse observations',fontsize=10)
    save(fig,'figure_S7_provisional',[U+'regional_svd.csv','inputs/continuation/coastline.zip'],'S7 all views','Positive 2-sigma errors; zero NCC observations excluded only from log-count axes. Scott KDE in log10(error), explicitly differing from unspecified paper bandwidth. All outliers retained. No fixed 10 m target.')
    # Annual and swarm maps use their original white/black simple style.
    summary=json.loads((ROOT/(D+'summary.json')).read_text())
    for kind,names,filename,title in [('year',[f'year{y}' for y in range(2022,2026)],'figure_S10_provisional','S10'),('swarm',[f'swarm-{i}' for i in range(1,5)],'figure_S11_provisional','S11')]:
        fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained');inputs=[]
        for ax,name in zip(axes.flat,names):
            path=D+name+'.csv';inputs.append(path);d=table(path)
            p.coast(ax);ax.scatter(d.x_km,d.y_km,s=3,c='black',lw=0);ax.set(xlim=(min(-6.,e.x_km.min()-.2),max(3.5,e.x_km.max()+.2)),ylim=(min(-3.5,e.y_km.min()-.2),max(3.5,e.y_km.max()+.2)),xlabel='Easting (km)',ylabel='Northing (km)',title=name+f' · {len(d)} provisional events');ax.grid(alpha=.25,lw=.5)
            if d.empty:ax.text(.5,.5,'No relocated result in this window\nSparse exposure; not evidence of no earthquakes',transform=ax.transAxes,ha='center',fontsize=8)
        fig.suptitle(title+' · Partial observed subsets; calendar selections, no substituted events',fontsize=10)
        save(fig,filename,inputs+['inputs/continuation/coastline.zip'],title,'Shared geographic axes expand beyond the original display when needed to retain every own location; black points; no magnitude-size mapping in these simple maps. Empty selection explicitly marked, not an empirical absence.')
    # S12: coordinate-ordered traces from actual original P picks, no author values.
    idx=table(D+'cpoz_index.csv');waves=np.load(ROOT/(D+'cpoz_gathers.npz'))
    fig=plt.figure(figsize=(11,10),layout='constrained');grid=fig.add_gridspec(3,3);a=fig.add_subplot(grid[0,:2]);b=fig.add_subplot(grid[0,2]);p.coast(a)
    colors={'East':'#2ca02c','Southwest':'#ff7f0e','North':'#1f77b4','Other':'black'}
    for sector,z in sectors.groupby('sector'):
        a.scatter(z.x_km,z.y_km,s=5,color=colors[sector],label=sector);b.scatter(z.x_km,z.depth_km,s=5,color=colors[sector])
    a.set(xlabel='Easting (km)',ylabel='Northing (km)',title='A · Alternative geographic sectors',xlim=(min(-6.,sectors.x_km.min()-.2),max(3.5,sectors.x_km.max()+.2)),ylim=(min(-3.5,sectors.y_km.min()-.2),max(3.5,sectors.y_km.max()+.2)));a.legend(fontsize=7);b.set(xlabel='Easting (km)',ylabel='Depth (km)',title='B · No imposed depth bands');b.invert_yaxis()
    for i,channel in enumerate(['HHZ','HHN']):
        for j,sector in enumerate(['East','Southwest','North']):
            ax=fig.add_subplot(grid[i+1,j]);g=idx[(idx.channel==channel)&(idx.sector==sector)].sort_values('x_km' if sector=='North' else 'y_km');coord='x_km' if sector=='North' else 'y_km'
            for r in g.itertuples():
                t,y=waves[r.array_key];center=getattr(r,coord)
                ax.pcolormesh(np.r_[t,t[-1]+1/r.sample_rate_hz]+1,[center-.020,center+.020],y[None,:],cmap='seismic',vmin=-1,vmax=1,shading='flat',rasterized=True)
            ax.set(xlim=(0,8),xlabel='Time from window start (s)',ylabel='Easting (km)' if sector=='North' else 'Northing (km)',title=f'{"CDEFGH"[i*3+j]} · {sector}, {channel}, n={len(g)}');ax.axvline(1,c='.5',ls=':',lw=.5)
            if g.empty:ax.text(.5,.5,'No retained CPOZ P window\nin this alternative sector',transform=ax.transAxes,ha='center',fontsize=8)
    fig.suptitle('S12 · Provisional locations and >4 Hz gathers; unreviewed onsets, alternative masks',fontsize=10)
    save(fig,'figure_S12_provisional',[D+'sectors.csv',D+'cpoz_index.csv',D+'cpoz_gathers.npz','inputs/continuation/coastline.zip'],'S12','Actual P-aligned eight-second traces; normalized amplitudes -1..1, seismic diverging palette. No traces inferred between coordinates; 0.040 km display strip width only, not spatial averaging or uncertainty. Sector membership differs from unpublished masks.')
    # S13 locations are available even though the exact satellite image is not.
    fig,axes=plt.subplots(2,1,figsize=(8,9),layout='constrained',facecolor='black')
    for ax,box,label in zip(axes,[(-6,3.5,-3.5,3.5),(-2,2,-1,2)],['A · Full caldera','B · Onshore display window']):
        p.coast(ax)
        for line in ax.lines:line.set_color('white')
        scatter(ax,e,'x_km','y_km');ax.set(xlim=box[:2],ylim=box[2:],xlabel='Easting (km)',ylabel='Northing (km)',title=label);p.style.frame(ax,True)
    cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cm),ax=axes,extend='max',ticks=range(6),shrink=.7);cb.ax.invert_yaxis();cb.ax.tick_params(colors='white');cb.set_label('Depth (km); magenta >5 km',color='white')
    fig.suptitle('S13 · Partial relocated maps; satellite layer not implemented; independent coastline',color='white',fontsize=9)
    save(fig,'figure_S13_provisional',[D+'relocated.csv','inputs/continuation/coastline.zip'],'S13A–B','Own locations; no copied satellite/DEM or figure pixels. Basemap mismatch disclosed. Full data in saved table, explicit onshore display window.')
    (ROOT/(D+'style.json')).write_text(json.dumps(limits,indent=2)+'\n')
    if extension:return
    hybrid='data/grid_calibration/merged4/hybrid/'
    if (ROOT/(hybrid+'display_candidates.csv')).exists():
        candidates=table(hybrid+'display_candidates.csv');arrays=np.load(ROOT/(hybrid+'display_waveforms.npz'))
        fig,axes=plt.subplots(1,3,figsize=(13,8),layout='constrained')
        for ax,(template,z) in zip(axes,candidates.groupby('template',sort=True)):
            z=z.sort_values('time')
            for i,r in enumerate(z.itertuples()):
                t,w=arrays[r.array_key];ax.plot(t,i+.32*w,c='red' if r.FI<0 else 'black',lw=.45)
                ax.text(0,i+.4,str(r.time)[:19]+f'  cc={r.cc:.2f}',fontsize=5.5)
                ax.text(0,i+.12,f'FI={r.FI:.2f}; log10(A/Amax)={r.log10_horizontal_ratio:.2f}',fontsize=5.5)
            ax.set(xlim=(0,8),ylim=(-.5,len(z)),xlabel='Time from template alignment (s)',yticks=[],title=template+f' candidates · {len(z)} displayed')
        fig.suptitle('S14 · Partial candidate-family analysis; no confirmed hybrids or validated clusters\nTwelve highest correlations per template; amplitude ratios are not accepted relative magnitudes',fontsize=10)
        save(fig,'figure_S14_candidates',[hybrid+'display_candidates.csv',hybrid+'display_waveforms.npz'],'S14/1–3','Measured original CAAM 1–10 Hz waveforms; FI<0 red; labels are own correlation/FI/amplitude measurements. Highest-score display subset, no event confirmation. No independent unclustered sample.')
