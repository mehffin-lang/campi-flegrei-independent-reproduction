"""Rebuild current EIDA counterparts and both existing PDFs.

Default verifies the sealed numerical checkpoint then redraws and compiles.
--analysis reruns all frozen numerical stages; no download or new visual judgment.
Original observations and model/method resources must already be placed locally.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';M=ROOT/'data/mechanism_eida'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--analysis',action='store_true');a=ap.parse_args();W=ROOT/'tmp/eida_rebuild';W.mkdir(exist_ok=True);runs=[]
    def run(script,*args,env=None):
        command=[sys.executable,'scripts/'+script,*args];log=W/(script+'.log')
        with log.open('w') as out:r=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        runs.append(dict(command=command,returncode=r.returncode,log=str(log.relative_to(ROOT))));(D/'rebuild_result.json').write_text(json.dumps(dict(passed=False,analysis_requested=a.analysis,runs=runs),indent=2)+'\n')
        print(script,r.returncode,flush=True)
        if r.returncode:raise RuntimeError(str(log))
    if a.analysis:
        run('build_eida_velest.py');run('build_eida_tomodd.py');run('build_eida_hypodd.py')
        run('build_sparse_velest.py');run('adopt_sparse_velest.py')
        run('process_eida_followup.py')
        run('calibrate_eida_followup.py');run('validate_eida_holdout.py');run('diagnose_eida_precision.py');run('eida_shallow_example.py')
        run('audit_continuation.py','--data-dir','data/eida_continuation')
        run('extend_hybrid_scan.py','--dataset','grid','--output','data/eida_continuation/hybrid','--input-manifest','data/eida_continuation/input_jobs.json');run('hybrid_eida_followup.py')
        run('review_eida_hybrids.py')
        import numpy as np
        review=json.loads((D/'hybrid/visual_review.json').read_text());arrays=np.load(D/'hybrid/review_waveforms.npz')
        for name,h in review['input_hashes'].items():assert sha(ROOT/name)==h,'Hybrid review input changed: '+name
        for key,h in review['array_hashes'].items():assert hashlib.sha256(arrays[key].tobytes()).hexdigest()==h,'Hybrid review window changed: '+key
        run('catalog_frequency_index.py',env=dict(os.environ,CF_OBSERVATIONS='data/eida_continuation'))
        run('catalog_frequency_review.py',env=dict(os.environ,CF_OBSERVATIONS='data/eida_continuation',CF_FREQUENCY_DIAGNOSTIC='figures/catalog_frequency_eida_diagnostic.pdf'))
        screen=json.loads((D/'catalog_frequency_visual_screen.json').read_text()); arrays=np.load(D/'catalog_frequency_review.npz')
        for key,h in screen['review_array_hashes'].items():assert hashlib.sha256(arrays[key].tobytes()).hexdigest()==h,'FI screening window changed: '+key
        run('grid_focal_attempt.py',env=dict(os.environ,CF_GRID_BASE='data/eida_continuation/calibration',CF_GRID_WORK='tmp/eida_continuation',CF_OBSERVATIONS='data/eida_continuation'))
        run('link_eida_candidates.py')
        env=dict(os.environ,CF_MECH_OUT='data/mechanism_eida',CF_MECH_OBSERVATIONS='data/eida_continuation',CF_MECH_WORK='tmp/mechanism_eida',CF_MECH_DECISIONS='config/mechanism_eida_decisions.json',CF_MECH_ARRIVALS='config/mechanism_eida_arrivals.csv',CF_MECH_LOCATIONS='data/mechanism_eida/candidate_locations.csv',CF_MECH_MODEL='data/eida_continuation/calibration/merged4/independent_calibrated.mod')
        run('mechanism_measurements.py',env=env)
        # Rerunning inference must not silently reuse review after the windows change.
        receipt=json.loads((M/'new_visual_review.json').read_text())
        for name,h in receipt['sources'].items():
            if name.endswith('review_waveforms.npz'):continue # ZIP timestamps are nonnumerical.
            assert sha(ROOT/name)==h,'Visual review input changed: '+name
        import numpy as np
        arrays=np.load(M/'review_waveforms.npz')
        assert set(arrays.files)==set(receipt['review_array_hashes'])
        for key,h in receipt['review_array_hashes'].items():assert hashlib.sha256(arrays[key].tobytes()).hexdigest()==h,key
        run('run_reviewed_skhash.py',env=env);run('run_gcap_followup.py',env=env);run('run_gcap_followup.py','--high-band',env=env);run('validate_mechanism_followup.py',env=env)
        run('eida_checkpoint_summary.py');run('acquisition_ledger.py','--data-dir','data/eida_continuation','--snapshot','data/eida_continuation/acquisition_snapshot.json');run('seal_eida_results.py')
    seal=json.loads((D/'numerical_checkpoint.json').read_text())
    for name,h in seal['files'].items():assert sha(ROOT/name)==h,name
    run('plot_eida_followup.py');run('eida_report.py');run('build_documents.py','--clean')
    plots=json.loads((D/'plot_inventory.json').read_text())
    for plot in plots:
        for name,h in dict(plot['inputs'],**plot['outputs']).items():assert sha(ROOT/name)==h,name
    build=json.loads((ROOT/'report/document_build.json').read_text());assert build['build_passed']
    result=dict(passed=True,analysis_requested=a.analysis,numerical_checkpoint_verified=True,scientific_acceptance=False,runs=runs,plots=len(plots),document_order_verified=True,analysis_execution='data/eida_continuation/pipeline_execution.json',note='Default reuses hash-verified executed numerical outputs, redraws current panels, and builds both PDFs; it is not a new full-period analysis or human review.')
    (D/'rebuild_result.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
