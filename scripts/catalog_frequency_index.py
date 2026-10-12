"""Frequency-index screening at all retrieved eligible vertical channels.

Incomplete observations and unreviewed onsets/coda prevent hybrid classification.
No source-paper event list, author pick or numerical figure data is read.
"""
from pathlib import Path
import json,os,concurrent.futures,multiprocessing
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2')
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
from gamma.seismic_ops import initialize_eikonal,calc_time
D=ROOT/'data/continuation'

def initialize_measurements(arrivals):
    global INVENTORIES,ARRIVALS
    INVENTORIES={net:read_inventory(str(ROOT/f'inputs/continuation/{net}_responses.xml')) for net in ['IV','2I']}
    ARRIVALS=arrivals

def measure_file(plan):
    file,jobs=plan;rows=[];failures=[]
    stream=read(str(ROOT/file)).select(component='Z').merge(method=0).split()
    for eid,station,channel,t,kind in jobs:
        try:
            st=stream.select(id=channel).slice(t-10,t+10).copy()
            if len(st)!=1:raise ValueError('Gap or overlapping channel segments')
            st.detrend('demean');st.remove_response(inventory=INVENTORIES[station.split('.')[0]],output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
            tr=st[0];fs=tr.stats.sampling_rate;x=tr.copy().trim(t,t+8-1/fs).data.astype(float);noise=tr.copy().trim(t-8,t-1/fs).data.astype(float)
            assert len(x)==round(8*fs) and len(noise)==len(x)
            x-=x.mean();noise-=noise.mean();f=np.fft.rfftfreq(len(x),1/fs);power=abs(np.fft.rfft(x))**2
            lo=power[(f>=2)&(f<=5)].sum();hi=power[(f>=8)&(f<=15)].sum()
            if min(lo,hi)<=0:raise ValueError('Zero spectral band power')
            preceding=[a for a in ARRIVALS[station] if 0<float(t)-a<8]
            rows.append(dict(event_index=eid,station=station,channel=channel,arrival=str(t),alignment=kind,source=file,FI=float(np.log10(hi/lo)),
                             power_SNR_dB=float(10*np.log10(np.mean(x*x)/max(np.mean(noise*noise),np.finfo(float).tiny))),
                             another_provisional_arrival_in_preceding_8s=bool(preceding),
                             reviewed=False,status='Spectral candidate only; onset and coda unreviewed'))
        except Exception as e:failures.append(dict(event_index=eid,station=station,source=file,error=repr(e)))
    return rows,failures

def main():
    events=pd.read_csv(D/'initial_events.csv');picks=pd.read_csv(D/'picks.csv');ass=pd.read_csv(D/'associations.csv')
    combined=ass.merge(picks,left_on='pick_index',right_index=True)
    pp=combined[combined.phase=='P'].sort_values('probability',ascending=False).drop_duplicates(['event_index','trace_id']).set_index(['event_index','trace_id'])
    stations=pd.read_csv(D/'stations.csv').set_index('id')
    config=json.loads((ROOT/'config/continuation_association.json').read_text());eik=initialize_eikonal(config['eikonal'])
    coverage=pd.read_csv(D/'processed_coverage.csv');coverage=coverage[coverage.channel.str.endswith('Z')].sort_values('file')
    coverage['station']=coverage.channel.str.rsplit('.',n=1).str[0]
    plans={};unavailable=[];rows=[];failures=[]
    for r in events.to_dict('records'):
        eid=int(r['event_index'])
        for station in sorted(set(coverage.station)&set(stations.index)):
            if (eid,station) in pp.index:arrival=UTCDateTime(pp.loc[(eid,station),'time']);kind='independent P pick'
            else:
                loc=np.array([[r['x(km)'],r['y(km)'],r['z(km)'],0.]])
                point=stations.loc[[station],['x(km)','y(km)','z(km)']].to_numpy()
                arrival=UTCDateTime(r['time'])+float(calc_time(loc,point,np.array(['p']),eikonal=eik)[0,0]);kind='alternative-profile predicted P'
            span=coverage[(coverage.station==station)&(coverage.start<=float(arrival)-10)&(coverage.end>=float(arrival)+10)]
            if span.empty:unavailable.append(dict(event_index=eid,station=station,reason='No retrieved gap-free Z span with 10 s margins'));continue
            plans.setdefault(span.iloc[0].file,[]).append((eid,station,span.iloc[0].channel,arrival,kind))
    arrivals={}
    for jobs in plans.values():
        for _,station,_,t,_ in jobs:arrivals.setdefault(station,[]).append(float(t))
    # Each process reads an original file once; ordered map preserves the same
    # numerical row order as serial evaluation. No shared waveform is mutated.
    with concurrent.futures.ProcessPoolExecutor(max_workers=6,mp_context=multiprocessing.get_context('spawn'),initializer=initialize_measurements,initargs=(arrivals,)) as pool:
        for measured,failed in pool.map(measure_file,plans.items()):rows.extend(measured);failures.extend(failed)
    table=pd.DataFrame(rows);table.to_csv(D/'catalog_frequency_index.csv',index=False)
    means=table.groupby('event_index').agg(mean_FI=('FI','mean'),stations=('station','nunique'),minimum_SNR_dB=('power_SNR_dB','min'),preceding_arrival_flag=('another_provisional_arrival_in_preceding_8s','max')).reset_index()
    means.to_csv(D/'catalog_frequency_index_events.csv',index=False)
    summary=dict(provisional_events=len(events),station_measurements=len(rows),measured_events=len(means),no_retrieved_window=unavailable,measurement_failures=failures,
                 negative_mean_FI=int((means.mean_FI<0).sum()),confirmed_hybrids=0,
                 method='All eligible recorded stations, Z response-corrected velocity; 8 s from own picked/predicted P; FFT power ratio 8--15/2--5 Hz; mean of station FIs. No taper or SNR rejection. Prior-arrival flag uses own provisional catalog, not a definitive coda classifier.',
                 status='Partial spectral screening only; negative FI is not a confirmed hybrid or LP event.')
    (D/'catalog_frequency_index.json').write_text(json.dumps(summary,indent=2)+'\n')
    print({k:v for k,v in summary.items() if k not in ['no_retrieved_window','measurement_failures']})

if __name__=='__main__':main()
