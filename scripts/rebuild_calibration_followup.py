"""Rebuild the frozen exploratory follow-up and presentation; no new downloads.

Default: reuse a hash-verified independently computed expanded association
checkpoint. --fresh-association reruns association and any uncached inference.
Waveform differential times and all subsequent trials are recomputed by default.
Procedure success never means that scientific calibration passed validation.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);D=ROOT/'data/calibration_followup';PY=sys.executable
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fresh-association',action='store_true');args=parser.parse_args()
    os.environ.update(TMPDIR=str(ROOT/'tmp'),SOURCE_DATE_EPOCH='1791849600',PYTHONDONTWRITEBYTECODE='1')
    record=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),procedure_passed=False,scientific_calibration_accepted=False,
                expanded_mode='rerun association with compatible inference caches' if args.fresh_association else 'reuse hash-verified own association checkpoint',runs=[])
    path=D/'rebuild_status.json'
    def run(command,label):
        start=time.time();log=ROOT/'tmp/calibration_followup'/('rebuild_'+label+'.log')
        print(label,flush=True)
        with log.open('w') as stream:r=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        record['runs'].append(dict(label=label,command=command,returncode=r.returncode,seconds=time.time()-start,log=str(log.relative_to(ROOT))))
        path.write_text(json.dumps(record,indent=2)+'\n');r.check_returncode()
    try:
        for item in json.loads((ROOT/'docs/file_inventory.json').read_text()):
            if item['file'] in ['tanmodel.pdf','tanmodelsupp.pdf']:
                assert sha(ROOT/item['file'])==item['sha256'],item['file']
        run([PY,'scripts/followup_inventory.py'],'input_hashes')
        if args.fresh_association:
            run([PY,'scripts/extend_calibration_observations.py','--workers','8'],'expanded_association')
        else:
            checkpoint=json.loads((D/'expanded/processing_checkpoint.json').read_text())
            for p,h in checkpoint['files'].items():assert sha(ROOT/p)==h,p
            record['expanded_checkpoint_sha256']=sha(D/'expanded/processing_checkpoint.json')
        run([PY,'scripts/build_velest.py'],'build_velest')
        for bits in [32,64]:
            run(['gfortran','-std=legacy','-O2','-fcheck=bounds']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I','build','build/velest-portable.f','-o',f'build/velest{bits}'],f'compile_{bits}')
        run([PY,'scripts/build_hypodd21.py'],'build_hypodd')
        run([PY,'tests/check_hypodd_matrix.py'],'isolated_matrix_test')
        run([PY,'scripts/calibration_chain.py'],'calibration')
        assert json.loads((D/'summary.json').read_text())['status']=='executed exploratory chain'
        run([PY,'scripts/relocation_followup.py'],'observed_delays_and_hypodd')
        run([PY,'scripts/calibration_validation.py'],'validation')
        run([PY,'scripts/calibration_selection_check.py'],'selection_sensitivity')
        run([PY,'scripts/audit_continuation.py','--data-dir','data/calibration_followup/expanded'],'expanded_response_audit')
        run([PY,'scripts/acquisition_ledger.py','--data-dir','data/calibration_followup/expanded','--snapshot','data/calibration_followup/acquisition_snapshot.json'],'request_ledger')
        run([PY,'scripts/plot_calibration_followup.py'],'diagnostics')
        run([PY,'scripts/plot_continuation.py'],'publication_panels')
        run([PY,'scripts/continuation_report.py'],'panel_record')
        run([PY,'scripts/followup_report.py'],'followup_record')
        run([PY,'scripts/build_documents.py','--clean'],'documents')
        run([PY,'scripts/verify_current_outputs.py'],'existing_result_checks')
        run([PY,'scripts/verify_calibration_followup.py'],'followup_checks')
        record['procedure_passed']=True
        record['scientific_outcome']='Calibration rejected: nonconvergence and nonphysical stricter-selection fits. HypoDD exploratory only, NE SVD diverged. No fixed-3D TomoDD or accepted-location magnitude solution.'
    except Exception as exc:record['error']=repr(exc)
    record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['script_sha256']=sha(Path(__file__))
    path.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='runs'},indent=2))
    if not record['procedure_passed']:sys.exit(1)

if __name__=='__main__':main()
