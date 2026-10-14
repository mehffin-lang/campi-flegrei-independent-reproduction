"""Publication counterparts from saved eligible EIDA numerical outputs only."""
import json
import numpy as np,pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from obspy.imaging.beachball import beach
from pyproj import Transformer
import publication_plots as p
import grid_publication_panels as gp
ROOT=p.ROOT;D=ROOT/'data/eida_continuation';B=D/'calibration/merged4';M=ROOT/'data/mechanism_eida'
PROJ=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)

def shallow_plot(save):
    shallow=D/'shallow_example';review=json.loads((shallow/'summary.json').read_text())
    if review['available']:
        data=pd.read_csv(shallow/'waveforms.csv');spectra=np.load(shallow/'spectra.npz')
        fig,axes=plt.subplots(2,4,figsize=(12,3.2),sharex='col',layout='constrained')
        for k,(station,component) in enumerate([(s,c) for s in ['CAAM','COLB'] for c in ['Z','E']]):
            g=data[(data.station==station)&(data.component==component)];key=station+'_'+component
            axes[0,k].plot(g.time_s,g.normalized,c='black',lw=.55);axes[0,k].set(title=station+' HH'+component,yticks=[],ylim=(-1.05*data.normalized.abs().max(),1.05*data.normalized.abs().max()))
            f=spectra[key+'_f'];mask=(f>=1)&(f<=20);power=10*np.log10(np.maximum(spectra[key+'_power'][mask],np.finfo(float).tiny))
            axes[1,k].pcolormesh(spectra[key+'_t'],f[mask],power,cmap=p.spectral_cmap('gist_rainbow_r',power,key),vmin=-80,vmax=0,shading='auto',rasterized=True)
            axes[1,k].set(yscale='log',ylim=(1,20),xlim=(-2,12),xlabel='Seconds from own CAAM P',ylabel='Hz' if k==0 else '')
        r=review['selected'];fig.suptitle(f'S15D analogue · own event {r["event_index"]}, trial depth {r["depth_km"]:.3f} km; source type and depth unvalidated\nObserved velocity normalized by CAAM; spectra −80…0 dB, explicit scale differing from unspecified paper normalization.',fontsize=8)
        save(fig,'figure_S15D_eida_followup',[str((shallow/n).relative_to(ROOT)) for n in ['waveforms.csv','spectra.npz','summary.json']],'S15D','Different independently associated waveform example, not an identified published VT event. Provisional shallow location; CAAM proximity is an explicit alternative to unavailable west-Accademia polygon. No figure pixels or reference event result supplies input.')

def main():
    p.theme();original=p.save
    def save(fig,name,inputs,panel,note='',png=False):
        name=name.replace('_local_followup','_eida_followup')
        original(fig,name,inputs,panel,note,png=True)
    p.save=save
    gp.generate(p,extension=True,base_override=str(B.relative_to(ROOT))+'/')
    p.magnitudes(extension=True,source_override=str((B/'magnitude').relative_to(ROOT)))
    best=pd.read_csv(B/'panels/best_located.csv')
    if len(best):
        fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained',facecolor='black')
        for ax,(xx,yy) in zip(axes,[('x_km','y_km'),('depth_km','y_km'),('x_km','depth_km')]):
            ax.scatter(best[xx],best[yy],s=3,c=best.depth_km,cmap=p.style.depth_cmap(),vmin=0,vmax=5,lw=0)
            ax.set(xlabel=xx.replace('_',' '),ylabel=yy.replace('_',' '));p.style.frame(ax,True)
        axes[2].invert_yaxis();p.coast(axes[0])
        cb=fig.colorbar(ScalarMappable(norm=Normalize(0,5),cmap=p.style.depth_cmap()),ax=axes,ticks=range(6),extend='max');cb.ax.invert_yaxis();cb.ax.tick_params(colors='white');cb.set_label('Depth (km); magenta >5',color='white')
        fig.suptitle(f'S9 · {len(best)} own trial events with NCCP+NCCS ≥100; model accuracy unvalidated',color='white',fontsize=10)
        save(fig,'figure_S9_eida_followup',[str((B/'panels/best_located.csv').relative_to(ROOT)),'inputs/continuation/coastline.zip'],'S9 all views','Documented >=100 selection; provisional locations, fixed depth colors and no inferred data.')
    cov=pd.read_csv(D/'processed_coverage.csv');cov['station']=cov.channel.str.split('.').str[:2].str.join('.')
    a=json.loads((D/'analysis_summary.json').read_text());names=sorted(cov.station.unique())
    fig,ax=plt.subplots(figsize=(9,7),layout='constrained')
    for i,sta in enumerate(names):
        z=cov[cov.station==sta];starts=z.start.to_numpy()/86400;ends=z.end.to_numpy()/86400
        segments=np.stack([np.column_stack([starts,np.full(len(z),i)]),np.column_stack([ends,np.full(len(z),i)])],axis=1)
        ax.add_collection(LineCollection(segments,linewidths=2,colors='#2166ac',capstyle='butt'))
        ax.plot(starts,np.full(len(z),i),ls='none',marker='|',ms=3,mew=.5,color='#2166ac')
    ax.set(yticks=range(len(names)),yticklabels=names,xlabel='UTC; actual returned sample intervals',title='S1 · Continuous observation intervals; large gaps remain')
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,7]));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'));ax.invert_yaxis();ax.grid(axis='x',alpha=.25)
    ax.set_xlim(mdates.date2num(pd.Timestamp('2022-01-21')),mdates.date2num(pd.Timestamp('2025-03-21')))
    fig.supxlabel(f'{a["files"]:,} files · {len(a["stations"])} station names · {a["processed_channel_hours"]:,.3f} union channel-hours\nEvent-selected snippets excluded. Ticks identify interval starts, not duration.',fontsize=9)
    save(fig,'coverage_eida_followup',[str((D/'processed_coverage.csv').relative_to(ROOT))],'S1','Only successful observed samples; no failed/pending request or event-selected snippet counted.')
    mech=pd.read_csv(M/'gcap/solutions.csv');events=pd.read_csv(B/'panels/relocated.csv');mech['x'],mech['y']=PROJ.transform(mech.longitude.to_numpy(),mech.latitude.to_numpy())
    fig,axes=plt.subplots(2,1,figsize=(8,10.5),layout='constrained',facecolor='black');norm=Normalize(0,5,clip=False);cm=p.style.depth_cmap()
    for ax,box,title in zip(axes,[(min(-6.,events.x_km.min()-.2),max(3.5,events.x_km.max()+.2),min(-3.5,events.y_km.min()-.2),max(3.5,events.y_km.max()+.2)),(-3,2,-1,3)],['A · Whole caldera','B · Central display window']):
        p.coast(ax)
        for line in ax.lines:line.set_color('white')
        known=events.ML.notna();ax.scatter(events.loc[known,'x_km'],events.loc[known,'y_km'],s=p.style.areas(events.loc[known,'ML']),c=events.loc[known,'depth_km'],norm=norm,cmap=cm,lw=0)
        ax.scatter(events.loc[~known,'x_km'],events.loc[~known,'y_km'],s=8,marker='x',c=events.loc[~known,'depth_km'],norm=norm,cmap=cm,lw=.4)
        subset=mech if title.startswith('A') else mech[mech.x.between(box[0],box[1])&mech.y.between(box[2],box[3])]
        for i,r in enumerate(subset.itertuples()):
            xx=box[0]+.65 if i%2==0 else box[1]-.65;spacing=(box[3]-box[2]-.8)/(int(np.ceil(len(subset)/2))+1);yy=box[3]-.5-(i//2)*spacing
            ax.plot([r.x,xx],[r.y,yy],c='.7',lw=.5);ax.plot(r.x,r.y,'o',mfc='none',mec='white',ms=6,mew=.6)
            ax.add_collection(beach([r.strike,r.dip,r.rake],xy=(xx,yy),width=min(.35,.65*spacing),linewidth=.5,facecolor='.55',edgecolor='white',bgcolor='white',zorder=5))
            ax.text(xx,yy-min(.23,.45*spacing),f'{r.event_id}: VR {r.variance_reduction_percent:.1f}%',color='white',ha='left' if i%2==0 else 'right',va='top',fontsize=7)
        ax.set(xlim=box[:2],ylim=box[2:],xlabel='Easting (km)',ylabel='Northing (km)',title=title,aspect='equal');p.style.frame(ax,True);ax.grid(color='white',alpha=.25,lw=.4)
        cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cm),ax=ax,ticks=range(6),extend='max',shrink=.78);cb.ax.invert_yaxis();cb.set_label('Depth (km); magenta >5 km',color='white');cb.ax.tick_params(colors='white')
    fig.suptitle('Figure 4 · Unaccepted waveform-inversion trials\nGray: unvalidated, 0.2–2 Hz; own current model; linked candidate locations',color='white',fontsize=10)
    fig.supxlabel('Background: new EIDA trial catalog. Candidate IDs are separate. Uniform beachball sizes; no terrain raster.',color='white',fontsize=8)
    save(fig,'figure_4_eida_followup',[str((M/'gcap/solutions.csv').relative_to(ROOT)),str((B/'panels/relocated.csv').relative_to(ROOT)),'inputs/continuation/coastline.zip'],'4A–B','Gray unvalidated trials, separate review IDs, explicit shared-phase location mapping and current own model. Background new catalog not joined by integer IDs. Depth 0–5 km jet_r, reversed integer colorbar, magenta >5, no clipping. Uniform beachball area; depth rather than unavailable terrain elevation in B.')
    idx=pd.read_csv(M/'gcap/fit_index.csv');fits=np.load(M/'gcap/fit_waveforms.npz')
    fig,axes=plt.subplots(4,2,figsize=(10,8),layout='constrained')
    for row,eid in enumerate([649,100331,101400,101760]):
        g=idx[idx.event_id.eq(eid)&idx.file.str.contains('_CPOZ.',regex=False)]
        vr=mech.loc[mech.event_id.eq(eid),'variance_reduction_percent'].iloc[0]
        for col,(label,digit) in enumerate([('Pnl Z',8),('S transverse',0)]):
            arrays=[fits[g[g.file.str.endswith('.'+str(k))].iloc[0].key] for k in [digit,digit+1]]
            scale=max(abs(arrays[0][1]).max(),1e-30);ax=axes[row,col]
            for arr,color,name in zip(arrays,['black','red'],['Observed','FK/gCAP prediction']):ax.plot(arr[0],arr[1]/scale,color=color,lw=.8,label=name)
            ax.set(xlabel='Seconds from own origin',ylabel='Common amplitude scale',title=f'{eid} CPOZ · {label}; event VR {vr:.1f}%')
    axes[0,0].legend(fontsize=8);fig.suptitle('Reproduction diagnostic: own observed and predicted windows, 0.2–2 Hz\nUnaccepted mechanisms; predictions are not observations',fontsize=10)
    save(fig,'mechanism_eida_fit_diagnostic',[str((M/'gcap'/n).relative_to(ROOT)) for n in ['fit_index.csv','fit_waveforms.npz','solutions.csv']],'diagnostic','Fixed four-event CPOZ comparison, common observed-peak normalization per pair; theoretical amplitudes not independently normalized. Saved SAC a includes fitted window lag. Supporting documentation only, never a paper-panel counterpart.')
    H=D/'hybrid';candidates=pd.read_csv(H/'display_candidates.csv');waves=np.load(H/'display_waveforms.npz')
    fig,axes=plt.subplots(1,3,figsize=(13,8),layout='constrained')
    for ax,(template,z) in zip(axes,candidates.groupby('template',sort=True)):
        z=z.sort_values('time')
        for i,r in enumerate(z.itertuples()):
            offset=1.4*i
            t,w=waves[r.array_key];ax.plot(t,offset+.32*w,c='red' if r.FI<0 else 'black',lw=.45)
            ax.text(0,offset+.65,str(r.time)[:19]+f'  cc={r.cc:.2f}',fontsize=5.5);ax.text(0,offset+.43,f'FI={r.FI:.2f}; log10(A/Amax)={r.log10_horizontal_ratio:.2f}',fontsize=5.5)
        ax.set(xlim=(0,8),ylim=(-.5,1.4*len(z)),xlabel='Time from template alignment (s)',yticks=[],title=template+f' candidates · {len(z)} displayed')
    fig.suptitle('S14 · Unconfirmed candidates; no validated hybrid clusters\nTwelve highest correlations per template; amplitude ratios are not accepted relative magnitudes',fontsize=10)
    save(fig,'figure_S14_eida_followup',[str((H/'display_candidates.csv').relative_to(ROOT)),str((H/'display_waveforms.npz').relative_to(ROOT))],'S14/1–3','Measured original CAAM 1–10 Hz waveforms. FI<0 red. Own correlations, spectral indices and amplitude ratios; no confirmed family or unclustered sample.')
    p.hybrids() # Correct common amplitude axes from unchanged saved observations.
    shallow_plot(save)
    for record in p.RECORD:record['command']='.venv/bin/python scripts/plot_eida_followup.py'
    (D/'plot_inventory.json').write_text(json.dumps(p.RECORD,indent=2)+'\n')

if __name__=='__main__':main()
