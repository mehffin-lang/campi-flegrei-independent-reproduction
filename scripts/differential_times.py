"""Exploratory waveform differential times from independently picked observations.

The paper specifies neighboring events and coherence-weighted measurements but
not windows, neighbor count, spectral estimation or cutoffs. Those choices below
are explicit pilot assumptions, not recovered author settings. No relocation is
claimed and no unverified background model or published event list is read.
"""
from pathlib import Path
import os,json,concurrent.futures,multiprocessing
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
import numpy as np
import pandas as pd
from scipy.signal import correlate,correlation_lags,welch,csd
from scipy.spatial import cKDTree
from obspy import read,read_inventory,UTCDateTime
D=ROOT/'data/continuation'
SETTINGS=dict(neighbors=10,window_s=[-.25,1.75],sample_rate_hz=100,max_lag_s=.25,
              frequency_band_hz=[1,15],welch_nperseg=64,welch_noverlap=32,
              minimum_correlation=.6,minimum_mean_coherence=.6)


def delay(x,y,fs=100):
    """Return delay of y relative to x; positive means y arrives later.

    Integer correlation alignment precedes a weighted, through-origin fit
    -arg(Sxy)=2*pi*f*delta. Weight gamma^2/(1-gamma^2) approximates inverse
    cross-spectral phase variance for averaged periodograms. The returned
    observation weight is mean magnitude-squared coherence in the fitted band.
    """
    x=np.asarray(x,float)-np.mean(x);y=np.asarray(y,float)-np.mean(y)
    norm=np.linalg.norm(x)*np.linalg.norm(y)
    if norm==0:raise ValueError('Zero signal norm')
    lags=correlation_lags(len(y),len(x));corr=correlate(y,x)/norm
    keep=np.abs(lags)<=round(fs*SETTINGS['max_lag_s']);lags=lags[keep];corr=corr[keep]
    k=int(np.argmax(corr));lag=int(lags[k])
    if lag>0:xx,yy=x[:-lag],y[lag:]
    elif lag<0:xx,yy=x[-lag:],y[:lag]
    else:xx,yy=x,y
    args=dict(fs=fs,nperseg=64,noverlap=32,detrend='constant',window='hann')
    f,px=welch(xx,**args);_,py=welch(yy,**args);_,cross=csd(xx,yy,**args)
    coherence=np.clip(np.abs(cross)**2/np.maximum(px*py,np.finfo(float).tiny),0,1)
    band=(f>=1)&(f<=15);omega=2*np.pi*f[band]
    phase=-np.unwrap(np.angle(cross[band]));g=coherence[band]
    weight=g/np.maximum(1-g,1e-6);den=float(np.sum(weight*omega**2))
    if den<=0:raise ValueError('No spectral information')
    residual=float(np.sum(weight*omega*phase)/den)
    result=dict(delay_y_minus_x_s=lag/fs+residual,integer_lag_s=lag/fs,
                residual_delay_s=residual,correlation=float(corr[k]),mean_coherence=float(g.mean()),
                at_search_boundary=bool(k==0 or k==len(corr)-1))
    result['measurement_pass']=bool(corr[k]>=.6 and g.mean()>=.6 and not result['at_search_boundary'] and abs(residual)<=1/fs)
    return result


def windows(job):
    source,rows=job;st=read(str(ROOT/source)).merge(method=0).split();out={};errors=[];inventories={}
    for r in rows:
        t=UTCDateTime(r['time']);net,sta,loc=r['trace_id'].split('.')
        for component in (['Z'] if r['phase']=='P' else ['N','E']):
            try:
                traces=st.select(network=net,station=sta,location=loc,component=component).slice(t-10,t+10).copy()
                if len(traces)!=1:raise ValueError('Missing or gapped component')
                tr=traces[0];fs=tr.stats.sampling_rate
                if fs!=100 or tr.stats.starttime>t-2 or tr.stats.endtime<t+3:raise ValueError('Insufficient context or sample rate')
                if net not in inventories:inventories[net]=read_inventory(str(ROOT/f'inputs/continuation/{net}_responses.xml'))
                traces.detrend('demean');traces.remove_response(inventory=inventories[net],output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                traces.filter('bandpass',freqmin=1,freqmax=15,corners=4,zerophase=False)
                tr.trim(t-.25,t+1.75-1/fs)
                if len(tr)!=200:raise ValueError('Incomplete 2-second window')
                out[(int(r['event_index']),r['trace_id'],r['phase'],component)]=tr.data.astype(float)
            except Exception as exc:errors.append(dict(pick_index=int(r['pick_index']),component=component,error=repr(exc),source=source))
    return out,errors


def main():
    quality=pd.read_csv(D/'association_quality.csv')
    # This is a pilot event set. Causality is necessary but not sufficient for
    # correct association; depth-bound hits are excluded from the neighbor graph.
    allowed=quality.loc[quality.passes_causality & ~quality.depth_boundary,'event_index']
    events=pd.read_csv(D/'initial_events.csv').set_index('event_index').loc[allowed].sort_index()
    picks=pd.read_csv(D/'picks.csv');assigned=pd.read_csv(D/'associations.csv').merge(picks,left_on='pick_index',right_index=True)
    assigned=assigned[assigned.event_index.isin(events.index)]
    assert not assigned[['event_index','trace_id','phase']].duplicated().any(), 'Ambiguous repeated phase at one event/station; review before measuring differential times'
    observations={};errors=[]
    jobs=[(source,g.to_dict('records')) for source,g in assigned.groupby('source')]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('spawn')) as pool:
        for wave,failed in pool.map(windows,jobs):observations.update(wave);errors.extend(failed)
    arrays={f'e{e}_{station}_{phase}_{comp}':v for (e,station,phase,comp),v in observations.items()}
    np.savez_compressed(D/'differential_waveform_windows.npz',**arrays)
    assigned.to_csv(D/'differential_window_picks.csv',index=False)
    xyz=events[['x(km)','y(km)','z(km)']].to_numpy();ids=events.index.to_numpy()
    tree=cKDTree(xyz);_,neighbors=tree.query(xyz,k=min(len(xyz),11));pairs=set()
    for i,row in enumerate(neighbors):
        for j in np.atleast_1d(row):
            if i!=j:pairs.add(tuple(sorted([int(ids[i]),int(ids[j])])))
    pickmap={(int(r.event_index),r.trace_id,r.phase):r for r in assigned.itertuples()}
    keys={eid:{(sta,phase,comp) for e,sta,phase,comp in observations if e==eid} for eid in ids}
    rows=[]
    # Calculations consume the saved waveform windows.
    with np.load(D/'differential_waveform_windows.npz') as saved:
        for a,b in sorted(pairs):
            for sta,phase,comp in sorted(keys[a]&keys[b]):
                pa,pb=pickmap[a,sta,phase],pickmap[b,sta,phase]
                try:
                    result=delay(saved[f'e{a}_{sta}_{phase}_{comp}'],saved[f'e{b}_{sta}_{phase}_{comp}'])
                    pick_dt=(UTCDateTime(pa.time)-UTCDateTime(events.loc[a,'time']))-(UTCDateTime(pb.time)-UTCDateTime(events.loc[b,'time']))
                    rows.append(dict(event_a=a,event_b=b,station=sta,phase=phase,component=comp,
                        picked_differential_time_s=float(pick_dt),differential_time_s=float(pick_dt-result['delay_y_minus_x_s']),
                        source_a=pa.source,source_b=pb.source,**result))
                except Exception as exc:errors.append(dict(event_a=a,event_b=b,station=sta,phase=phase,component=comp,error=repr(exc)))
    table=pd.DataFrame(rows);table.to_csv(D/'differential_times.csv',index=False)
    pd.DataFrame(errors).to_csv(D/'differential_time_failures.csv',index=False)
    summary=dict(events=len(events),neighbor_pairs=len(pairs),saved_waveform_windows=len(observations),
        measured_channel_pairs=len(table),passing_measurements=int(table.measurement_pass.sum()) if len(table) else 0,
        failures=len(errors),settings=SETTINGS,accepted_relocated_events=0,
        provenance='Own phase picks, own provisional alternative-model positions, original recordings and official instrument responses. No author products or routine catalog.',
        limitations='Exploratory timing measurements only. Unreviewed phases and initial neighbor geometry remain uncertain. Tan does not specify the window, neighbor count, frequency estimation, coherence or lag thresholds used here. The fixed 2008 grid remains unverified; neither TomoDD round nor HypoDD uncertainties are produced.')
    both=table[(table.phase=='S') & table.measurement_pass].pivot(index=['event_a','event_b','station'],columns='component',values='delay_y_minus_x_s')
    if {'N','E'}<=set(both.columns):
        difference=(both.N-both.E).dropna().abs()
        summary['horizontal_component_consistency']=dict(pairs=len(difference),median_difference_s=float(difference.median()) if len(difference) else None,maximum_difference_s=float(difference.max()) if len(difference) else None,
            interpretation='Agreement of two measured component delays, not absolute timing accuracy or location uncertainty.')
    (D/'differential_times.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)


if __name__=='__main__':main()
