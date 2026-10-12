"""Audit released station metadata against official response epochs for S2.

Released identifiers are candidate membership only. No matching by proximity or
renaming is used to invent the paper's 48-instrument deployment inventory.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from obspy import read_inventory,UTCDateTime
from pyproj import Geod
from continue_context import PROJ

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data/continuation'
START,END=UTCDateTime('2022-01-21'),UTCDateTime('2025-03-21')

def main():
    import inspect_ran_metadata
    inspect_ran_metadata.main()
    released=pd.read_csv(ROOT/'inputs/models/stations.csv').rename(columns={'Unnamed: 0':'id'})
    official={};epochs=[];sources=[]
    metadata=sorted((ROOT/'inputs/continuation').glob('*_responses.xml'))+sorted((ROOT/'inputs/revision/ran_stationxml').glob('*.xml'))
    for p in metadata:
        sources.append(dict(file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        for network in read_inventory(str(p)):
            for station in network:
                for ch in station:
                    if ch.code[:2] not in ['HH','EH','HN','HG']:continue
                    if (ch.start_date and ch.start_date>=END) or (ch.end_date and ch.end_date<START):continue
                    ident=f'{network.code}.{station.code}.{ch.location_code}.{ch.code[:2]}'
                    row=dict(id=ident,channel=ch.code,longitude=ch.longitude,latitude=ch.latitude,elevation_m=ch.elevation,
                             channel_depth_m=ch.depth,start=str(ch.start_date),end=str(ch.end_date or ''),source=str(p.relative_to(ROOT)),
                             response_present=bool(ch.response and ch.response.instrument_sensitivity and ch.response.response_stages))
                    epochs.append(row);official.setdefault(ident,[]).append(row)
    geod=Geod(ellps='WGS84');rows=[]
    for r in released.to_dict('records'):
        net,sta,loc,band=r['id'].split('.')
        matches=official.get(r['id'],[])
        other_bands=sorted(k for k in official if k.startswith(f'{net}.{sta}.{loc}.') and k!=r['id'])
        points=sorted({(v['longitude'],v['latitude'],v['elevation_m']) for v in matches})
        # Multiple official coordinates remain unresolved, not silently averaged.
        status='verified official epoch' if len(points)==1 else ('unresolved epoch coordinates' if points else 'released metadata only; epoch unverified')
        if not points and other_bands:status='unresolved channel-band mismatch'
        lon,lat,elev=points[0] if len(points)==1 else (r['longitude'],r['latitude'],r['elevation(m)'])
        _,_,difference=geod.inv(r['longitude'],r['latitude'],lon,lat)
        x,y=PROJ.transform(lon,lat);back=PROJ.transform(x,y,direction='INVERSE')
        assert np.allclose(back,[lon,lat],rtol=0,atol=1e-9)
        rows.append(dict(id=r['id'],network=net,station=sta,location=loc,band=band,
                         released_longitude=r['longitude'],released_latitude=r['latitude'],released_elevation_m=r['elevation(m)'],
                         longitude=lon,latitude=lat,elevation_m=elev,x_km=x,y_km=y,coordinate_difference_m=difference,
                         coordinate_status=status,official_epochs=len(matches),inside_map=(-10<=x<=13 and -8<=y<=9),
                         other_official_band_identifiers=';'.join(other_bands),
                         coordinate_units='longitude/latitude degrees; elevation metres; projected kilometres',
                         coordinate_source=';'.join(sorted({v['source'] for v in matches})) or 'inputs/models/stations.csv'))
    table=pd.DataFrame(rows);table.to_csv(D/'station_geometry_qa.csv',index=False)
    pd.DataFrame(epochs).to_csv(D/'station_geometry_epochs.csv',index=False)
    table.to_csv(D/'figure_S2.csv',index=False)
    coincident=[]
    for _,g in released.groupby(['longitude','latitude']):
        if len(g)>1:coincident.append(g.id.tolist())
    summary=dict(identifiers=len(table),published_instruments=48,verified_identifiers=int(table.coordinate_status.eq('verified official epoch').sum()),
                 unresolved_identifiers=table.loc[~table.coordinate_status.eq('verified official epoch'),'id'].tolist(),
                 verified_outliers=table.loc[table.coordinate_status.eq('verified official epoch')&~table.inside_map,'id'].tolist(),
                 released_coincident_identifiers=coincident,maximum_coordinate_correction_m=float(table.coordinate_difference_m.max()),
                 projection='WGS84 azimuthal equidistant, lon_0=14.14, lat_0=40.82; km; always_xy=True',map_extent_km=[-10,13,-8,9],
                 membership_verified=False,explanation='51 identifiers are not 51 verified distinct instruments. Two pairs share released coordinates; no deployment/alias evidence establishes that collapsing them, or removing any other identifier, yields the published 48.',
                 map_error='Natural Earth bounding-box filtering selected whole coastline geometries. Distant vertices expanded the axes; station coordinates themselves were local. Coast vertices are now masked before projection and map limits follow the coordinate audit.',sources=sources)
    (D/'station_geometry_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
