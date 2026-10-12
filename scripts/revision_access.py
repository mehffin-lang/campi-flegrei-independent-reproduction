"""Retrieve written sources and access evidence, never author analysis results."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'inputs/revision'
OUT.mkdir(exist_ok=True)
URLS = {
    'battaglia2008_institution.html': 'https://www.fedoa.unina.it/7315/',
    'battaglia2008_publisher.html': 'https://onlinelibrary.wiley.com/doi/10.1111/j.1365-2478.2007.00687.x',
    'calo2018_publisher.html': 'https://www.nature.com/articles/s41598-018-34456-x',
    'calo2018_earthprints.json': 'https://www.earth-prints.org/server/api/core/bundles/e3b35e58-da65-49a9-8f8b-39e95afea8c5/bitstreams',
    'battaglia_hal.json': 'https://api.archives-ouvertes.fr/search/?q=title_t:%22Merging%20active%20and%20passive%22&fl=title_s,uri_s,fileMain_s,docid&wt=json',
    'routine_history.json': 'https://web.archive.org/cdx/search/cdx?url=terremoti.ov.ingv.it/gossip/flegrei/2025/index.html&output=json&filter=statuscode:200&filter=mimetype:text/html&collapse=timestamp:6',
    'routine_current.html': 'https://terremoti.ov.ingv.it/gossip/flegrei/2025/index.html',
    'local_traces.html': 'https://dataserver.ov.ingv.it/users/anna.tramelli/seismic_records/index.html',
    'RAN.html': 'https://ran.protezionecivile.it/IT/index.php',
    'EIDA_IV.html': 'https://eida.ingv.it/it/network/IV',
    'station_epoch_metadata.txt': 'https://webservices.ingv.it/fdsnws/station/1/query?net=IV,2I,IT&minlat=40.70&maxlat=40.95&minlon=13.95&maxlon=14.35&starttime=2022-01-21&endtime=2025-03-21&level=channel&format=text',
}

def get(item):
    name,url=item
    row=dict(file=str((OUT/name).relative_to(ROOT)),url=url,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        response=requests.get(url,timeout=(15,45))
        row.update(http=response.status_code,final_url=response.url,bytes=len(response.content),sha256=hashlib.sha256(response.content).hexdigest(),content_type=response.headers.get('Content-Type'))
        (OUT/name).write_bytes(response.content)
    except requests.RequestException as e:
        row.update(error=str(e),file=None)
    return row

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(get,URLS.items()))
    (ROOT/'docs/revision_access.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))
