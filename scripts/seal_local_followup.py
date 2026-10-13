"""Preserve execution records and classify the continuation's actual inputs."""
from pathlib import Path
import hashlib,json,re,zipfile
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/local_extension';M=ROOT/'data/mechanism_followup'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    checkpoint=json.loads((D/'processing_checkpoint.json').read_text())
    current=ROOT/'scripts/process_local_followup.py'
    if sha(current)!=checkpoint['files'][str(current.relative_to(ROOT))]:
        # The only post-execution change added a frozen-manifest rebuild option.
        executed=current.read_text().replace("ap.add_argument('--frozen',action='store_true');",'')
        executed=re.sub(r'    if args.frozen:\n.*?(?=    p.jobs=)','',executed,flags=re.S)
        assert hashlib.sha256(executed.encode()).hexdigest()==checkpoint['files'][str(current.relative_to(ROOT))]
        saved=D/'executed_process_local_followup.py.txt';saved.write_text(executed)
        write(D/'source_revision.json',dict(executed_source=str(saved.relative_to(ROOT)),executed_sha256=sha(saved),current_source=str(current.relative_to(ROOT)),current_sha256=sha(current),change='After the executed run, added --frozen to read/verify the saved input manifest for repeat runs. No inference, association or numerical algorithm changed. Original executed source retained byte-for-byte.'))
    for name,expected in checkpoint['files'].items():
        if name=='scripts/process_local_followup.py' and sha(ROOT/name)!=expected:continue
        assert sha(ROOT/name)==expected,name
    members={}
    with zipfile.ZipFile(D/'calibration/run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT/'tmp/local_extension').rglob('*')):
            if path.is_file() and path.suffix not in ['.npz','.sqlite']:
                name=str(path.relative_to(ROOT/'tmp/local_extension'));archive.write(path,name);members[name]=sha(path)
    write(D/'calibration/run_records.json',members)
    logdir=M/'execution_logs';logdir.mkdir(exist_ok=True)
    for path in (ROOT/'tmp/mechanism_followup').glob('*.log'):
        (logdir/path.name).write_bytes(path.read_bytes())
    jobs={r['file']:r for r in json.loads((D/'input_jobs.json').read_text())}
    used=sorted(pd.read_csv(M/'measurements.csv').source.dropna().unique())
    observations=[]
    for name in used:
        assert name in jobs,name
        observations.append(dict(file=name,sha256=jobs[name]['sha256'],classification='Original waveform observation',role='Phase and three-component amplitude inspection; response-corrected gCAP observation where accepted'))
    inputs=[]
    for name,classification,role in [
        ('inputs/continuation/IV_responses.xml','Public metadata','Response, orientation, position and epoch'),
        ('inputs/continuation/2I_responses.xml','Public metadata','Response, orientation, position and epoch'),
        ('inputs/models/phasenet_retrained.pt','Permitted trained method weights','Tan-retrained PhaseNet inference; attribution and original source in prior model manifest'),
        ('data/grid_calibration/reference_grid.original','Permitted starting/reference grid','Tan distribution attributed to Battaglia2008; dimension discrepancy disclosed, original preserved'),
        ('data/coverage_extension/calibration/merged4/independent_calibrated.mod','Independent provisional result','Frozen cohort model for mechanism trials, not accepted physical model'),
        ('data/coverage_extension/calibration/merged4/uncertainty/relocated_events.csv','Independent provisional result','Frozen candidate locations, not Tan locations'),
        ('config/mechanism_visual_decisions.json','Independent AI visual measurements','Trace review decisions and signs, not human manual review'),
        ('config/mechanism_review_arrivals.csv','Independent AI visual measurement','CFMN649 observed P onset, not author pick')]:
        inputs.append(dict(file=name,sha256=sha(ROOT/name),classification=classification,role=role))
    write(M/'input_provenance.json',dict(observations=observations,other_inputs=inputs,method_software='data/mechanism_followup/method_resources.json',outputs={'review_waveforms.npz':'Observed response-corrected windows','measurements.csv':'Own measurements; raw automatic scores kept distinct from accepted review','gcap/solutions.csv':'Own unaccepted fitted results','gcap/run_records.zip':'Original waveform inputs plus theoretical Green functions/predictions, controls and logs; these predictions are not empirical observations'},review='AI visually inspected saved picked and broad unpicked records, with per-record decisions. Zero human reviews. The broad unpicked review predates the additional CFMN P pick.',published_references='Display-only source PDFs/crops in separate comparison PDF; no reference pixels or Tan derived solution table used in these calculations',tests='Only fixed-matrix eigensolver/rotation assertions; no synthetic observations or test fixtures in empirical tables'))
    source={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('*followup*.py'))}
    source['scripts/mechanism_measurements.py']=sha(ROOT/'scripts/mechanism_measurements.py')
    source['scripts/run_reviewed_skhash.py']=sha(ROOT/'scripts/run_reviewed_skhash.py')
    write(M/'source_hashes.json',source)
    # Actual local paths rather than requested spans; no new network request.
    physical={str(p.relative_to(ROOT)) for p in (ROOT/'inputs').rglob('*.mseed')}
    covered=set(pd.read_csv(D/'processed_coverage.csv').file)
    receipts={}
    for name in ['data/calibration_followup/expanded/processed_input_receipts.json','docs/continuous_retrievals.json']:
        receipts.update({r['file']:r for r in json.loads((ROOT/name).read_text()) if r.get('file')})
    combined=[]
    for name in sorted(covered):
        old=receipts.get(name,{})
        row=dict(file=name,sha256=jobs.get(name,old).get('sha256'),url=old.get('url'),classification='Original waveform observation',processing='Current per-file inference/cache manifest' if name in jobs else 'Previously independently processed baseline; own picks/coverage reused, not reinferred this turn')
        assert row['sha256'],name
        if name not in jobs:assert sha(ROOT/name)==row['sha256'],name
        combined.append(row)
    write(D/'all_observation_inputs.json',combined)
    write(D/'local_input_check.json',dict(current_inference_manifest_files=len(jobs),previously_processed_baseline_files=len(covered-set(jobs)),physical_mseed_files=len(physical),processed_source_files=len(covered),physical_files_not_in_processed_coverage=sorted(physical-covered),manifest_missing=[f for f in jobs if not (ROOT/f).is_file()],mechanism_observation_files=len(observations),note='859 current jobs plus 165 earlier independently processed baseline files, all original observations. Processing is not the same as obtaining valid picks for every fragment.'))
    print('Saved provenance and',len(members),'calibration execution records.')
if __name__=='__main__':main()
