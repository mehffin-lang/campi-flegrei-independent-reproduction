"""Measure original recordings for the frozen 1,023-association cohort.

No catalog or published mechanism is read. Additional stations use this
implementation's PhaseNet arrivals, inspected separately from retained picks.
Amplitude windows and gates below are explicit exploratory choices, not claimed
Tan settings. Visual decisions are a separate, versioned input to SKHASH.
"""
from pathlib import Path
import hashlib,json,sys,os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy import read,read_inventory,UTCDateTime
from obspy.geodetics import gps2dist_azimuth

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/coverage_extension';B=BASE/'calibration/merged4';D=ROOT/os.environ.get('CF_MECH_OUT','data/mechanism_followup')
OBS=ROOT/os.environ.get('CF_MECH_OBSERVATIONS','data/coverage_extension')
LOCATIONS=ROOT/os.environ.get('CF_MECH_LOCATIONS','data/coverage_extension/calibration/merged4/uncertainty/relocated_events.csv')

def main():
    D.mkdir(exist_ok=True);(D/'review').mkdir(exist_ok=True)
    if '--plots-only' in sys.argv:
        render(pd.read_csv(D/'measurements.csv'),np.load(D/'review_waveforms.npz'))
        return
    events=pd.read_csv(LOCATIONS).set_index('event_index')
    old=pd.read_csv(B/'focal/polarity_screen.csv');ids=sorted(old.event_id.unique())
    picks=pd.read_csv(OBS/'picks.csv');picks['epoch']=picks.time.map(lambda t:float(UTCDateTime(t)))
    retained=pd.read_csv(B/'tomodd/retained_picks.csv')
    if os.environ.get('CF_MECH_LOCATIONS'):
        ids=sorted(events.index)
        current=pd.read_csv(OBS/'calibration/merged4/tomodd/retained_picks.csv');mapped=[]
        for eid in ids:
            new_id=events.loc[eid].get('current_event_index')
            part=current[current.event_index==int(new_id)].copy() if pd.notna(new_id) else retained[retained.event_index==eid].copy()
            part['event_index']=eid;mapped.append(part)
        retained=pd.concat(mapped,ignore_index=True)
    arrival_file=ROOT/os.environ.get('CF_MECH_ARRIVALS','config/mechanism_review_arrivals.csv')
    reviewed=pd.read_csv(arrival_file)
    coverage=pd.read_csv(OBS/'processed_coverage.csv')
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'))+read_inventory(str(ROOT/'inputs/continuation/2I_responses.xml'))
    rows=[];waves={};stations=[]
    for eid in ids:
        e=events.loc[eid];origin=float(UTCDateTime(e.time));near=picks[(picks.epoch>origin)&(picks.epoch<origin+15)]
        cand=coverage[(coverage.start<origin-10)&(coverage.end>origin+20)&coverage.channel.str.endswith('Z')].copy()
        cand['ident']=cand.channel.map(lambda c:'.'.join(c.split('.')[:3]));cand=cand.drop_duplicates('ident')
        for item in cand.itertuples():
            ident=item.ident;net,sta,loc=ident.split('.');key=f'e{eid}_{net}_{sta}'
            row=dict(event_id=int(eid),network=net,station=sta,location=loc or '--',key=key,source=item.file,reviewer='not yet inspected',accepted=False)
            try:
                meta=inv.select(network=net,station=sta,location=loc,channel=item.channel.split('.')[-1],time=UTCDateTime(origin))[0][0][0]
                if abs(meta.dip+90)>1:raise ValueError('Upward vertical orientation not verified')
                dist,az,baz=gps2dist_azimuth(e.latitude,e.longitude,meta.latitude,meta.longitude)
                # Search guide only. Never use the approximate travel time as a pick.
                expected=origin+np.hypot(dist/1000,e.depth_km+meta.elevation/1000)/2.58
                pp=retained[(retained.event_index==eid)&(retained.trace_id==ident)&(retained.phase=='P')]
                method='retained own P'
                override=reviewed[(reviewed.event_id==eid)&(reviewed.trace_id==ident)]
                if len(override):
                    pp=pd.DataFrame([dict(time=override.p_time.iloc[0])]);method='AI visual P onset from original waveform; no human review'
                elif pp.empty:
                    pp=near[(near.trace_id==ident)&(near.phase=='P')].copy()
                    pp['distance_to_search']=abs(pp.epoch-expected);pp=pp[pp.distance_to_search<=2.0].sort_values('distance_to_search').head(1)
                    method='additional own PhaseNet P; travel-time search only'
                if pp.empty:raise ValueError('No independent P within 2 s of approximate own-model search time')
                pt=UTCDateTime(pp.iloc[0].time)
                ss=retained[(retained.event_index==eid)&(retained.trace_id==ident)&(retained.phase=='S')]
                if ss.empty:
                    ss=near[(near.trace_id==ident)&(near.phase=='S')&(near.epoch>float(pt)+.08)&(near.epoch<float(pt)+6)].copy()
                    ss['distance_to_search']=abs(ss.epoch-(origin+(float(pt)-origin)*1.73));ss=ss.sort_values('distance_to_search').head(1)
                stime=UTCDateTime(ss.iloc[0].time) if len(ss) else None
                stream=read(str(ROOT/item.file),starttime=pt-10,endtime=pt+15).merge(method=0).split()
                stream=stream.select(network=net,station=sta,location=loc)
                vertical=stream.select(component='Z')
                if len(vertical)!=1:raise ValueError('Not one continuous vertical segment')
                raw=vertical[0].copy().detrend('demean')
                vel=stream.copy().detrend('demean').taper(.03)
                for tr in vel:tr.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                z=vel.select(component='Z')[0];noise=z.copy().trim(pt-1,pt-.2).data;nrms=float(np.sqrt(np.mean(noise**2)))
                a=z.copy().trim(pt-.7,pt+.8);r=raw.copy().trim(pt-.7,pt+.8)
                waves[key+'_z']=np.vstack([a.times()+float(a.stats.starttime-pt),a.data])
                waves[key+'_raw']=np.vstack([r.times()+float(r.stats.starttime-pt),r.data])
                signs=[];snrs=[]
                for duration in [.04,.07,.10]:
                    y=z.copy().trim(pt,pt+duration).data;peak=y[np.argmax(abs(y))];signs.append(int(np.sign(peak)));snrs.append(float(abs(peak)/max(nrms,1e-30)))
                row.update(p_time=str(pt),s_time=str(stime) if stime else '',pick_basis=method,channel=z.stats.channel,azimuth=az,distance_km=dist/1000,latitude=meta.latitude,longitude=meta.longitude,elevation=meta.elevation,origin_latitude=e.latitude,origin_longitude=e.longitude,origin_depth_km=e.depth_km,noise_rms_m_s=nrms,sign_40ms=signs[0],sign_70ms=signs[1],sign_100ms=signs[2],minimum_onset_snr=min(snrs),automatic_stable=len(set(signs))==1 and min(snrs)>=3)
                stations.append(dict(network=net,station=sta,location=loc or '--',channel=z.stats.channel,latitude=meta.latitude,longitude=meta.longitude,elevation=meta.elevation))
                row.update(sp_usable=False,sp_reason='No own S arrival' if stime is None else 'Three oriented components required')
                components=[vel.select(component=c) for c in 'ZNE']
                if stime and all(len(c)==1 for c in components):
                    for c,azimuth,dip in [('N',0,0),('E',90,0)]:
                        tr=vel.select(component=c)[0];m=inv.select(network=net,station=sta,location=loc,channel=tr.stats.channel,time=pt)[0][0][0]
                        if abs(m.dip-dip)>1 or abs((m.azimuth-azimuth+180)%360-180)>1:raise ValueError('Horizontal orientation not verified')
                    filt=vel.copy().filter('bandpass',freqmin=1,freqmax=15,corners=4,zerophase=True)
                    common=filt.copy().trim(pt-3,stime+1,nearest_sample=True)
                    tr=common.select(component='Z')[0];t=tr.times()+float(tr.stats.starttime-pt)
                    yy=np.array([common.select(component=c)[0].data for c in 'ZNE'])
                    if yy.shape[1]!=len(t):raise ValueError('Component sample alignment')
                    waves[key+'_three']=np.vstack([t,yy])
                    amplitude=np.linalg.norm(yy,axis=0);sp=float(stime-pt);pend=min(.30,sp-.10)
                    if pend<.08:raise ValueError('P and S windows overlap')
                    ap=float(max(amplitude[(t>=0)&(t<=pend)]));ass=float(max(amplitude[(t>=sp)&(t<=sp+.50)]));noise=float(np.sqrt(np.mean(amplitude[(t>=-3)&(t<=-1)]**2)))
                    clipping=[]
                    for raw_tr in stream.copy().trim(pt,stime+.5):
                        y=raw_tr.data;extreme=(y==np.min(y))|(y==np.max(y))
                        edges=np.flatnonzero(np.diff(np.r_[False,extreme,False]));longest=max((b-a for a,b in zip(edges[::2],edges[1::2])),default=0)
                        if longest>=3 and float(np.max(y))-float(np.min(y))>100:clipping.append(raw_tr.id)
                    usable=ap/noise>=3 and ass/noise>=3 and not clipping
                    reason='Repeated raw extrema for >=3 samples; possible clipping: '+','.join(clipping) if clipping else 'Passes amplitude QC; arrival identity requires review' if usable else 'P or S vector peak below 3x vector noise RMS'
                    row.update(amp_p=ap,amp_s=ass,noise_p=noise,noise_s=noise,sp_ratio=ass/ap,p_snr=ap/noise,s_snr=ass/noise,sp_usable=usable,sp_reason=reason,possible_clipping_channels=';'.join(clipping),p_window_end_s=pend,s_minus_p_s=sp)
            except Exception as exc:row['error']=str(exc)
            rows.append(row)
        print(eid,len([r for r in rows if r['event_id']==eid]),flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(D/'measurements.csv',index=False);pd.DataFrame(stations).drop_duplicates().to_csv(D/'stations.csv',index=False);np.savez_compressed(D/'review_waveforms.npz',**waves)
    meta=dict(cohort='data/coverage_extension',candidate_events=len(ids),records=len(frame),reviewable=int(frame.p_time.notna().sum()),amplitude_qc_pass=int(frame.sp_usable.fillna(False).sum()),human_manual_reviews=0,method='Upward vertical verified from StationXML. Polarity raw counts and VEL, no additional bandpass. S/P = peak three-component velocity norm in P to min(P+.30,S-.10) and S to S+.50; 1–15 Hz 4-pole zero-phase. Noise P-3 to P-1; both peak/noise RMS >=3. Window/filter choices are exploratory; S/P and additional arrival identity need review.',sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [BASE/'picks.csv',B/'tomodd/retained_picks.csv',B/'uncertainty/relocated_events.csv',ROOT/'inputs/continuation/IV_responses.xml',ROOT/'inputs/continuation/2I_responses.xml']})
    meta['observation_checkpoint']=str(OBS.relative_to(ROOT))
    meta['amplitude_clipping_check']='Reject possible clipping if a raw P-through-S+.5 s component has >=3 consecutive extrema samples and peak-to-peak range >100 counts. Conservative exploratory QA, not a recovered Tan setting or proof of instrument saturation. Polarity remains a separate visual judgment.'
    meta['location_source']=str(LOCATIONS.relative_to(ROOT))
    meta['sources'][str(arrival_file.relative_to(ROOT))]=hashlib.sha256(arrival_file.read_bytes()).hexdigest()
    meta['sources'].pop(str((BASE/'picks.csv').relative_to(ROOT)),None)
    for file in [OBS/'picks.csv',OBS/'processed_coverage.csv']:
        meta['sources'][str(file.relative_to(ROOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
    if os.environ.get('CF_MECH_LOCATIONS'):
        meta['cohort']='Explicit candidate_mapping.csv; old review labels linked to current own locations, with new independently selected larger candidates where available.'
        for file in [LOCATIONS,OBS/'calibration/merged4/tomodd/retained_picks.csv',D/'candidate_mapping.csv']:
            meta['sources'][str(file.relative_to(ROOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
    (D/'measurement_summary.json').write_text(json.dumps(meta,indent=2)+'\n')
    if '--measurements-only' not in sys.argv:render(frame,waves)

def render(frame,waves):
    for eid,g in frame.groupby('event_id'):
        g=g.sort_values('station');good=g[g.key.map(lambda k:k+'_z' in waves)]
        for page in range((len(good)+7)//8):
            chunk=good.iloc[page*8:(page+1)*8];fig,axes=plt.subplots(len(chunk),2,figsize=(12,1.6*len(chunk)),squeeze=False,layout='constrained')
            for (_,r),(left,right) in zip(chunk.iterrows(),axes):
                for suffix,color,label in [('_raw','gray','counts'),('_z','black','response-corrected VEL')]:
                    t,y=waves[r.key+suffix];scale=max(abs(y[(t>=-.15)&(t<=.2)]).max(),1e-30);left.plot(t,y/scale,c=color,lw=.7,label=label)
                left.set(xlim=(-.4,.4),ylim=(-1.5,1.5),title=f'{r.network}.{r.station}  P {r.p_time[11:22]}  SNR {r.minimum_onset_snr:.1f}',xlabel='Seconds from own P');left.axvline(0,c='red',lw=.6);left.axhline(0,c='.7',lw=.5)
                if r.key+'_three' in waves:
                    arr=waves[r.key+'_three'];scale=max(abs(arr[1:]).max(),1e-30)
                    for i,c in enumerate('ZNE'):right.plot(arr[0],arr[i+1]/scale+i,c=['black','blue','green'][i],lw=.6,label=c)
                    sp=float(UTCDateTime(r.s_time)-UTCDateTime(r.p_time))
                    right.axvline(0,c='red',lw=.6);right.axvline(sp,c='orange',lw=.6);right.set(xlim=(-1,sp+1),xlabel='Seconds from P; orange = own S')
                else:right.text(.1,.5,str(r.get('sp_reason','')));right.axis('off')
            fig.suptitle(f'Event {eid}: original waveforms for AI visual review; not a paper figure')
            fig.savefig(D/f'review/event_{eid}_{page+1}.png',dpi=130);plt.close(fig)
if __name__=='__main__':main()
