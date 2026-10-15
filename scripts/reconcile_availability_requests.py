"""Do not repeat successful full-window requests to chase advertised internal gaps.

Gaps remain explicitly unverified, not counted as covered or declared empty.
Fresh, unattempted windows continue. No original file is removed.
"""
import argparse,json,sqlite3
import pandas as pd
import availability_extension as a
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    base=pd.read_csv(a.D/'baseline_files.csv');known=set(base.file);hashes=base.groupby('sha256').file.apply(list).to_dict()
    old=sqlite3.connect(a.ROOT/'inputs/continuation/acquisition.sqlite');old.row_factory=sqlite3.Row
    prior={(r['network'],r['station'],r['channel'][:2],r['start'],r['end']):dict(r) for r in old.execute("SELECT id,network,station,channel,start,end,status,file,sha256,url FROM jobs WHERE status='downloaded'") if r['file'] in known};old.close()
    c=a.database();rows=[];duplicates=[]
    for r in c.execute('SELECT * FROM requests').fetchall():
        key=(r['net'],r['sta'],r['band'],r['start'],r['end'])
        if r['status']=='pending' and key in prior:
            p=prior[key];receipt=dict(request=r['id'],status='prior_success_unverified_gaps',previous_request=p['id'],previous_file=p['file'],previous_sha256=p['sha256'],previous_url=p['url'],advertised_missing_channel_seconds=r['missing_s'],reason='This exact station/band/core request already succeeded. Repeating the full window can return identical bytes; remaining advertised gaps require targeted checks, not another whole-window download.')
            rows.append(receipt)
            if args.apply:
                c.execute('UPDATE requests SET status=?,receipt=? WHERE id=? AND status=?',(receipt['status'],json.dumps(receipt),r['id'],'pending'));a.dump(a.D/'receipts'/(r['id']+'.json'),receipt)
        elif r['status']=='downloaded':
            receipt=json.loads(r['receipt']);matches=hashes.get(receipt['sha256'],[])
            if matches:
                duplicates.append(dict(request=r['id'],file=receipt['file'],bytes=receipt['bytes'],identical_to=matches))
                if args.apply:
                    receipt['duplicate_of']=matches;receipt['new_raw_coverage']=False
                    c.execute('UPDATE requests SET receipt=? WHERE id=?',(json.dumps(receipt),r['id']));a.dump(a.D/'receipts'/(r['id']+'.json'),receipt)
    c.commit();c.close()
    result=dict(applied=args.apply,reclassified_requests=len(rows),advertised_gap_channel_hours=sum(r['advertised_missing_channel_seconds'] for r in rows)/3600,duplicate_downloads=duplicates,reclassified=rows,scope='Remaining gaps are unverified. Their advertised intervals remain in remaining_available_intervals.csv; no claim that they are absent or retrieved. Collector rechecks pending status before each batch.')
    a.dump(a.D/'prior_success_reconciliation.json',result)
    print({k:v for k,v in result.items() if k not in ['duplicate_downloads','reclassified']},'duplicate files',len(duplicates))
if __name__=='__main__':main()
