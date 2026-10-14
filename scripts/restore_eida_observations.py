"""Restore only missing frozen original EIDA waveforms, with exact SHA checks.

This is opt-in input restoration, not the pending full-period acquisition queue.
Changed archive bytes are reported and never silently accepted for a rebuild.
"""
from pathlib import Path
import argparse,hashlib,json
import requests
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');a=p.parse_args();missing=[]
    for r in json.loads((ROOT/'data/eida_continuation/observation_retrievals.json').read_text()):
        f=ROOT/r['file']
        if f.exists():assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'],r['file'];continue
        if not a.download or not r.get('url'):missing.append(r['file']);continue
        assert r['url'].startswith('https://webservices.ingv.it/'),r['url']
        f.parent.mkdir(parents=True,exist_ok=True);part=f.with_suffix('.restore-part')
        try:
            with requests.get(r['url'],stream=True,timeout=(20,150)) as response:
                response.raise_for_status()
                with part.open('wb') as out:
                    for chunk in response.iter_content(1024*1024):out.write(chunk)
            assert hashlib.sha256(part.read_bytes()).hexdigest()==r['sha256'],'Archive bytes differ: '+r['file']
            part.replace(f);print('Restored',r['file'],flush=True)
        finally:part.unlink(missing_ok=True)
    print(json.dumps(dict(missing=missing,download_requested=a.download),indent=2))
    if missing:raise SystemExit(1)
if __name__=='__main__':main()
