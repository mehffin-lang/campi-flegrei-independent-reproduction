"""Save P-aligned own CPOZ observations as a reproduction diagnostic.

No author picks, depths or sectors; no claim to reproduce S12 ring sectors.
"""
from pathlib import Path
import json,os
ROOT=Path(__file__).resolve().parents[1];os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np
import pandas as pd
from obspy import read,UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=ROOT/'data/continuation'

def main():
    picks=pd.read_csv(D/'picks.csv');assign=pd.read_csv(D/'associations.csv');events=pd.read_csv(D/'initial_events.csv').set_index('event_index')
    selected=assign.merge(picks,left_on='pick_index',right_index=True)
    selected=selected[(selected.trace_id.str.split('.').str[1]=='CPOZ')&(selected.phase=='P')].copy()
    rows=[];gathers=[];errors=[]
    for file,group in selected.groupby('source'):
        stream=read(str(ROOT/file)).select(component='Z').merge(method=0).split()
        for r in group.itertuples():
            t=UTCDateTime(r.time)
            try:
                st=stream.slice(t-2,t+6).copy()
                if len(st)!=1 or st[0].stats.starttime>t-1.9 or st[0].stats.endtime<t+5.9:raise ValueError('Incomplete gap-free gather')
                st.detrend('demean');st.filter('bandpass',freqmin=1,freqmax=15,corners=4,zerophase=False)
                tr=st[0];amplitude=np.max(abs(tr.data))
                if amplitude==0:raise ValueError('Zero waveform')
                time=tr.times()+float(tr.stats.starttime-t);values=tr.data/amplitude
                gathers.append((int(r.event_index),time,values))
                rows.append(dict(event_index=int(r.event_index),p_time=r.time,source=file,normalizer_counts=float(amplitude),initial_depth_km=float(events.loc[r.event_index,'z(km)']),status='unreviewed provisional association; no relocated sector'))
            except Exception as e:errors.append(dict(event_index=int(r.event_index),source=file,error=repr(e)))
    pd.DataFrame(rows).to_csv(D/'cpoz_gather_index.csv',index=False)
    np.savez_compressed(D/'cpoz_gathers.npz',**{f'e{eid}':np.vstack([t,y]) for eid,t,y in gathers})
    # Plot only the saved normalized traces, with no sector or depth inference.
    saved=np.load(D/'cpoz_gathers.npz');fig,ax=plt.subplots(figsize=(8,6))
    for i,key in enumerate(saved.files):t,y=saved[key];ax.plot(t,i+.4*y,lw=.35,color='#176b9a')
    ax.axvline(0,color='.4',ls=':',lw=.6);ax.set(xlabel='Time from independently picked P (s)',ylabel='Provisional event index in gather',
        title=f'Reproduction diagnostic: {len(saved.files)} CPOZ gathers\nUnreviewed arrivals; not the S12 relocated-sector test')
    fig.tight_layout();fig.savefig(ROOT/'figures/cpoz_gather_diagnostic.pdf');plt.close(fig)
    summary=dict(associated_picks=len(selected),gathers=len(gathers),failures=errors,relocated_sector_gathers=0,
                 status='Reproduction diagnostic only; initial depths are not accepted locations. Manual polarity, onset and suspicious-depth reviews remain incomplete.')
    (D/'cpoz_gather_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
