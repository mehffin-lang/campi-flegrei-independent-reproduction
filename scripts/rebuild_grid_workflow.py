"""Rebuild current reference-grid experiments, saved-result styling and both PDFs."""
from pathlib import Path
import argparse,json,hashlib,os,subprocess,sys,time,datetime
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/grid_calibration';PY=sys.executable

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--remeasure',action='store_true',help='Reread original waveforms and recompute all differential measurements.');parser.add_argument('--resume-presentation',action='store_true',help='After completed scientific stages, repair presentation without repeating inversion.');parser.add_argument('--resume-relocation',action='store_true',help='Rebuild/rerun relocation and presentation after completed calibration.');parser.add_argument('--resume-documents',action='store_true',help='Recheck and compile saved results after a document-only correction.');args=parser.parse_args();os.chdir(ROOT)
    os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',TMPDIR=str(ROOT/'tmp'),PYTHONDONTWRITEBYTECODE='1',SOURCE_DATE_EPOCH='1791849600')
    record=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),procedure_passed=False,runs=[],scope='Verified expanded independent picking/association checkpoint; calibration rerun; optional verified own delay reuse; all current plots and both documents. No new waveform acquisition or full-period inference claimed.')
    def save():(D/'rebuild_status.json').write_text(json.dumps(record,indent=2)+'\n')
    def run(cmd,label):
        start=time.time();path=ROOT/'tmp/grid_calibration'/('rebuild_'+label+'.log');print(label,flush=True)
        with path.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
        record['runs'].append(dict(label=label,command=cmd,returncode=r.returncode,seconds=time.time()-start,log=str(path.relative_to(ROOT))));save();r.check_returncode()
    if args.resume_presentation or args.resume_relocation or args.resume_documents:
        previous=json.loads((D/'rebuild_status.json').read_text())
        required=['four_layer_calibration','precision_validation','differential_and_tomodd','provenance_checks']
        assert all(any(r['label']==label and r['returncode']==0 for r in previous['runs']) for label in required)
        history=D/('first_rebuild_attempt.json' if not (D/'first_rebuild_attempt.json').exists() else 'before_relocation_repair.json');history.write_text(json.dumps(previous,indent=2)+'\n')
        record.update(previous);record['resumed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['previous_error']=record.pop('error',None)
        record['procedure_passed']=False
        record['presentation_resume']='Scientific stages completed in this recorded full rebuild; independent input/measurement hashes rechecked. Inversions are not repeated for formatting changes.'
        try:
            for receipt in ['merged4/validation.json','merged4/tomodd/measurement.json']:
                info=json.loads((D/receipt).read_text())
                for p,h in info.get('sources',info.get('files',{})).items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
            if args.resume_relocation:
                record['relocation_resume']='Calibration unchanged; rebuild generic solver with complete per-cluster residual output, rerun both rounds and active-observation gap filters.'
                run([PY,'scripts/build_grid_tomodd.py'],'tomodd_output_fix_build')
                run([PY,'scripts/run_grid_tomodd.py','--reuse-measurements'],'tomodd_all_cluster_validation')
            steps=([('publication_plots.py','all_plots_repair')] if not args.resume_documents else [])+[('grid_report.py','current_record_repair'),('verify_grid_workflow.py','provenance_recheck'),('build_documents.py','documents_repair')]
            for script,label in steps:run([PY,'scripts/'+script]+(['--clean'] if script=='build_documents.py' else []),label)
            record['procedure_passed']=True;record['scientific_outcome']=json.loads((D/'current_status.json').read_text())
        except Exception as exc:record['error']=repr(exc)
        record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps(record,indent=2))
        if not record['procedure_passed']:sys.exit(1)
        return
    try:
        checkpoint=json.loads((ROOT/'data/calibration_followup/expanded/processing_checkpoint.json').read_text())
        for p,h in checkpoint['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
        run([PY,'scripts/build_velest.py'],'velest_source')
        for bits in [32,64]:run(['gfortran','-std=legacy','-O2','-fcheck=bounds']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I','build','build/velest-portable.f','-o',f'build/velest{bits}'],f'velest{bits}')
        run([PY,'scripts/build_grid_tomodd.py'],'tomodd_build')
        run([PY,'scripts/prepare_grid_calibration.py'],'grid_profiles')
        run([PY,'scripts/run_grid_velest.py'],'eight_layer_trial')
        run([PY,'scripts/run_grid_velest.py','--coarse-four'],'four_layer_calibration')
        run([PY,'scripts/validate_grid_velest.py'],'precision_validation')
        run([PY,'scripts/run_grid_tomodd.py']+([] if args.remeasure else ['--reuse-measurements']),'differential_and_tomodd')
        run([PY,'scripts/publication_plots.py'],'all_plots')
        run([PY,'scripts/grid_report.py'],'current_record')
        run([PY,'scripts/verify_grid_workflow.py'],'provenance_checks')
        run([PY,'scripts/build_documents.py','--clean'],'both_documents')
        record['procedure_passed']=True;record['scientific_outcome']=json.loads((D/'current_status.json').read_text())
    except Exception as exc:record['error']=repr(exc)
    record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps(record,indent=2))
    if not record['procedure_passed']:sys.exit(1)
if __name__=='__main__':main()
