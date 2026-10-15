"""Verify new raw observations; optionally restore exact receipts and the ledger.

Previously empty/failed requests are not issued again. A fresh checkout can
reconstruct the ignored SQLite ledger from its committed snapshot and receipts.
Restore earlier inputs with restore_eida_observations.py first.
"""
import argparse,json,shutil
import pandas as pd
import requests
import availability_extension as a
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--download',action='store_true');x=ap.parse_args();missing=[];checked=0
    reserve=json.loads((a.D/'storage_budget.json').read_text())['reserve_bytes']
    receipts={p.stem:json.loads(p.read_text()) for p in (a.D/'receipts').glob('*.json')}
    for r in receipts.values():
        if r['status']!='downloaded':continue
        p=a.ROOT/r['file']
        if not p.exists() and x.download:
            p.parent.mkdir(parents=True,exist_ok=True);part=p.with_suffix('.restore.part')
            try:
                with requests.get(a.BASE+'dataselect/1/query',params=r['parameters'],stream=True,timeout=(20,90)) as z:
                    z.raise_for_status()
                    with part.open('wb') as f:
                        for b in z.iter_content(1048576):
                            if shutil.disk_usage(a.ROOT).free-len(b)<reserve+8*1048576:raise OSError('Storage reserve reached')
                            f.write(b)
                assert a.sha(part)==r['sha256'],'Remote bytes differ from the recorded observation; do not reuse previous analysis.'
                part.replace(p)
            finally:part.unlink(missing_ok=True)
        if not p.exists():missing.append(r['file']);continue
        assert p.stat().st_size==r['bytes'] and a.sha(p)==r['sha256'],r['file'];checked+=1
    print(json.dumps(dict(checked_files=checked,missing_files=missing),indent=2))
    if missing:raise SystemExit(1)
    if not (a.I/'requests.sqlite').exists():
        a.I.mkdir(exist_ok=True);c=a.database()
        for r in pd.read_csv(a.D/'request_ledger.csv.gz').to_dict('records'):
            c.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?)',tuple(r[k] for k in ['id','net','sta','band','start','end','missing_s','status'])+(json.dumps(receipts[r['id']]) if r['id'] in receipts else None,))
        c.commit();c.close();print('Restored request states; prior failed/empty intervals remain excluded.')
if __name__=='__main__':main()
