"""Publication counterparts from saved local-extension and mechanism results."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from obspy.imaging.beachball import beach
from pyproj import Transformer
import publication_plots as p
import grid_publication_panels as gp
ROOT=p.ROOT;D=ROOT/'data/mechanism_followup';PROJ=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)

def main():
    p.theme();gp.generate(p,extension=True,base_override='data/local_extension/calibration/merged4/')
    p.magnitudes(extension=True,source_override='data/local_extension/calibration/merged4/magnitude')
    coverage=pd.read_csv(ROOT/'data/local_extension/processed_coverage.csv')
    short={r['file'] for r in json.loads((ROOT/'data/local_extension/short_window_inputs.json').read_text())}
    coverage['station']=coverage.channel.str.split('.').str[:2].str.join('.')
    names=sorted(coverage.station.unique());fig,ax=plt.subplots(figsize=(9,8),layout='constrained')
    epoch=mdates.date2num(pd.Timestamp('1970-01-01'))
    for i,sta in enumerate(names):
        for r in coverage[coverage.station==sta].assign(short=coverage.file.isin(short)).sort_values('short').itertuples():
            color='#d95f02' if r.file in short else '#2166ac'
            ax.plot([epoch+r.start/86400,epoch+r.end/86400],[i,i],lw=3,color=color,solid_capstyle='butt',marker='|',markevery=[0],ms=4,mew=.6)
    ax.set(yticks=range(len(names)),yticklabels=names,xlabel='UTC; actual sample intervals',title='S1 · Retrieved records; large gaps remain')
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,7]));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.set_xlim(mdates.date2num(pd.Timestamp('2022-01-21')),mdates.date2num(pd.Timestamp('2025-03-21')))
    ax.tick_params(axis='y',labelsize=8);ax.grid(axis='x',alpha=.3);ax.invert_yaxis()
    ax.plot([],[],lw=3,color='#2166ac',label='Returned public intervals');ax.plot([],[],lw=3,color='#d95f02',label='Event-selected short windows')
    ax.legend(loc='lower left',fontsize=8)
    fig.supxlabel('1,024 files · 30 station names · 8,952.452 union channel-hours\nTicks mark interval starts for visibility, not duration. Four names have only short single-channel windows.',fontsize=9)
    p.save(fig,'coverage_local_followup',['data/local_extension/processed_coverage.csv','data/local_extension/short_window_inputs.json'],'S1','Actual intervals, no requested duration counted. Fixed-width ticks identify start times, not continuous exposure. Event-selected original windows distinguished from returned public intervals.',png=True)
    mech=pd.read_csv(D/'gcap/solutions.csv');e=pd.read_csv(ROOT/'data/coverage_extension/calibration/merged4/panels/relocated.csv')
    mech['x'],mech['y']=PROJ.transform(mech.longitude.to_numpy(),mech.latitude.to_numpy())
    fig,axes=plt.subplots(2,1,figsize=(8,10.5),layout='constrained',facecolor='black')
    norm=Normalize(0,5,clip=False);cm=p.style.depth_cmap()
    for ax,box,title in zip(axes,[(-6,3.5,-3.5,3.5),(-3,2,-1,3)],['A · Whole caldera','B · Central display window']):
        p.coast(ax)
        for line in ax.lines:line.set_color('white')
        known=e.ML.notna();ax.scatter(e.loc[known,'x_km'],e.loc[known,'y_km'],s=p.style.areas(e.loc[known,'ML']),c=e.loc[known,'depth_km'],norm=norm,cmap=cm,lw=0)
        ax.scatter(e.loc[~known,'x_km'],e.loc[~known,'y_km'],s=8,marker='x',c=e.loc[~known,'depth_km'],norm=norm,cmap=cm,lw=.4)
        # Display all own trial fits on A; B uses its explicit geographic zoom.
        subset=mech if title.startswith('A') else mech[mech.x.between(box[0],box[1])&mech.y.between(box[2],box[3])]
        for i,r in enumerate(subset.itertuples()):
            left=i%2==0;xx=box[0]+.65 if left else box[1]-.65;yy=box[3]-.6-(i//2)*.8
            ax.plot([r.x,xx],[r.y,yy],c='.7',lw=.5);ax.plot(r.x,r.y,'o',mfc='none',mec='white',ms=6,mew=.6)
            bb=beach([r.strike,r.dip,r.rake],xy=(xx,yy),width=.35,linewidth=.5,facecolor='.55',edgecolor='white',bgcolor='white',zorder=5);ax.add_collection(bb)
            ax.text(xx,yy-.23,f'{r.event_id}: VR {r.variance_reduction_percent:.1f}%',color='white',ha='center',va='top',fontsize=7)
        ax.set(xlim=box[:2],ylim=box[2:],xlabel='Easting (km)',ylabel='Northing (km)',title=title,aspect='equal');p.style.frame(ax,True);ax.grid(color='white',alpha=.25,lw=.4)
        cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cm),ax=ax,ticks=range(6),extend='max',shrink=.78);cb.ax.invert_yaxis();cb.set_label('Depth (km); magenta >5 km',color='white');cb.ax.tick_params(colors='white')
    fig.suptitle('Figure 4 · Provisional waveform fits, not accepted focal mechanisms\nGray = unvalidated; 0.2–2 Hz trial; no SKHASH solution',color='white',fontsize=10)
    fig.supxlabel('Uniform beachball size: Mw is exploratory. No terrain raster; B colors show depth, not elevation.',color='white',fontsize=8)
    p.save(fig,'figure_4_followup',['data/mechanism_followup/gcap/solutions.csv','data/coverage_extension/calibration/merged4/panels/relocated.csv','inputs/continuation/coastline.zip'],'4A–B','Gray is a separate unvalidated class, not the publication red/blue quality mapping. Background depth 0–5 km jet_r, integer ticks, magenta >5. B has no independent DEM: depth, not published elevation. Beachballs uniform .35 km display width; no magnitude claim.',png=True)
    # Supporting diagnostic: saved observed/predicted windows, one common
    # normalization per pair, no synthetic observations and no published images.
    idx=pd.read_csv(D/'gcap/fit_index.csv');a=np.load(D/'gcap/fit_waveforms.npz');fig,axes=plt.subplots(4,2,figsize=(10,8),layout='constrained')
    for row,sta in enumerate(['CPOZ','CFMN','CMIS','CAAM']):
        for col,(component,number) in enumerate([('Pnl Z',8),('S transverse',0)]):
            g=idx[(idx.event_id==649)&idx.file.str.contains('_'+sta+'.',regex=False)];pair=[]
            for digit in [number,number+1]:
                item=g[g.file.str.endswith('.'+str(digit))].iloc[0];pair.append(a[item.key])
            scale=max(abs(pair[0][1]).max(),1e-30);ax=axes[row,col]
            for arr,color,label in zip(pair,['black','red'],['Observed','FK/gCAP prediction']):ax.plot(arr[0],arr[1]/scale,c=color,lw=.8,label=label)
            ax.set(xlabel='Seconds from own origin',ylabel='Common amplitude scale',title=sta+' · '+component)
    axes[0,0].legend(fontsize=8);fig.suptitle('Reproduction diagnostic: event 649, poor waveform fit (VR 6.0%)',fontsize=11)
    p.save(fig,'mechanism_fit_diagnostic',['data/mechanism_followup/gcap/fit_index.csv','data/mechanism_followup/gcap/fit_waveforms.npz'],'diagnostic','Even output suffix is observed, odd is theoretical. Stored SAC a includes fitted lag. One observed-peak normalization per pair; prediction amplitude not independently normalized.',png=True)
    for r in p.RECORD:r['command']='.venv/bin/python scripts/plot_local_followup.py'
    (D/'plot_inventory.json').write_text(json.dumps(p.RECORD,indent=2)+'\n')
if __name__=='__main__':main()
