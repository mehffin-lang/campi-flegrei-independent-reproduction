"""Raw and filtered pre-2025 onset review; no automatic repicking/acceptance."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from obspy import read,read_inventory,UTCDateTime as U,Inventory
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from extend_velocity_training import R,D,C,TARGET,END,sha,dump

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalog',default=str(C.relative_to(R)));ap.add_argument('--events',default='1952,1961');ap.add_argument('--tag',default='existing');args=ap.parse_args()
    cat=R/args.catalog;out=D/'review'/args.tag;out.mkdir(parents=True,exist_ok=True)
    p=pd.read_csv(cat/'picks.csv');p=p[p.time<'2025-01-01'];a=pd.read_csv(cat/'associations.csv');ev=pd.read_csv(cat/'initial_events.csv')
    events=ev[ev.event_index.isin([int(x) for x in args.events.split(',')])].sort_values('time');assert len(events)>0 and (events.time<'2025-01-01').all()
    intervals=pd.read_csv(D/'pre2025_stored_intervals.csv')
    new=D/'target_waveform_intervals.csv'
    if new.exists():intervals=pd.concat([intervals,pd.read_csv(new)],ignore_index=True).drop_duplicates()
    for ties in D.glob('ties_*/target_waveform_intervals.csv'):
        intervals=pd.concat([intervals,pd.read_csv(ties)],ignore_index=True).drop_duplicates()
    xmls=sorted((R/'inputs/continuation').glob('*_responses.xml'));inventory=sum((read_inventory(str(f)) for f in xmls),Inventory(networks=[],source='Existing EIDA StationXML'))
    saved=[];metadata=[];arrays={};timing=[]
    pt=p.time.map(lambda t:float(U(t)))
    for event in events.itertuples():
        origin=U(event.time);assert float(origin)<END
        chosen=p[(pt>=float(origin)-1)&(pt<float(origin)+14)].copy();chosen['assigned']=chosen.index.isin(a[a.event_index==event.event_index].pick_index)
        relevant=intervals[(intervals.start<=float(origin)-2)&(intervals.end>=float(origin)+16)]
        sources=relevant.groupby(relevant.channel.str.split('.').str[:3].str.join('.')).file.first().to_dict()
        stations=sorted(set(sources)&(set(chosen.trace_id)|{f'{n}.{s}.' for s,(n,b) in TARGET.items()}))
        for page,start in enumerate(range(0,len(stations),6)):
            batch=stations[start:start+6];fig,axes=plt.subplots(len(batch),1,figsize=(12,2*len(batch)),layout='constrained',squeeze=False)
            for ax,station in zip(axes[:,0],batch):
                source=sources[station];st=read(str(R/source),starttime=origin-2,endtime=origin+16,details=True)
                st=st.select(network=station.split('.')[0],station=station.split('.')[1]);gp=chosen[chosen.trace_id.eq(station)]
                item=dict(event_index=int(event.event_index),origin=str(origin),station=station,source=source,source_sha256=sha(R/source),picks=[])
                for i,tr in enumerate(sorted(st,key=lambda tr:tr.id)):
                    if np.ma.isMaskedArray(tr.data) and np.ma.getmaskarray(tr.data).any():continue
                    raw=tr.data.astype(float);raw-=np.mean(raw);filtered=tr.copy().detrend('linear').filter('bandpass',freqmin=1,freqmax=20,corners=2,zerophase=True).data
                    t=tr.times()+float(tr.stats.starttime-origin);key=f'e{event.event_index}_{tr.id}';arrays[key]=np.vstack([t,raw,filtered])
                    ax.plot(t,raw/max(abs(raw).max(),1e-20)*.45+i,color='.7',lw=.5)
                    ax.plot(t,filtered/max(abs(filtered).max(),1e-20)*.45+i,color='black',lw=.65);ax.text(-1.9,i+.3,tr.id,fontsize=7)
                    inv=inventory.select(network=tr.stats.network,station=tr.stats.station,location=tr.stats.location,channel=tr.stats.channel,time=origin)
                    chans=[(net.code,s,ch) for net in inv for s in net for ch in s]
                    for net,s,ch in chans:
                        metadata.append(dict(event_index=event.event_index,trace=tr.id,epoch_start=str(ch.start_date),epoch_end=str(ch.end_date),latitude=ch.latitude,longitude=ch.longitude,elevation_m=ch.elevation,depth_m=ch.depth,azimuth=ch.azimuth,dip=ch.dip,sample_rate=ch.sample_rate,trace_rate=tr.stats.sampling_rate,response_present=ch.response is not None,station_epoch_valid=ch.start_date<=origin and (ch.end_date is None or origin<ch.end_date)))
                    timing.append(dict(event_index=event.event_index,trace=tr.id,start=str(tr.stats.starttime),end=str(tr.stats.endtime),samples=tr.stats.npts,rate=tr.stats.sampling_rate,gaps=st.select(id=tr.id).get_gaps(),timing_quality=str(tr.stats.mseed.get('blkt1001',{})),metadata_matches=len(chans)))
                for idx,pick in gp.iterrows():
                    off=U(pick.time)-origin;col='#0072b2' if pick.phase=='P' else '#d55e00'
                    ax.axvline(off,color=col,lw=1,ls='-' if pick.assigned else ':');ax.text(off,2.65,f'{pick.phase} {pick.probability:.2f}',fontsize=7,color=col,rotation=45)
                    item['picks'].append(dict(pick_index=int(idx),phase=pick.phase,time=pick.time,probability=pick.probability,assigned=bool(pick.assigned)))
                ax.set(xlim=(-2,16),ylim=(-.6,3.1),yticks=[],xlabel='Seconds from provisional origin; gray raw, black 1–20 Hz')
                ax.set_title(f'{station}: solid = assigned, dotted = unassigned project pick',fontsize=9);saved.append(item)
            fig.suptitle(f'Training waveform review: event {event.event_index}, {event.time}\nDisplay only; no pick changes. P blue, S orange.');fig.savefig(out/f'event_{event.event_index}_{page}.png',dpi=140);plt.close(fig)
    dump(out/'windows.json',saved);dump(out/'timing.json',timing);pd.DataFrame(metadata).to_csv(out/'metadata.csv',index=False);np.savez_compressed(out/'windows.npz',**arrays)
    if args.tag=='ties_dec12':
        # Enlarged original raw traces used to measure/assess onsets, never a
        # published image. Keep this display reproducible beside its arrays.
        origin=U(events[events.event_index.eq(0)].iloc[0].time)
        fig,axes=plt.subplots(3,1,figsize=(12,9),layout='constrained')
        for ax,station,lo,hi in zip(axes,['2I.CGAU.','IV.CRUS.','IV.CUMA.'],[1,1.4,1.5],[3.6,4.3,4.5]):
            for i,key in enumerate(k for k in arrays if k.startswith('e0_'+station)):
                t,raw,_=arrays[key];mask=(t>=lo)&(t<=hi);scale=max(abs(raw[mask]).max(),1e-20)
                ax.plot(t[mask]+origin.second+origin.microsecond/1e6,raw[mask]/scale*.4+i,lw=.7,label=key)
            ax.set(title=station+' raw (demeaned only)',xlabel='UTC seconds after 04:34:00 on 2024-12-12',yticks=[]);ax.legend(fontsize=7);ax.grid(alpha=.3)
        fig.savefig(out/'onset_zoom.png',dpi=150);plt.close(fig)
    dump(out/'input_hashes.json',{str(f.relative_to(R)):sha(f) for f in [cat/'picks.csv',cat/'associations.csv',cat/'initial_events.csv',*xmls]})
    print('Reviewed-window records prepared',len(saved),'traces',len(timing),'metadata',len(metadata))
if __name__=='__main__':main()
