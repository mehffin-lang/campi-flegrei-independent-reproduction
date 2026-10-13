"""Measure observation gaps and response-epoch coverage from saved actual spans."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from obspy import read_inventory, UTCDateTime
from pyproj import Geod

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir',default='data/continuation')
args=parser.parse_args();D=(ROOT/args.data_dir).resolve()
assert D.is_relative_to(ROOT/'data')
start=float(UTCDateTime('2022-01-21'));end=float(UTCDateTime('2025-03-21'))
epochs={};details=[]
for file in sorted((ROOT/'inputs/extended/responses').glob('*.xml'))+sorted((ROOT/'inputs/continuation').glob('*_responses.xml')):
    for net in read_inventory(str(file)):
        for station in net:
            for ch in station:
                ident=f'{net.code}.{station.code}.{ch.location_code}.{ch.code}'
                a=float(ch.start_date) if ch.start_date else -np.inf
                b=float(ch.end_date) if ch.end_date else np.inf
                usable=bool(ch.response and ch.response.instrument_sensitivity and ch.response.response_stages)
                if usable:epochs.setdefault(ident,[]).append((a,b))
                details.append(dict(channel=ident,start=str(ch.start_date),end=str(ch.end_date or ''),usable_response=usable,
                    latitude=ch.latitude,longitude=ch.longitude,elevation_m=ch.elevation,depth_m=ch.depth,
                    sample_rate=ch.sample_rate,response_stages=len(ch.response.response_stages) if ch.response else 0,
                    source=str(file.relative_to(ROOT))))

def union(spans):
    out=[]
    for a,b in sorted(spans):
        if b<=a:continue
        if out and a<=out[-1][1]+1e-6:out[-1][1]=max(out[-1][1],b)
        else:out.append([a,b])
    return out

rows=[];gaps=[];stations={}
for r in json.loads((D/'processed_coverage_union.json').read_text()):
    ident=r['channel'];spans=union([(max(start,a),min(end,b)) for a,b in r['intervals']])
    response=union(epochs.get(ident,[]));cursor=start
    for a,b in spans:
        matched=sum(max(0,min(b,v)-max(a,u)) for u,v in response)
        rows.append(dict(channel=ident,start=str(UTCDateTime(a)),end=str(UTCDateTime(b)),observed_seconds=b-a,
            response_covered_seconds=matched,missing_response_seconds=max(0,b-a-matched)))
        if a>cursor:gaps.append(dict(channel=ident,start=str(UTCDateTime(cursor)),end=str(UTCDateTime(a)),gap_hours=(a-cursor)/3600))
        cursor=max(cursor,b)
    if cursor<end:gaps.append(dict(channel=ident,start=str(UTCDateTime(cursor)),end=str(UTCDateTime(end)),gap_hours=(end-cursor)/3600))
    station='.'.join(ident.split('.')[:2]);stations.setdefault(station,[]).extend(spans)
pd.DataFrame(details).drop_duplicates().to_csv(D/'response_epoch_details.csv',index=False)
coordinate_rows=[];geod=Geod(ellps='WGS84');detail_table=pd.DataFrame(details)
detail_table['id']=detail_table.channel.str.rsplit('.',n=1).str[0]
for ident,g in detail_table.groupby('id'):
    points=g[['longitude','latitude','elevation_m','depth_m']].drop_duplicates().to_numpy()
    horizontal=max([geod.inv(a[0],a[1],b[0],b[1])[2] for i,a in enumerate(points) for b in points[i+1:]] or [0.])
    coordinate_rows.append(dict(id=ident,distinct_coordinate_records=len(points),maximum_horizontal_difference_m=horizontal,
        elevation_range_m=float(np.ptp(points[:,2])),depth_range_m=float(np.ptp(points[:,3]))))
pd.DataFrame(coordinate_rows).to_csv(D/'coordinate_variability.csv',index=False)
pd.DataFrame(rows).to_csv(D/'response_coverage.csv',index=False)
pd.DataFrame(gaps).to_csv(D/'unobserved_channel_intervals.csv',index=False)
station_rows=[]
raw=pd.read_csv(D/'processed_coverage.csv')
for station,spans in sorted(stations.items()):
    times=union(spans);files=sorted(set(raw.loc[raw.channel.str.startswith(station+'.'),'file']))
    station_rows.append(dict(station=station,start=str(UTCDateTime(times[0][0])),end=str(UTCDateTime(times[-1][1])),
        union_station_hours=sum(b-a for a,b in times)/3600,
        channel_hours=sum(r['observed_seconds'] for r in rows if r['channel'].startswith(station+'.'))/3600,
        files=len(files),input_bytes=sum((ROOT/f).stat().st_size for f in files),disjoint_intervals=len(times)))
pd.DataFrame(station_rows).to_csv(D/'station_coverage.csv',index=False)
summary=dict(stations=len(station_rows),channels=len({r['channel'] for r in rows}),response_covered_channel_hours=sum(r['response_covered_seconds'] for r in rows)/3600,
    missing_response_channel_hours=sum(r['missing_response_seconds'] for r in rows)/3600,
    missing_response_intervals=sum(r['missing_response_seconds']>.05 for r in rows),
    maximum_metadata_coordinate_difference_m=max(r['maximum_horizontal_difference_m'] for r in coordinate_rows),
    note='Only actual returned intervals count. A response must have sensitivity and stages with overlapping epoch. This does not independently validate instrument calibration. Unobserved intervals are gaps in this retrieval, not assertions that the archive has no data.')
(D/'coverage_audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
