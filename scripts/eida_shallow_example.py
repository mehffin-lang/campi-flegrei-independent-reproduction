"""Observed S15D analogue selected from own provisional shallow locations.

The event is not identified as a verified VT source or the published example.
The explicit 2 km CAAM proximity screen substitutes neither for the unpublished
west-Accademia polygon nor for absolute-depth validation. No reference event
time, location or figure value is read.
"""
from pathlib import Path
import hashlib,json,os
import numpy as np,pandas as pd
from scipy.signal import spectrogram
from obspy import read,read_inventory,UTCDateTime
from obspy.geodetics import gps2dist_azimuth
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';B=D/'calibration/merged4';O=D/'shallow_example'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    O.mkdir(exist_ok=True)
    existing=O/'summary.json'
    if existing.exists():
        old=json.loads(existing.read_text());identity={n:sha(ROOT/n) for n in old['inputs']}
        sources=[f for r in old['attempts'] for f in r.get('sources',[])]
        if identity==old['inputs'] and all(sha(ROOT/f['file'])==f['sha256'] for f in sources):
            print('Reused shallow-example attempt with matching observation, input and implementation hashes.');return
    events=pd.read_csv(B/'uncertainty/relocated_events.csv')
    picks=pd.read_csv(B/'tomodd/retained_picks.csv');coverage=pd.read_csv(D/'processed_coverage.csv')
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'))
    records=[];usable=[]
    for e in events[(events.depth_km>=0)&(events.depth_km<.6)&(events.latitude<40.83)].itertuples():
        r=dict(event_index=int(e.event_index),time=e.time,latitude=e.latitude,longitude=e.longitude,depth_km=e.depth_km)
        try:
            origin=UTCDateTime(e.time);sta=inv.select(network='IV',station='CAAM',time=origin)[0][0]
            r['distance_to_CAAM_km']=gps2dist_azimuth(e.latitude,e.longitude,sta.latitude,sta.longitude)[0]/1000
            if r['distance_to_CAAM_km']>2:raise ValueError('Beyond the explicit 2 km CAAM proximity screen')
            own=picks[(picks.event_index==e.event_index)&(picks.phase=='P')].copy()
            own['station']=own.trace_id.str.split('.').str[1]
            if not {'CAAM','COLB'}<=set(own.station):raise ValueError('Independent retained P missing at CAAM or COLB')
            t=UTCDateTime(own[own.station=='CAAM'].iloc[0].time);arrays={};sources=[];r['sources']=sources
            for name in ['CAAM','COLB']:
                q=coverage[coverage.channel.str.startswith('IV.'+name+'.')&(coverage.start<=float(t)-15)&(coverage.end>=float(t)+25)]
                if q.empty:raise ValueError('No complete continuous observation window at '+name)
                file=q.iloc[0].file;sources.append(dict(file=file,sha256=sha(ROOT/file)))
                st=read(str(ROOT/file),starttime=t-15,endtime=t+25).select(station=name).merge(method=0).split()
                st.detrend('demean');st.taper(.03);st.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                for component in ['Z','E']:
                    tr=st.select(component=component)
                    if len(tr)!=1 or tr[0].stats.sampling_rate!=100:raise ValueError('Incomplete or non-100 Hz '+name+component)
                    trace=tr[0].copy().trim(t-2,t+12);arrays[name+'_'+component]=np.vstack([trace.times(reftime=t),trace.data])
            tt,y=arrays['CAAM_Z'];signal=y[(tt>=0)&(tt<=4)];noise=y[(tt>=-2)&(tt<=-.3)]
            snr=10*np.log10(np.mean(signal**2)/np.mean(noise**2));r['power_SNR_dB']=float(snr)
            if not np.isfinite(snr) or snr<5:raise ValueError('CAAM Z signal/noise below explicit 5 dB display screen')
            r.update(p_alignment=str(t),sources=sources,eligible=True);usable.append((r,arrays))
        except Exception as exc:r.update(eligible=False,reason=repr(exc))
        records.append(r)
    summary=dict(method=__doc__,selection='Depth 0–0.6 km and latitude <40.83 N in own relocated trial; <=2 km from CAAM; retained own P at both stations; four complete continuous components; CAAM Z power SNR >=5 dB. Highest CAAM SNR among eligible events. These display choices are not recovered Tan settings.',attempts=records,available=bool(usable),accepted_source_classification=False,inputs={str(p.relative_to(ROOT)):sha(p) for p in [B/'uncertainty/relocated_events.csv',B/'tomodd/retained_picks.csv',D/'processed_coverage.csv',ROOT/'inputs/continuation/IV_responses.xml',Path(__file__)]})
    if usable:
        selected,arrays=max(usable,key=lambda q:q[0]['power_SNR_dB']);normalization=max(np.max(abs(arrays['CAAM_'+c][1])) for c in ['Z','E']);rows=[];spectra={}
        for key,(tt,y) in arrays.items():
            yy=y/normalization
            rows.extend(dict(station=key.split('_')[0],component=key[-1],time_s=float(t),velocity_m_s=float(v),normalized=float(n)) for t,v,n in zip(tt,y,yy))
            f,t,p=spectrogram(yy,fs=100,nperseg=128,noverlap=112);spectra[key+'_f']=f;spectra[key+'_t']=t+tt[0];spectra[key+'_power']=p
        pd.DataFrame(rows).to_csv(O/'waveforms.csv',index=False);np.savez_compressed(O/'spectra.npz',**spectra)
        summary.update(selected=selected,normalization_CAAM_velocity_m_s=normalization,normalization='One maximum across CAAM Z/E velocity, applied also to COLB; relative amplitudes retained.',spectral_settings='Hann is not assumed: scipy.signal.spectrogram default Tukey(0.25), 128 samples, 112 overlap, density scaling; 100 Hz; display 1–20 Hz and -80–0 dB normalized velocity squared per Hz, explicit alternative because published normalization unspecified.')
    (O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
