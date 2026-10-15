"""Diagnose saved calendar holdout residuals and display original arrival windows.

No arrival is changed. Raw-window displays are reproduction diagnostics, not
paper figures. The held-out 2025 observations remain excluded from fitting.
"""
import json, hashlib, re
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read, UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import validate_observational_profile as vr

R=Path(__file__).resolve().parents[1]
C=R/'data/availability_extension/catalog_december'
V=R/'data/availability_extension/velocity_december'
D=R/'data/velocity_holdout_review'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    D.mkdir(exist_ok=True); (D/'review').mkdir(exist_ok=True)
    vr.W=R/'tmp/availability_extension/velocity_december'
    events=pd.read_csv(V/'event_roles.csv').sort_values('time')
    picks=pd.read_csv(C/'picks.csv'); assoc=pd.read_csv(C/'associations.csv')
    aliases=pd.read_csv(V/'station_aliases.csv').set_index('alias').id
    paired=[]
    for role,name,subset in [('training','base_convergence3',events[events.role.eq('balanced training')]),
                             ('holdout','base_holdout_fitted',events[events.role.eq('2025 holdout')])]:
        rows=vr.residuals(name); rows['event_index']=rows.event_ordinal.map(dict(enumerate(subset.event_index)))
        rows['station']=rows.alias.map(aliases)
        ap=assoc[assoc.event_index.isin(subset.event_index)].copy()
        ap=ap.join(picks,on='pick_index');ap=ap.rename(columns={'trace_id':'station'})
        rows=rows.merge(ap,on=['event_index','station','phase'],validate='one_to_one')
        rows['role']=role;paired.append(rows)
    allrows=pd.concat(paired,ignore_index=True)
    allrows.to_csv(D/'saved_residual_arrivals.csv',index=False)
    stats=[]
    for trial in ['base','all_training']:
        g=pd.read_csv(V/(trial+'_holdout_paired_residuals.csv'))
        total=float((g.fitted_residual_s**2-g.residual_s**2).sum())
        for label,mask in [('represented',g.training_phase_count.gt(0)),('unrepresented',g.training_phase_count.eq(0))]:
            q=g[mask]; delta=float((q.fitted_residual_s**2-q.residual_s**2).sum())
            stats.append(dict(trial=trial,support=label,arrivals=len(q),pairs=len(q[['station','phase']].drop_duplicates()),initial_rms_s=float(np.sqrt(np.mean(q.residual_s**2))),fitted_rms_s=float(np.sqrt(np.mean(q.fitted_residual_s**2))),extra_squared_residual_s2=delta,fraction_of_net_deterioration=delta/total))
    pd.DataFrame(stats).to_csv(D/'old_holdout_decomposition.csv',index=False)
    support=[]
    for (station,phase),q in allrows.groupby(['station','phase']):
        support.append(dict(station=station,phase=phase,training=int(q.role.eq('training').sum()),holdout=int(q.role.eq('holdout').sum())))
    pd.DataFrame(support).to_csv(D/'old_support.csv',index=False)
    # Display largest absolute residuals in both phases and sets; diagnostic
    # review only, never screen holdout observations by their model residual.
    choices=allrows.assign(abs_residual=allrows.residual_s.abs()).sort_values('abs_residual',ascending=False).groupby(['role','phase'],sort=True).head(6)
    choices=choices.sort_values(['role','phase','abs_residual'],ascending=[True,True,False]).reset_index(drop=True)
    windows={};review=[];sources={}
    for i,row in choices.iterrows():
        t=UTCDateTime(row.time);other=allrows[(allrows.event_index==row.event_index)&(allrows.station==row.station)]
        offsets={r.phase:UTCDateTime(r.time)-t for r in other.itertuples()}
        start=min(-1.5,min(offsets.values())-1);end=max(2,max(offsets.values())+1)
        item=row.to_dict();item.update(review_id=int(i),associated_phase_offsets_s=offsets)
        path=R/row.source
        try:
            st=read(str(path),starttime=t+start,endtime=t+end)
            item['trace_ids']=[];item['sampling_hz']=[];item['gaps']=st.get_gaps()
            for tr in st:
                if np.ma.isMaskedArray(tr.data) and np.ma.getmaskarray(tr.data).any():continue
                tr.detrend('linear');raw=tr.data.copy();tr.filter('bandpass',freqmin=1,freqmax=min(20,tr.stats.sampling_rate*.4),zerophase=True,corners=2)
                tm=tr.times()+float(tr.stats.starttime-t)
                key=f'w{i}_{len(item["trace_ids"])}';windows[key]=np.vstack([tm,raw,tr.data])
                item['trace_ids'].append(tr.id);item['sampling_hz'].append(float(tr.stats.sampling_rate))
            item['window_available']=bool(item['trace_ids']);sources[row.source]=sha(path)
        except Exception as exc:item.update(window_available=False,error=str(exc))
        review.append(item)
    np.savez_compressed(D/'review/windows.npz',**windows)
    dump(D/'review/window_index.json',review)
    for page in range((len(review)+5)//6):
        fig,axes=plt.subplots(3,2,figsize=(13,10),layout='constrained')
        for ax,item in zip(axes.flat,review[page*6:(page+1)*6]):
            i=item['review_id']
            for j,trace in enumerate(item.get('trace_ids',[])):
                x,raw,y=windows[f'w{i}_{j}'];scale=max(np.max(abs(y)),1e-20)
                ax.plot(x,raw/max(np.max(abs(raw)),1e-20)+j*2.3,color='.75',lw=.5)
                ax.plot(x,y/scale+j*2.3,color='black',lw=.6);ax.text(x[0],j*2.3+.8,trace,fontsize=7)
            for phase,off in item['associated_phase_offsets_s'].items():ax.axvline(off,color='#0072b2' if phase=='P' else '#d55e00',label=phase,lw=1)
            ax.set_title(f"{i}: {item['role']} e{item['event_index']} {item['station']} {item['phase']}\nr={item['residual_s']:.3f}s; score={item['probability']:.2f}",fontsize=9)
            ax.set_xlabel('Seconds from tested pick; P blue, S orange');ax.set_yticks([])
        fig.suptitle('Reproduction diagnostic: original arrival windows; gray raw, black 1–20 Hz')
        fig.savefig(D/f'review/windows_{page+1}.png',dpi=150);plt.close(fig)
    dump(D/'diagnosis_inputs.json',dict(inputs={str(p.relative_to(R)):sha(p) for p in [C/'picks.csv',C/'associations.csv',C/'stations.csv',V/'event_roles.csv',V/'summary.json']},waveforms=sources,review_count=len(review),holdout_unchanged=True,background_coordination='Stopped automatic model/report watcher PID 3325726 to prevent competing report writes. Existing waveform collector and incremental picker remain active; no new files enter this frozen experiment.'))
    print(pd.DataFrame(stats).to_string(index=False));print('Review windows:',len(review))

if __name__=='__main__':main()
