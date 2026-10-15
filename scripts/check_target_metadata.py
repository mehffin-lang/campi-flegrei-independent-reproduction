"""Check actual target headers against dated StationXML and local coordinates."""
import json
import pandas as pd
import numpy as np
from obspy import read,read_inventory,Inventory,UTCDateTime as U
from pyproj import Geod
from extend_velocity_training import R,D,C,END,sha,dump

def main():
    xmls=sorted((R/'inputs/continuation').glob('*_responses.xml'))
    inv=sum((read_inventory(str(p)) for p in xmls),Inventory(networks=[],source='EIDA'))
    station=pd.read_csv(C/'stations.csv').set_index('id');rows=[];geod=Geod(ellps='WGS84')
    for job in json.loads((D/'new_input_jobs.json').read_text()):
        assert job['end']<END and sha(R/job['file'])==job['sha256']
        st=read(str(R/job['file']),headonly=True)
        for tr in st:
            when=U(job['start']);ident='.'.join(tr.id.split('.')[:3]);ep=inv.select(network=tr.stats.network,station=tr.stats.station,location=tr.stats.location,channel=tr.stats.channel,time=when)
            channels=[ch for net in ep for s in net for ch in s]
            row=dict(file=job['file'],trace=tr.id,metadata_matches=len(channels),trace_start=str(tr.stats.starttime),trace_end=str(tr.stats.endtime),sample_rate=tr.stats.sampling_rate,phase_data_role='pre-2025 training only')
            if len(channels)==1:
                ch=channels[0];s=station.loc[ident];d=geod.inv(s.longitude,s.latitude,ch.longitude,ch.latitude)[2]
                row.update(epoch_start=str(ch.start_date),epoch_end=str(ch.end_date),latitude=ch.latitude,longitude=ch.longitude,elevation_m=ch.elevation,burial_m=ch.depth,azimuth_deg=ch.azimuth,dip_deg=ch.dip,response_present=ch.response is not None,metadata_rate=ch.sample_rate,coordinate_difference_m=float(d),elevation_difference_m=float(ch.elevation+s['z(km)']*1000),epoch_covers_core=ch.start_date<=when and (ch.end_date is None or ch.end_date>=U(job['end'])))
            rows.append(row)
    f=pd.DataFrame(rows);f.to_csv(D/'metadata_qa.csv',index=False)
    checks=dict(unique_epoch=bool(f.metadata_matches.eq(1).all()),responses=bool(f.response_present.all()),epochs_cover_core=bool(f.epoch_covers_core.all()),sample_rates=bool(f.sample_rate.eq(f.metadata_rate).all()),coordinate_max_difference_m=float(f.coordinate_difference_m.max()),elevation_max_difference_m=float(f.elevation_difference_m.abs().max()),metadata_sources={str(p.relative_to(R)):sha(p) for p in xmls},absolute_clock_verified=False,note='Header/epoch/response consistency does not establish absolute timing accuracy.')
    dump(D/'metadata_qa.json',checks);print(json.dumps(checks,indent=2))
    assert all(checks[k] for k in ['unique_epoch','responses','epochs_cover_core','sample_rates'])
if __name__=='__main__':main()
