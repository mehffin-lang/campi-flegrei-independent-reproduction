"""Freeze the new acquisition checkpoint without changing the pilot's IDs."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/calibration_followup'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    target=D/'acquisition_snapshot.json'
    if args.freeze:
        tmp=ROOT/'tmp/calibration_followup/acquisition.sqlite'
        source=sqlite3.connect(f'file:{ROOT}/inputs/continuation/acquisition.sqlite?mode=ro',uri=True)
        destination=sqlite3.connect(tmp);source.backup(destination);source.close();destination.close()
        archive=D/'acquisition.sqlite.gz';archive.write_bytes(gzip.compress(tmp.read_bytes(),mtime=0))
        target.write_text(json.dumps(dict(file=str(archive.relative_to(ROOT)),bytes=archive.stat().st_size,sha256=sha(archive),
            frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),role='Actual request ledger; pending requests are not coverage'),indent=2)+'\n')
        baseline=json.loads((ROOT/'data/continuation/acquisition_checkpoint.json').read_text())
        current=json.loads((ROOT/'data/continuation/acquisition_summary.json').read_text())
        (D/'acquisition_checkpoint.json').write_text(json.dumps(current,indent=2)+'\n')
        current_receipts=json.loads((ROOT/'docs/continuous_retrievals.json').read_text())
        old={r['file'] for r in json.loads((ROOT/'docs/continuation_rebuild_inputs.json').read_text())}
        added=[dict(file=r['file'],url=r['url'],sha256=r['sha256'],bytes=r['bytes'],classification='Original waveform observations',start=r['start'],end=r['end']) for r in current_receipts if r.get('file') and r['file'] not in old and r.get('status')=='downloaded']
        (D/'additional_inputs.json').write_text(json.dumps(added,indent=2)+'\n')
        delta=dict(successful_requests=current['files']-baseline['files'],new_no_data=current['jobs_by_status']['no_data']-baseline['jobs_by_status']['no_data'],
                   bytes=current['downloaded_bytes']-baseline['downloaded_bytes'],channel_hours=current['channel_hours']-baseline['channel_hours'],
                   selected_by='Chronological queue; no event catalog; requests are six-hour intervals with processing margins',
                   request_command='.venv/bin/python scripts/collect_continuous.py run --workers 6 --max-jobs 48')
        (D/'acquisition_delta.json').write_text(json.dumps(delta,indent=2)+'\n')
    meta=json.loads(target.read_text());assert sha(ROOT/meta['file'])==meta['sha256']
    for r in json.loads((D/'additional_inputs.json').read_text()):assert sha(ROOT/r['file'])==r['sha256'],r['file']
    print('Verified frozen acquisition receipt and additional observation hashes.')

if __name__=='__main__':main()
