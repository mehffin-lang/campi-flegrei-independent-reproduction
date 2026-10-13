"""Rebuild supported provisional analyses from the frozen independent cohort.

Acquisition and inference are separately resumable and are not falsely called
full-period coverage by this bounded, reproducible scientific checkpoint.
"""
from pathlib import Path
import argparse,subprocess,json,datetime,sys
ROOT=Path(__file__).resolve().parents[1];PY=str(ROOT/'.venv/bin/python');D=ROOT/'data/grid_calibration';LOG=ROOT/'tmp/grid_calibration/provisional_rebuild'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--presentation-only',action='store_true');ap.add_argument('--documents-only',action='store_true');ap.add_argument('--science-only',action='store_true');ap.add_argument('--calibration',action='store_true');ap.add_argument('--extension',action='store_true');args=ap.parse_args();LOG.mkdir(exist_ok=True)
    record=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=' '.join(sys.argv),stages=[],procedure_passed=False,scientific_acceptance=False)
    if (args.presentation_only or args.documents_only) and (D/'provisional_rebuild.json').exists():
        prior=json.loads((D/'provisional_rebuild.json').read_text())
        scientific=prior.get('previous_scientific_execution',prior)
        (D/'provisional_science_rebuild.json').write_text(json.dumps(scientific,indent=2)+'\n')
        record['previous_scientific_execution']=scientific
        attempts=D/'provisional_build_attempts.json';history=json.loads(attempts.read_text()) if attempts.exists() else []
        if '--presentation-only' in prior.get('command','') or '--documents-only' in prior.get('command',''):history.append({k:v for k,v in prior.items() if k!='previous_scientific_execution'});attempts.write_text(json.dumps(history,indent=2)+'\n')
        if args.documents_only:record['reused_completed_stages']=prior.get('reused_completed_stages',[r for r in prior['stages'] if r['returncode']==0])
    def save():(D/'provisional_rebuild.json').write_text(json.dumps(record,indent=2)+'\n')
    def run(script,*extra):
        cmd=[PY,'scripts/'+script,*extra];name=script.removesuffix('.py')+('_extension' if '--extension' in extra else '');start=datetime.datetime.now(datetime.timezone.utc).isoformat();print('Running',name,flush=True)
        with (LOG/(name+'.log')).open('w') as out:r=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
        record['stages'].append(dict(command=cmd,start=start,returncode=r.returncode,log=str((LOG/(name+'.log')).relative_to(ROOT))));save()
        if r.returncode:raise RuntimeError(name+' failed; inspect recorded log')
    try:
        if not args.presentation_only and not args.documents_only:
            if not (ROOT/'build/hypodd21/src/hypoDD/hypoDD').exists():run('build_hypodd21.py')
            if args.calibration:
                run('build_velest.py')
                for bits in [32,64]:
                    subprocess.run(['gfortran','-std=legacy','-O2','-fcheck=bounds']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I','build','build/velest-portable.f','-o',f'build/velest{bits}'],cwd=ROOT,check=True)
                run('build_grid_tomodd.py');run('prepare_grid_calibration.py');run('run_grid_velest.py','--coarse-four');run('validate_grid_velest.py');run('run_grid_tomodd.py')
            # Core calibration/relocation already has a complete executed rebuild
            # receipt; validate source identities before extending its analyses.
            receipt=json.loads((D/'merged4/tomodd/measurement.json').read_text())
            import hashlib
            for p,h in receipt['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
            run('diagnose_grid_paths.py');run('settle_grid_prelocation.py');run('grid_uncertainty.py')
            run('downstream_checks.py','--dataset','grid','--workers','6');run('magnitude_statistics.py','--grid')
            run('grid_focal_attempt.py');run('grid_panel_data.py');run('grid_location_checks.py');run('extend_hybrid_scan.py','--dataset','grid');run('grid_hybrid_candidates.py')
            if args.extension:run('calibrate_coverage_extension.py');run('coverage_extension_downstream.py')
        if args.documents_only:
            import hashlib
            for file in [D/'verification.json',D/'provisional_verification.json',ROOT/'data/coverage_extension/calibration/verification.json',ROOT/'data/coverage_extension/calibration/provisional_verification.json']:assert json.loads(file.read_text())['passed'],file
            for entry in json.loads((D/'style/plot_inventory.json').read_text()):
                for path,digest in {**entry['inputs'],**entry['outputs']}.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
            run('build_documents.py','--clean')
        elif not args.science_only:
            run('coverage_extension_report.py','--prepare-only');run('publication_plots.py');run('grid_report.py');run('provisional_report.py');run('coverage_extension_report.py');run('verify_grid_workflow.py');run('verify_provisional_workflow.py')
            if (ROOT/'data/coverage_extension/downstream_execution.json').exists():run('verify_grid_workflow.py','--extension');run('verify_provisional_workflow.py','--extension')
            run('build_documents.py','--clean')
        record['procedure_passed']=True
    except Exception as exc:record['error']=repr(exc)
    record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps(record,indent=2))
    if not record['procedure_passed']:sys.exit(1)
if __name__=='__main__':main()
