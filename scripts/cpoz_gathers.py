"""Observed CPOZ HHZ/HHN gathers with the written S12 window and filter.

These remain diagnostics: the required independently relocated sectors and
reviewed onsets are not available. No author picks, depths or sectors are used.
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
    rows=[];gathers={};errors=[]
    for file,group in selected.groupby('source'):
        stream=read(str(ROOT/file)).select(station='CPOZ').merge(method=0).split()
        for r in group.itertuples():
            t=UTCDateTime(r.time)
            for channel in ['HHZ','HHN']:
                try:
                    st=stream.select(channel=channel).slice(t-16,t+22).copy()
                    if len(st)!=1:raise ValueError('No single gap-free component')
                    tr=st[0];fs=tr.stats.sampling_rate
                    if tr.stats.starttime>t-1 or tr.stats.endtime<t+7-1/fs:raise ValueError('Incomplete gather')
                    # Filter with surrounding observations before taking the 8 s
                    # published window. Order/causality are disclosed assumptions.
                    st.detrend('demean');st.filter('highpass',freq=4,corners=4,zerophase=False)
                    tr.trim(t-1,t+7-1/fs)
                    if len(tr)!=round(8*fs):raise ValueError('Unexpected sample count')
                    amplitude=np.max(abs(tr.data))
                    if amplitude==0:raise ValueError('Zero waveform')
                    key=f'e{int(r.event_index)}_{channel}'
                    gathers[key]=np.vstack([tr.times()+float(tr.stats.starttime-t),tr.data/amplitude])
                    rows.append(dict(event_index=int(r.event_index),channel=channel,array_key=key,p_time=r.time,source=file,
                        normalizer_counts=float(amplitude),samples=len(tr),sample_rate_hz=fs,
                        initial_depth_km=float(events.loc[r.event_index,'z(km)']),status='Unreviewed provisional association; no relocated sector'))
                except Exception as exc:errors.append(dict(event_index=int(r.event_index),channel=channel,source=file,error=repr(exc)))
    index=pd.DataFrame(rows);index.to_csv(D/'cpoz_gather_index.csv',index=False)
    np.savez_compressed(D/'cpoz_gathers.npz',**gathers)
    saved=np.load(D/'cpoz_gathers.npz');index=pd.read_csv(D/'cpoz_gather_index.csv')
    ids=sorted(index.event_index.unique());order={eid:i for i,eid in enumerate(ids)}
    fig,axes=plt.subplots(1,2,figsize=(10,7),sharey=True)
    for ax,channel in zip(axes,['HHZ','HHN']):
        for r in index[index.channel==channel].itertuples():
            t,y=saved[r.array_key];ax.plot(t,order[r.event_index]+.4*y,lw=.35,color='#176b9a')
        ax.axvline(0,color='.4',ls=':',lw=.6);ax.set(xlabel='Time from independently picked P (s)',title=channel+'; highpass >4 Hz',xlim=(-1,7))
    axes[0].set_ylabel('Provisional events, ordered by own origin time')
    fig.suptitle(f'Reproduction diagnostic: {len(ids)} CPOZ events, {len(index)} component traces\nUnreviewed arrivals; no S12 relocated-sector or coordinate ordering')
    fig.tight_layout();fig.savefig(ROOT/'figures/cpoz_gather_diagnostic.pdf');plt.close(fig)
    summary=dict(associated_picks=len(selected),gathers=len(ids),component_traces=len(index),failures=errors,relocated_sector_gathers=0,
        window_s=[-1,7],filter='4-Hz causal four-pole highpass, 15 s surrounding context when available',
        assumptions='Paper specifies >4 Hz and an 8 s -1/+7 window on HHZ/HHN, but not filter order/causality. Normalization is per trace. Time order replaces unavailable sector/coordinate order only in this explicitly labeled diagnostic.',
        status='Reproduction diagnostic only; initial depths are not accepted locations. Onset and suspicious-depth reviews remain incomplete.')
    (D/'cpoz_gather_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
