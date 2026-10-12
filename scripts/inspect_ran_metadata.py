"""List and read official RAN station metadata, never execute archive files.

The saved 17 selected XML files are public metadata, not RAN waveforms.
The frozen copies are restored by the revision source bundle.
"""
from pathlib import Path
from io import BytesIO
import hashlib,json,zipfile,warnings
import pandas as pd
from bs4 import BeautifulSoup
from obspy import read_inventory,UTCDateTime

ROOT=Path(__file__).resolve().parents[1]
def main():
    receipts=json.loads((ROOT/'docs/ran_metadata_access.json').read_text())
    for r in receipts:
        if not (ROOT/r['file']).exists() and r['file'].endswith('RAN_metadata_response'):continue
        assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
    released=pd.read_csv(ROOT/'inputs/models/stations.csv')
    wanted={s.split('.')[1] for s in released.iloc[:,0] if s.startswith('IT.')}
    directory=ROOT/'inputs/revision/ran_stationxml';directory.mkdir(exist_ok=True)
    selected=[];epochs=[];parser_warnings=[]
    archive=ROOT/'inputs/revision/RAN_metadata_response'
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            members=[dict(name=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size,crc=i.CRC) for i in z.infolist()]
            (ROOT/'docs/ran_metadata_members.json').write_text(json.dumps(dict(classification='Public station and response metadata; no execution',members=members),indent=2)+'\n')
            for member in members:
                name=member['name']
                if name not in {s+'.IT.xml' for s in wanted}:continue
                raw=z.read(name) # ZipFile checks the member CRC before returning.
                p=directory/name;p.write_bytes(raw)
    else:
        members=json.loads((ROOT/'docs/ran_metadata_members.json').read_text())['members']
        for r in json.loads((ROOT/'docs/ran_metadata_summary.json').read_text())['selected_xml']:
            assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
    for name in sorted(s+'.IT.xml' for s in wanted):
        p=directory/name;raw=p.read_bytes()
        selected.append(dict(file=str(p.relative_to(ROOT)),archive_member=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        with warnings.catch_warnings(record=True) as caught:
            inv=read_inventory(BytesIO(raw))
        parser_warnings.extend(sorted({str(w.message) for w in caught}))
        for net in inv:
            for station in net:
                for ch in station:
                    if ch.code[:2] not in ['HN','HG']:continue
                    if ch.start_date>=UTCDateTime('2025-03-21') or (ch.end_date and ch.end_date<UTCDateTime('2022-01-21')):continue
                    epochs.append(dict(id=f'{net.code}.{station.code}.{ch.location_code}.{ch.code}',start=str(ch.start_date),end=str(ch.end_date or ''),
                        latitude=ch.latitude,longitude=ch.longitude,elevation_m=ch.elevation,depth_m=ch.depth,
                        azimuth=ch.azimuth,dip=ch.dip,sample_rate=ch.sample_rate,
                        response_present=bool(ch.response and ch.response.instrument_sensitivity and ch.response.response_stages),source=str(p.relative_to(ROOT))))
    soup=BeautifulSoup((ROOT/'inputs/revision/RAN_stations.html').read_bytes(),'html.parser');installation=[]
    for row in soup.select('tr'):
        cells=[x.get_text(' ',strip=True) for x in row.find_all('td')]
        if cells and cells[0] in wanted:
            installation.append(dict(station=cells[0],state_at_retrieval=cells[1],latitude=float(cells[3]),longitude=float(cells[4]),
                elevation_source_string=cells[5],installed=cells[6],removed=cells[7],source='inputs/revision/RAN_stations.html'))
    pd.DataFrame(epochs).to_csv(ROOT/'data/continuation/ran_response_epochs.csv',index=False)
    pd.DataFrame(installation).to_csv(ROOT/'data/continuation/ran_installations.csv',index=False)
    result=dict(source='https://ran.protezionecivile.it/IT/stazioni.php',archive_members=len(members),selected_xml=selected,
                stations=len(selected),study_acceleration_channel_epochs=len(epochs),responses_present=sum(x['response_present'] for x in epochs),
                geometry_units='XML latitude/longitude degrees, elevation/depth metres; HTML altitude string retained without assumed conversion.',
                parser_warnings=sorted(set(parser_warnings)),note='Warnings concern ancillary channels with null orientation comments; acceleration-channel orientations are retained explicitly. NAP has HG channels, unlike the released HN identifier; it is not silently renamed. Metadata access is public. Waveform download credentials remain unavailable. POZA closes on 2025-01-15; all 17 overlap part of the study. This does not prove the paper used precisely these instruments.')
    (ROOT/'docs/ran_metadata_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k not in ['selected_xml','parser_warnings']})

if __name__=='__main__':main()
