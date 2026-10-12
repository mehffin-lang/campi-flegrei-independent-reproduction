"""Freeze every requested/pending interval and observed station/month exposure."""
from pathlib import Path
import gzip,hashlib,json,sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/continuation'

def main():
    meta=json.loads((ROOT/'docs/acquisition_database_snapshot.json').read_text());raw=(ROOT/meta['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==meta['sha256']
    checkpoint=ROOT/'tmp/continuation/request_ledger.sqlite'
    checkpoint.parent.mkdir(parents=True,exist_ok=True)
    checkpoint.write_bytes(gzip.decompress(raw))
    con=sqlite3.connect(f'file:{checkpoint}?mode=ro',uri=True)
    rows=pd.read_sql_query('SELECT * FROM jobs ORDER BY start,network,station',con);con.close()
    def exposure(value):
        per={}
        for s in json.loads(value if isinstance(value,str) and value else '[]'):per.setdefault(s['channel'],[]).append((s['start'],s['end']))
        total=0.
        for intervals in per.values():
            merged=[]
            for a,b in sorted(intervals):
                if merged and a<=merged[-1][1]+.001:merged[-1][1]=max(merged[-1][1],b)
                else:merged.append([a,b])
            total+=sum(b-a for a,b in merged)
        return total/3600
    rows['returned_channel_hours']=rows.segments.map(exposure)
    assert (rows.loc[~rows.status.eq('downloaded'),'returned_channel_hours']==0).all()
    rows=rows.drop(columns=['segments']);rows['start_utc']=pd.to_datetime(rows.start,unit='s',utc=True);rows['end_utc']=pd.to_datetime(rows.end,unit='s',utc=True)
    rows.to_csv(D/'request_ledger.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    table=rows.groupby(['network','station',rows.start_utc.dt.strftime('%Y-%m'),'status']).agg(requests=('id','size'),bytes=('bytes','sum'),returned_channel_hours=('returned_channel_hours','sum')).reset_index()
    table.to_csv(D/'request_station_month.csv',index=False)
    # Union-of-samples exposure remains authoritative if future requests overlap.
    (D/'request_ledger_note.json').write_text(json.dumps(dict(requests=len(rows),statuses=rows.status.value_counts().to_dict(),
        role='Request ledger is not a completeness claim. Per-request hours can overlap; authoritative processed exposure is processed_coverage_union.json. Pending, no_data and failed requests contribute zero.',
        missing_intervals='data/continuation/unobserved_channel_intervals.csv'),indent=2)+'\n')
    print('Saved',len(rows),'requests, including pending and failed intervals.')

if __name__=='__main__':main()
