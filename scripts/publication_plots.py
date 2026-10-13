"""Restyle every current generated figure from saved numerical products only.

Published images were visually inspected to specify styles; this code never
reads them. Diagnostics retain their meaning and are not publication panels.
"""
from pathlib import Path
import os,json,hashlib
ROOT=Path(__file__).resolve().parents[1];os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
from scipy.signal import spectrogram,find_peaks
from plot_continuation import coast
import routine_plot_style as style
D=ROOT/'data/continuation';F=ROOT/'figures';OUT=ROOT/'data/grid_calibration/style';RECORD=[];SPECTRAL=[]

def theme():
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,'axes.linewidth':.6,'lines.linewidth':.7,'axes.spines.top':True,'axes.spines.right':True,'pdf.fonttype':42,'savefig.dpi':180})
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def register(name,inputs,panel,note):
    files=['figures/'+name+'.pdf']+(['figures/'+name+'.png'] if (F/(name+'.png')).exists() else [])
    RECORD.append(dict(files=files,corresponding_panel=panel,note=note,inputs={str(p):sha(p) for p in inputs},command='.venv/bin/python scripts/publication_plots.py',outputs={p:sha(p) for p in files}))
def save(fig,name,inputs,panel,note='',png=False):
    fig.savefig(F/(name+'.pdf'),bbox_inches='tight',facecolor=fig.get_facecolor())
    if png or (F/(name+'.png')).exists():fig.savefig(F/(name+'.png'),bbox_inches='tight',facecolor=fig.get_facecolor())
    plt.close(fig);register(name,inputs,panel,note)
def dark(ax):style.frame(ax)
def date(x):return pd.to_datetime(x,utc=True,format='ISO8601')
def spectral_cmap(name,values,panel):
    cm=plt.get_cmap(name).copy();cm.set_under('white');cm.set_over('black')
    SPECTRAL.append(dict(panel=panel,limits_dB=[-80,0],ticks=None,paper_limits='No numerical limits/colorbar printed; this is an explicit independent display normalization.',palette=name,under_color='white',over_color='black',under_count=int((values < -80).sum()),over_count=int((values > 0).sum()),data_range_dB=[float(values.min()),float(values.max())],clipped=False))
    return cm

def history(ax):
    lev=pd.read_csv(D/'historical_leveling.csv');g=pd.read_csv(D/'rite_gnss.csv')
    for kind,marker,color,label in [('leveling survey','o','white','Leveling observations'),('source-provided estimate','^','#ffc870','Source estimates'),('source-provided reconstruction','x','#ee80bc','Source reconstruction')]:
        x=lev[lev.provenance_class==kind];ax.plot(date(x.date),x.elevation_m,linestyle='none',marker=marker,ms=3,mfc='none',mec=color,color=color,label=label)
    y=g.leveling_datum_m.copy();t=date(g.time);y.loc[t.diff()>pd.Timedelta(days=7)]=np.nan
    ax.plot(t,y,color='white',lw=.65,label='Daily GNSS')
    ax.set(xlabel='Year',ylabel='Vertical deformation (m)',title='B · Displacement through 20 March 2025');dark(ax)
    ax.legend(fontsize=6,facecolor='black',edgecolor='.5',labelcolor='white',ncol=2,loc='upper left')
def rate(ax):
    c=pd.read_csv(D/'figure_1C.csv');cum=pd.read_csv(D/'figure_1C_cumulative.csv');large=cum[cum.Md>=4]
    ax.bar(pd.to_datetime(c.month+'-01'),c.events,width=c.bin_days,align='edge',color='#8dd3c7',label='Monthly event count')
    ax.axvspan(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21'),color='#8c9cb2',alpha=.5)
    twin=ax.twinx();twin.step(date(cum.time),cum.cumulative,where='post',color='.85',ls='--',lw=1,label=r'Cumulative $M_d>0.2$')
    twin.scatter(date(large.time),large.cumulative,c='#c62728',s=26,marker='X',label=r'$M_d\geq4$')
    ax.set(xlabel='Year',ylabel='Monthly event count',title='C · External routine-catalog seismicity',xlim=(pd.Timestamp('2005-01-01'),pd.Timestamp('2025-03-21')));twin.set_ylabel('Cumulative event count')
    ax.xaxis.set_major_locator(mdates.YearLocator(2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m'));ax.tick_params(axis='x',rotation=60)
    dark(ax);dark(twin);twin.patch.set_visible(False)
    h,l=ax.get_legend_handles_labels();hh,ll=twin.get_legend_handles_labels();ax.legend(h+hh,l+ll,fontsize=6,facecolor='black',edgecolor='none',labelcolor='white',loc='upper left')

def contextual():
    style.standalone(ROOT,coast)
    for name,filename,panel in [('figure_1A_routine','figure_1A.csv','1A'),('figure_S5_routine','figure_S5.csv','S5')]:
        register(name,['data/continuation/'+filename,'inputs/continuation/coastline.zip'],panel,'Depth color 0–5 km, jet_r; >5 magenta, <0 white. S5 ticks 0..5. 1A ticks 0,2,4; unlabeled endpoints not exactly recoverable. Data unmodified; extent exclusions disclosed.')
    hist_inputs=['data/continuation/historical_leveling.csv','data/continuation/rite_gnss.csv'];rate_inputs=['data/continuation/figure_1C.csv','data/continuation/figure_1C_cumulative.csv']
    for name,fn,inp,panel in [('figure_1B_displacement',history,hist_inputs,'1B'),('figure_1C_routine',rate,rate_inputs,'1C')]:
        fig,ax=plt.subplots(figsize=(7,3.6),layout='constrained',facecolor='black');fn(ax);save(fig,name,inp,panel,'Black background, white labels. Source estimates remain distinct; full data range retained.')
    fig=plt.figure(figsize=(11.5,6.3),layout='constrained',facecolor='black');left,right=fig.subfigures(1,2,width_ratios=[1.4,1]);left.set_facecolor('black');right.set_facecolor('black')
    a=left.subplots();b,c=right.subplots(2,1);cat=pd.read_csv(D/'figure_1A.csv');sm=style.map_panel(a,cat,'1A',coast,'A · External routine-catalog locations');style.depth_bar(left,a,sm);history(b);rate(c)
    save(fig,'figure_1_combined',['data/continuation/figure_1A.csv','inputs/continuation/coastline.zip']+hist_inputs+rate_inputs,'1A–C','Original panel arrangement; contextual observations, not independent earthquake detections.')

def coverage():
    sources=[('data/continuation','continuation_coverage'),('data/calibration_followup/expanded','followup_coverage')]
    if (ROOT/'data/coverage_extension/analysis_summary.json').exists():sources.append(('data/coverage_extension','coverage_extension'))
    for folder,name in sources:
        path=folder+'/processed_coverage_union.json';rows=json.loads((ROOT/path).read_text());groups={}
        for r in rows:groups.setdefault('.'.join(r['channel'].split('.')[:-1])+'.'+r['channel'].split('.')[-1][:-1],[]).extend(r['intervals'])
        fig,ax=plt.subplots(figsize=(8,8),layout='constrained')
        segments=[]
        for i,(sta,spans) in enumerate(sorted(groups.items())):
            for aa,bb in spans:segments.append([(aa/86400,i),(bb/86400,i)])
        ax.add_collection(LineCollection(segments,colors='#1f77b4',linewidths=.8,rasterized=True));ax.set_ylim(-1,len(groups))
        centers=np.mean(np.asarray(segments),axis=1)
        ax.scatter(centers[:,0],centers[:,1],marker='|',s=10,linewidths=.5,c='#1f77b4',rasterized=True)
        ax.set_yticks(range(len(groups)),sorted(groups),fontsize=7);ax.yaxis.tick_right();ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.set(xlim=(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21')),xlabel='UTC date',title='S1 · Actual intervals; short intervals marked at their midpoints')
        save(fig,name,[path],'S1','White background, blue actual intervals and vertical midpoint ticks for otherwise invisible short intervals. Ticks do not imply duration. Right-hand instrument labels; no unavailable intervals drawn.')

def station_map():
    x=pd.read_csv(D/'figure_S2.csv').sort_values('id').reset_index(drop=True);fig,ax=plt.subplots(figsize=(10,8),facecolor='black');fig.subplots_adjust(left=.09,bottom=.08,right=.98,top=.94);coast(ax)
    for line in ax.lines:line.set_color('white')
    palette={'HH':'red','EH':'#ffbf00','HN':'white','HG':'white'}
    for band,g in x.groupby('band'):
        color=palette.get(band,'#cccccc');ok=g.coordinate_status.eq('verified official epoch')
        ax.scatter(g.loc[ok,'x_km'],g.loc[ok,'y_km'],marker='^',s=45,c=color,label={'HH':'Broadband','EH':'Short period','HN':'Accelerometer','HG':'Accelerometer'}.get(band,band))
        ax.scatter(g.loc[~ok,'x_km'],g.loc[~ok,'y_km'],marker='^',s=45,edgecolor=color,facecolor='none')
    ax.set(xlim=(-10,13),ylim=(-8,9),aspect='equal',xlabel='Easting (km)',ylabel='Northing (km)',title='S2 · Audited station coordinates; membership partial');dark(ax);fig.canvas.draw()
    placed=[];points=ax.transData.transform(x[['x_km','y_km']].to_numpy())
    for i,r in x.iterrows():
        point=points[i];target=None
        for radius in [14,22,34,48,66,88,114,142]:
            for angle in np.linspace(0,2*np.pi,48,endpoint=False):
                test=point+radius*np.array([np.cos(angle),np.sin(angle)])
                if (ax.bbox.x0+30<test[0]<ax.bbox.x1-30 and ax.bbox.y0+10<test[1]<ax.bbox.y1-10 and all(abs(test[0]-q[0])>52 or abs(test[1]-q[1])>18 for q in placed) and all(abs(test[0]-q[0])>24 or abs(test[1]-q[1])>12 for q in points)):
                    target=test;break
            if target is not None:break
        if target is None:target=point+np.array([0,14])
        placed.append(target);label=r.station+('?' if r.coordinate_status!='verified official epoch' else '')
        ax.annotate(label,(r.x_km,r.y_km),xytext=ax.transData.inverted().transform(target),color='white',fontsize=8,ha='center',va='center',arrowprops=dict(arrowstyle='-',lw=.4,color='.7'))
    ax.legend(facecolor='black',labelcolor='white',edgecolor='.5',fontsize=8,loc='upper right');ax.text(.02,.02,'Open triangles / ?: unresolved epoch. 51 identifiers, not verified 48 instruments.\nNo independent elevation raster; no elevation colorbar.',transform=ax.transAxes,color='white',fontsize=7)
    save(fig,'continuation_stations',['data/continuation/figure_S2.csv','inputs/continuation/coastline.zip'],'S2','Instrument-type colors from saved band metadata. No topography inferred or copied. Expanded extent retains all stations; leader labels replace overlap.')

def picking():
    cases=[('figure_S4A','data/continuation/figure_S4A.npz','S4A',True)]+[(f'picker_comparison_{s}',f'data/extended/picker_comparison_{s}.npz','diagnostic resembling S4',False) for s in ['CSOB','CMIS']]
    for name,file,panel,current in cases:
        saved_marks=json.loads((D/'figure_S4A_picks.json').read_text()) if current else None
        a=np.load(ROOT/file);t=a['time_s' if current else 'time'];y=a['vertical_counts' if current else 'raw_vertical_counts'];norm=float(np.max(abs(y)))
        f,ts,pow=spectrogram(y/norm,fs=100,nperseg=256,noverlap=192);db=10*np.log10(np.maximum(pow,np.finfo(float).tiny));target=OUT/(name+'_display.npz');np.savez_compressed(target,frequency_Hz=f,time_s=ts,power_dB=db,normalizer_counts=norm)
        fig,axes=plt.subplots(4,1,figsize=(9,5.5),sharex=True,gridspec_kw={'height_ratios':[2,2,1,1]},layout='constrained')
        axes[0].plot(t,y/norm,c='black',lw=.45,label='HHZ');axes[0].set(ylim=(-1,1),ylabel='Normalized amplitude');axes[0].legend(fontsize=7)
        mesh=axes[1].pcolormesh(ts,f,db,cmap=spectral_cmap('jet',db,name),vmin=-80,vmax=0,shading='auto',rasterized=True);axes[1].set(ylim=(0,50),ylabel='Frequency (Hz)')
        for ax,model in zip(axes[2:],['original','retrained']):
            for phase,color,linecolor in [('P','#1f77b4','#159c9b'),('S','#ff7f0e','red')]:
                key=model+'_'+phase;tt=a[key+('_time_s' if current else '_time')];yy=a[key]
                ax.plot(tt,yy,color=color,lw=.6,label=phase+' probability')
                if current:
                    mark_times=[(pd.Timestamp(r['time'])-pd.Timestamp('2024-05-20T20:10:03Z')).total_seconds() for r in saved_marks if r['model']==model and r['phase']==phase]
                else:
                    inds,_=find_peaks(np.nan_to_num(yy),height=.3,distance=50);mark_times=tt[inds]
                for mark in mark_times:ax.axvline(mark,color=linecolor,ls='--',lw=.5,alpha=.7)
            ax.set(ylim=(0,1),ylabel=model.capitalize());ax.legend(fontsize=6,ncol=2,loc='upper right')
        axes[-1].set(xlim=(t.min(),t.max()),xlabel='Time from saved window start (s)')
        title='S4A · Partial independent inference; exact published alignment unverified' if current else 'Reproduction diagnostic: separate calendar window, not S4'
        fig.suptitle(title+'\nSpectrogram: normalized-count²/Hz, −80 to 0 dB (under white / over black); paper scale unspecified.',fontsize=9)
        save(fig,name,[file,str(target.relative_to(ROOT))]+(['data/continuation/figure_S4A_picks.json'] if current else []),panel,'S4 blue P/orange S; teal/red own saved pick marks for S4A, score-peak indicators for separate diagnostics. Spectral limits undisclosed in paper; explicit own normalization. No published reference annotations.',png=True)

def magnitudes(extension=False,source_override=None):
    source=ROOT/'data/grid_calibration/merged4/magnitude' if (ROOT/'data/grid_calibration/merged4/magnitude/magnitude_statistics.json').exists() else D
    if extension:source=ROOT/'data/coverage_extension/calibration/merged4/magnitude'
    if source_override:source=ROOT/source_override
    a=pd.read_csv(source/'figure_S8A.csv');h=pd.read_csv(source/'figure_S8B.csv');stat=json.loads((source/'magnitude_statistics.json').read_text());fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    axes[0].scatter(a.Md,a.ML,c='blue',s=3,linewidths=0);axes[0].set(xlabel=r'Duration magnitude $M_d$',ylabel=r'Provisional local magnitude $M_L$',title='A · Calibration matches')
    axes[1].bar(h.ML_bin,h['count'],width=.09,color='#1f77b4',lw=0);axes[1].plot(h.ML_bin,h.cumulative,'.',ms=2,c='#1f77b4');axes[1].set(yscale='log',xlabel=r'Provisional magnitude $M_L$',ylabel='Number of events',title='B · Incomplete sample')
    if stat.get('b') is not None:
        xx=np.linspace(stat['Mc'],float(h.ML_bin.max()),100);yy=stat['events_ge_Mc']*10**(-stat['b']*(xx-stat['Mc']))
        target=source/'conditional_GR_display.csv' if source_override else OUT/('conditional_GR_extension.csv' if extension else 'conditional_GR_display.csv')
        pd.DataFrame(dict(ML=xx,expected_count=yy)).to_csv(target,index=False)
        axes[1].plot(xx,yy,c='#ff7f0e',lw=1,label=f"Conditional b={stat['b']:.2f} ± {stat['b_sigma']:.2f}")
        axes[1].scatter([stat['Mc']],[stat['events_ge_Mc']],c='#ff7f0e',s=30);axes[1].legend(fontsize=8)
    if len(a)>2:
        fit=np.polyfit(a.Md,a.ML,1);xx=np.array([a.Md.min(),a.Md.max()]);axes[0].plot(xx,np.polyval(fit,xx),color='red',lw=.8)
    fig.suptitle(f'S8 · Partial; {stat["magnitudes"]} magnitudes. Routine Md is calibration input, not validation.',fontsize=9)
    save(fig,'figure_S8_local_followup' if source_override else 'figure_S8_extension' if extension else 'figure_S8_pilot',[str((source/x).relative_to(ROOT)) for x in ['figure_S8A.csv','figure_S8B.csv','magnitude_statistics.json']],'S8A–B','Blue small dots, red own calibration fit, histogram and orange own conditional likelihood curve; full observed axes. Formal errors retained in source table.')

def hybrids():
    for event in ['E1','E2','E3']:
        path='data/observations/'+event+'_waveforms.csv';x=pd.read_csv(ROOT/path);inputs=[path];fig,axes=plt.subplots(2,4,figsize=(12,2.9),sharex='col',gridspec_kw={'height_ratios':[1,1]},layout='constrained')
        for k,(sta,comp) in enumerate([(s,c) for s in ['CAAM','COLB'] for c in ['Z','E']]):
            g=x[(x.station==sta)&(x.component==comp)];axes[0,k].plot(g.time_s,g.normalized,color='black',lw=.55,label=sta+' HH'+comp);axes[0,k].legend(fontsize=6);axes[0,k].set_yticks([])
            file=f'data/observations/{event}_{sta}_{comp}_spectrum.npz';inputs.append(file);a=np.load(ROOT/file);f=a['frequency'];keep=(f>=1)&(f<=20);values=10*np.log10(np.maximum(a['power'][keep],np.finfo(float).tiny))
            axes[1,k].pcolormesh(a['time'],f[keep],values,cmap=spectral_cmap('gist_rainbow_r',values,event+' '+sta+comp),vmin=-80,vmax=0,shading='auto',rasterized=True);axes[1,k].set(yscale='log',ylim=(1,20),xlabel='Time from written template (s)',ylabel='Hz' if k==0 else '',xlim=(g.time_s.min(),g.time_s.max()))
        label={'E1':'S15A analogue · E1 template, different event','E2':'S15B analogue · E2 template, different event','E3':'S15C · Partial'}[event]
        fig.suptitle(label+'; normalized spectra −80…0 dB; paper scale unspecified.',fontsize=8)
        save(fig,'hybrid_'+event,inputs,{'E1':'S15A analogue','E2':'S15B analogue','E3':'S15C'}[event],'Four component columns, waveforms above log-frequency spectra. E1/E2 are alternative documented family templates, not the published example events. Closest visible rainbow palette; exact palette/normalization not published. Observed window is not truncated to force reference onset.',png=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True);theme();contextual();coverage();station_map();picking();magnitudes();hybrids()
    diagnostics()
    grid_diagnostic()
    if (ROOT/'data/grid_calibration/merged4/panels/summary.json').exists():
        from grid_publication_panels import generate
        import sys
        generate(sys.modules[__name__])
        if (ROOT/'data/coverage_extension/calibration/merged4/panels/velest.csv').exists():
            generate(sys.modules[__name__],extension=True)
            if (ROOT/'data/coverage_extension/calibration/merged4/magnitude/magnitude_statistics.json').exists():magnitudes(extension=True)
    (OUT/'plot_inventory.json').write_text(json.dumps(RECORD,indent=2)+'\n')
    (OUT/'spectral_scales.json').write_text(json.dumps(SPECTRAL,indent=2)+'\n')
    print('Regenerated',len(RECORD),'current figure groups from saved data.')

# Diagnostic-only renderers follow; no new scientific selection or processing.
def diagnostics():
    colors=['#1f77b4','#ff7f0e','#2ca02c','#d62728']
    x=pd.read_csv(D/'sp_consistency.csv');fig,ax=plt.subplots(figsize=(5,4),layout='constrained');ax.scatter(x.observed_sp_s,x.calculated_sp_s,s=4,c='blue',alpha=.4,linewidths=0);lo=min(x.observed_sp_s.min(),x.calculated_sp_s.min());hi=max(x.observed_sp_s.max(),x.calculated_sp_s.max());ax.plot([lo,hi],[lo,hi],c='.4',lw=.7);ax.set(xlabel='Observed S–P (s)',ylabel='Initial-model S–P (s)',title='Reproduction diagnostic: unreviewed S–P consistency');save(fig,'continuation_sp_diagnostic',['data/continuation/sp_consistency.csv'],'diagnostic',png=True)
    x=pd.read_csv(ROOT/'data/observations/hourly_counts.csv');x['station']=x.source.str.extract(r'day_(\w+)_');x['hour']=x.source.str.extract(r'_(\d\d)\.mseed').astype(int);fig,ax=plt.subplots(figsize=(8,3),layout='constrained')
    for (sta,g),color in zip(x.groupby('station'),colors):ax.step(g.hour,g.picks,where='mid',color=color,label=sta)
    ax.set(xlabel='UTC hour on 1 January 2024',ylabel='Phase picks',title='Reproduction diagnostic: one-day inference');ax.legend(ncol=4,fontsize=8);save(fig,'independent_picks',['data/observations/hourly_counts.csv'],'diagnostic',png=True)
    x=pd.read_csv(ROOT/'data/calibration_followup/convergence_plot.csv');fig,aa=plt.subplots(1,2,figsize=(8,3),layout='constrained')
    for ax,col,label in zip(aa,['max_horizontal_move_m','event_rms_aggregate_s'],['Maximum horizontal change (m)','Event RMS aggregate (s)']):ax.plot(x.extra_pass,x[col],'.-',c='blue',ms=4);ax.set(xlabel='Extra calibration pass',ylabel=label)
    fig.suptitle('Reproduction diagnostic: superseded alternative-model calibration',fontsize=10);save(fig,'calibration_convergence_diagnostic',['data/calibration_followup/convergence_plot.csv'],'diagnostic')
    x=pd.read_csv(ROOT/'data/calibration_followup/svd_diagnostic_plot.csv');fig,aa=plt.subplots(1,3,figsize=(10,3),layout='constrained')
    for ax,col,label in zip(aa,['error_x_m','error_y_m','error_z_m'],['Easting','Northing','Depth']):
        for (region,g),color in zip(x.groupby('region'),['red','green','blue']):ax.scatter(g.cc_count,g[col],c=color,s=7,label=region,linewidths=0)
        ax.set(xscale='symlog',yscale='log',xlabel='Waveform-delay count',ylabel=label+' conditional 95% error (m)');ax.legend(fontsize=7)
    fig.suptitle('Reproduction diagnostic: prior alternative-model SVD; not S7 or absolute accuracy',fontsize=10);save(fig,'relocation_uncertainty_diagnostic',['data/calibration_followup/svd_diagnostic_plot.csv'],'diagnostic')
    x=pd.read_csv(D/'cpoz_gather_index.csv');arrays=np.load(D/'cpoz_gathers.npz');fig,aa=plt.subplots(1,2,figsize=(8,8),layout='constrained')
    for ax,channel in zip(aa,['HHZ','HHN']):
        g=x[x.channel==channel]
        for i,r in enumerate(g.itertuples()):t,y=arrays[r.array_key];ax.plot(t,y*.4+i,c='blue',lw=.3)
        ax.axvline(0,c='.5',ls='--',lw=.6);ax.set(xlabel='Time from own P pick (s)',ylabel='Chronological event index',title='CPOZ '+channel,xlim=(-1,7))
    fig.suptitle('Reproduction diagnostic: unreviewed arrivals; no relocated sector selection',fontsize=10);save(fig,'cpoz_gather_diagnostic',['data/continuation/cpoz_gather_index.csv','data/continuation/cpoz_gathers.npz'],'diagnostic')
    inp=['data/extended/hybrid_review_waveforms.csv','data/extended/hybrid_review_metrics.csv'];x=pd.read_csv(ROOT/inp[0]);m=pd.read_csv(ROOT/inp[1]);fig,aa=plt.subplots(len(m),1,figsize=(8,2*len(m)),layout='constrained',squeeze=False)
    for ax,r in zip(aa[:,0],m.itertuples()):
        for (sta,g),color in zip(x[x.candidate==r.candidate].groupby('station'),colors):ax.plot(g.time_s,g.velocity_m_s*1e6,color=color,label=sta)
        ax.set(title=f'Candidate {r.candidate}: {r.time}; unconfirmed',xlabel='Time (s)',ylabel='Velocity (µm/s)');ax.legend(fontsize=7)
    fig.suptitle('Reproduction diagnostic: threshold candidates, not confirmed hybrids',fontsize=10);save(fig,'hybrid_candidate_review',inp,'diagnostic',png=True)
    review=json.loads((D/'association_quality.json').read_text())['reviewed_examples'];inputs=['data/continuation/association_quality.json']
    with PdfPages(F/'association_review_diagnostic.pdf') as pdf:
        for r in review:
            stem=f'data/continuation/association_review/event_{r["event_index"]}';inputs.extend([stem+'.npz',stem+'_picks.csv']);a=np.load(ROOT/(stem+'.npz'));p=pd.read_csv(ROOT/(stem+'_picks.csv'));fig,ax=plt.subplots(figsize=(9,6),layout='constrained');stations=sorted({v['trace_id'] for v in r['traces']})
            for tr in r['traces']:
                t,y=a[tr['key']];i=stations.index(tr['trace_id']);color={'Z':'black','N':'#1f77b4','E':'.6'}.get(tr['channel'][-1],'black');ax.plot(t,y*.35+i,c=color,lw=.4)
            for row in p.itertuples():ax.plot([row.seconds_from_origin]*2,[stations.index(row.trace_id)-.4,stations.index(row.trace_id)+.4],c='red' if row.phase=='P' else 'green',lw=.7)
            ax.set_yticks(range(len(stations)),stations,fontsize=7);ax.set(xlabel='Time from provisional origin (s)',title=f'Reproduction diagnostic: event {r["event_index"]}; {r["category"]}');pdf.savefig(fig);plt.close(fig)
    register('association_review_diagnostic',inputs,'diagnostic','Saved normalized observations with own associated pick marks; not an accepted event solution.')
    arrays=np.load(D/'catalog_frequency_review.npz');rows=pd.DataFrame(json.loads((D/'catalog_frequency_review_index.json').read_text()))
    with PdfPages(F/'catalog_frequency_review_diagnostic.pdf') as pdf:
        for eid,g in rows.groupby('event_index'):
            fig,aa=plt.subplots(len(g),2,figsize=(9,2*len(g)+1),layout='constrained',squeeze=False)
            for axes,r in zip(aa,g.itertuples()):
                a=arrays[r.key]
                for ax,j in zip(axes,[1,2]):
                    ax.plot(a[0],a[j]*1e6,c='black',lw=.45);ax.axvspan(0,8,color='.85',zorder=-1);ax.axvline(0,c='red',ls='--',lw=.5)
                    for t in r.other_provisional_arrivals_s:ax.axvline(t,c='blue',ls=':',lw=.5)
                    ax.set(xlabel='Time from own alignment (s)',ylabel='Velocity (µm/s)',title=r.station+(' raw Z' if j==1 else ' 0.2–6 Hz'))
            fig.suptitle(f'Reproduction diagnostic: low-frequency candidate {eid}; coda unexcluded',fontsize=10);pdf.savefig(fig);plt.close(fig)
    register('catalog_frequency_review_diagnostic',['data/continuation/catalog_frequency_review.npz','data/continuation/catalog_frequency_review_index.json'],'diagnostic','Saved low-frequency reviews, no confirmed hybrid classification.')
    x=pd.read_csv(D/'hybrid_review_windows.csv');a=np.load(D/'hybrid_review_windows.npz')
    with PdfPages(F/'hybrid_review_diagnostic.pdf') as pdf:
        for eid,g in x.groupby('candidate'):
            fig,aa=plt.subplots(3,1,figsize=(9,6),layout='constrained')
            for ax,component in zip(aa,['Z','E','N']):
                for r,color in zip(g[g.component==component].itertuples(),colors):w=a[r.key];ax.plot(w[0],w[1]*1e6,c=color,label=r.station+' '+component,lw=.5)
                ax.axvspan(0,8,color='.85',zorder=-1);ax.set(xlabel='Time from template alignment (s)',ylabel='Velocity (µm/s)');ax.legend(fontsize=7)
            fig.suptitle(f'Reproduction diagnostic: candidate {eid}; not confirmed hybrid',fontsize=10);pdf.savefig(fig);plt.close(fig)
    register('hybrid_review_diagnostic',['data/continuation/hybrid_review_windows.csv','data/continuation/hybrid_review_windows.npz'],'diagnostic','Saved measured velocities; gray spectral window, no confirmed classification.')

def grid_diagnostic():
    folder='data/grid_calibration/merged4/';s=json.loads((ROOT/folder/'summary.json').read_text());region=s['lowest_converged_phase_RMS_region']
    model=folder+region+'_convergence3_model.csv';starts=folder+'starting_profiles.csv';m=pd.read_csv(ROOT/model);a=pd.read_csv(ROOT/starts);a=a[a.region==region]
    first=folder+'tomodd/round1_locations.csv';second=folder+'tomodd/round2_locations.csv'
    if not (ROOT/second).exists():return
    b=pd.read_csv(ROOT/second);c=pd.read_csv(ROOT/first).merge(b,on='event_index',suffixes=('_1','_2'))
    from pyproj import Transformer
    tr=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True);x,y=tr.transform(b.longitude,b.latitude)
    fig,aa=plt.subplots(1,3,figsize=(11,3.7),layout='constrained')
    for phase,color in [('Vp','red'),('Vs','blue')]:
        for table,linestyle,label in [(a,'--',' start'),(m,'-',' fit')]:
            depths=np.column_stack([table.layer_top_km,np.r_[table.layer_top_km.to_numpy()[1:],7.]]).ravel()
            aa[0].plot(np.repeat(table[phase+'_km_s'],2),depths,c=color,ls=linestyle,label=phase+label)
    aa[0].set(xlabel='Velocity (km/s)',ylabel='Layer top depth (km)',ylim=(7,-.5));aa[0].legend(fontsize=7)
    from matplotlib.colors import Normalize
    pts=aa[1].scatter(x,y,c=b.depth_km,cmap=style.depth_cmap(),norm=Normalize(0,5,clip=False),s=6);aa[1].set(xlabel='Easting (km)',ylabel='Northing (km)',aspect='equal');cb=fig.colorbar(pts,ax=aa[1],extend='max',ticks=range(6));cb.set_label('Depth (km); magenta >5');cb.ax.invert_yaxis()
    aa[2].scatter(c.depth_km_1,c.depth_km_2,s=6,c='blue');hi=max(c.depth_km_1.max(),c.depth_km_2.max());aa[2].plot([0,hi],[0,hi],c='.5',lw=.6);aa[2].set(xlabel='Round 1 depth (km)',ylabel='Round 2 depth (km)')
    fig.suptitle('Reproduction diagnostic: grid-derived trial; calibration path-sensitive, locations unvalidated',fontsize=10)
    save(fig,'grid_calibration_diagnostic',[model,starts,first,second],'diagnostic','Own numerical experiments, not S6/Figure 3. Fixed depth colors 0–5 km; all points retained, >5 magenta. No magnitude sizing because accepted magnitudes are unavailable.')

if __name__=='__main__':main()
