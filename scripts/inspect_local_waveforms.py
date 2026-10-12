"""Read original miniSEED examples from the listed local ZIP, without execution.

First archive member per station is an access/format inspection only. These
author-event-selected windows are not inserted into continuous exposure or used
to seed detections. ZIP member times are not read as event origins or picks.
"""
from pathlib import Path
import concurrent.futures,datetime,hashlib,io,json,struct,zlib
import requests
from obspy import read
ROOT=Path(__file__).resolve().parents[1]
URL='https://dataserver.ov.ingv.it/users/anna.tramelli/seismic_records/Tracce_AI_new.zip'
TARGET={'V0105','V0102','CRUS','CROS','CMDP','CFB1','CFB3','CREM','CSOC','CLAC','CGAU'}

def directory():
    raw=(ROOT/'inputs/extended/local_zip_directory.bin').read_bytes();i=raw.find(b'PK\x01\x02');selected={}
    while i>=0 and raw[i:i+4]==b'PK\x01\x02':
        h=struct.unpack_from('<4s6H3I5H2I',raw,i);n,e,c=h[10:13]
        name=raw[i+46:i+46+n].decode('utf-8')
        for station in TARGET:
            if station not in selected and '_'+station+'_' in name and name.endswith('.mseed'):
                selected[station]=dict(station=station,member=name,method=h[4],crc32=h[7],compressed=h[8],uncompressed=h[9],offset=h[16])
        i+=46+n+e+c
    return list(selected.values())

def fetch_range(a,b):
    r=requests.get(URL,headers={'Range':f'bytes={a}-{b}','Accept-Encoding':'identity'},timeout=(15,45))
    assert r.status_code==206 and len(r.content)==b-a+1,(r.status_code,r.headers.get('Content-Range'),len(r.content))
    return r.content

def inspect(member):
    row=dict(member,url=URL,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),classification='Original observations, author-event-selected 60-second windows; access inspection only',used_in_empirical_analysis=False)
    try:
        assert 0<member['uncompressed']<10_000_000
        header=struct.unpack('<4s5H3I2H',fetch_range(member['offset'],member['offset']+29));assert header[0]==b'PK\x03\x04'
        a=member['offset']+30+header[9]+header[10];b=a+member['compressed']-1
        compressed=fetch_range(a,b)
        raw=zlib.decompress(compressed,-15) if member['method']==8 else compressed
        assert len(raw)==member['uncompressed'] and zlib.crc32(raw)==member['crc32']
        path=ROOT/'inputs/local_inspection'/Path(member['member']).name;path.parent.mkdir(exist_ok=True);path.write_bytes(raw)
        st=read(io.BytesIO(raw))
        row.update(file=str(path.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),http=206,
            read_ok=True,request_ranges=[[member['offset'],member['offset']+29],[a,b]],
            traces=[dict(channel=t.id,start=str(t.stats.starttime),end=str(t.stats.endtime),samples=t.stats.npts,sample_rate=t.stats.sampling_rate) for t in st])
    except Exception as e:row.update(read_ok=False,error=repr(e))
    return row

if __name__=='__main__':
    members=directory();assert members
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(inspect,members))
    (ROOT/'docs/local_waveform_receipts.json').write_text(json.dumps(rows,indent=2)+'\n')
    (ROOT/'docs/local_waveform_inspection.json').write_text(json.dumps(dict(listed_stations=sorted(TARGET),
        stations_with_mseed_members=sorted(r['station'] for r in members),
        missing_from_saved_directory=sorted(TARGET-{r['station'] for r in members}),
        readable_examples=sum(r['read_ok'] for r in rows),
        selection='First miniSEED member per available station, solely for access/format inspection. Not an event seed or empirical result; author-event-selected 60-second cuts cannot establish continuous exposure.'),indent=2)+'\n')
    print([(r['station'],r['read_ok'],r.get('bytes'),r.get('error')) for r in rows])
