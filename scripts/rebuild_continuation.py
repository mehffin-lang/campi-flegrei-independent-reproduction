"""Rebuild the frozen observational checkpoint and both PDFs, offline.

Unfinished scientific stages remain explicit; a successful build is not a claim
that the full multiyear study has been reproduced.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,zipfile
import rebuild_state
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--fresh',action='store_true',help='Recompute all inference, including the earlier independent inputs.');ap.add_argument('--resume',action='store_true',help='Resume a failed stage only if completed dependencies retain their hashes.');args=ap.parse_args()
if args.fresh and args.resume:ap.error('--fresh and --resume are mutually exclusive')
if args.resume:
    prior=rebuild_state.verify()
    # Preserve the original fresh-build command sequence when resuming it.
    args.fresh=any('scripts/analyze_observations.py' in row for row in prior['passed_commands'])
os.environ.update(TMPDIR=str(ROOT/'tmp'),MPLCONFIGDIR=str(ROOT/'tmp/matplotlib'),SEISBENCH_CACHE_ROOT=str(ROOT/'tmp/seisbench'),NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'),SOURCE_DATE_EPOCH='1791763200',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
D=ROOT/'data/continuation'
for folder in [D,ROOT/'build',ROOT/'tmp/continuation',ROOT/'tests/results']:folder.mkdir(parents=True,exist_ok=True)
# Access/identity checks precede any product replacement.
for row in json.loads(Path('docs/file_inventory.json').read_text()):
    p=Path(row['file']);assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    if p.suffix=='.pdf':subprocess.run(['pdftotext','-layout',str(p),str(ROOT/'tmp/continuation'/f'{p.stem}.txt')],check=True)
    else:
        with zipfile.ZipFile(p) as z:
            names=z.namelist();assert names and z.testzip() is None
assert all('Figure S'+str(i)+':' in Path('tmp/continuation/tanmodelsupp.txt').read_text() for i in range(1,16))
for manifest in ['docs/rebuild_inputs.json','docs/continuation_rebuild_inputs.json']:
    for row in json.loads(Path(manifest).read_text()):
        p=Path(row['file']);assert p.exists() and p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['file']
commands=[['g++','-std=c++17','-O3','-Wall','-Wextra','-pedantic','src/method_checks.cpp','-o','build/method_checks'],['./build/method_checks','config/method_checks.cfg','tests/results'],[sys.executable,'scripts/build_velest.py']]
if args.fresh:commands += [[sys.executable,'scripts/'+s+'.py'] for s in ['analyze_observations','extended_analysis']]
commands += [[sys.executable,'scripts/'+s+'.py'] for s in ['plot_observations','prepare_continuation','continue_context','station_geometry','acquisition_ledger']]
commands.append([sys.executable,'scripts/process_continuous.py','all','--workers','6','--frozen']+(['--fresh'] if args.fresh else []))
commands.append([sys.executable,'scripts/check_starting_profile.py'])
commands += [[sys.executable,'scripts/audit_continuation.py'],[sys.executable,'scripts/downstream_checks.py','--dataset','continuation'],[sys.executable,'scripts/velest_stability.py'],[sys.executable,'scripts/magnitude_statistics.py'],[sys.executable,'scripts/location_consistency.py','--dataset','continuation'],[sys.executable,'scripts/cpoz_gathers.py'],[sys.executable,'scripts/extend_hybrid_scan.py','--dataset','continuation'],[sys.executable,'scripts/hybrid_candidate_metrics.py'],[sys.executable,'scripts/plot_continuation.py'],[sys.executable,'scripts/continuation_report.py'],[sys.executable,'scripts/build_documents.py','--clean']]
commands.insert(next(i for i,c in enumerate(commands) if c[-1]=='scripts/plot_continuation.py'),[sys.executable,'scripts/catalog_frequency_index.py'])
commands.insert(next(i for i,c in enumerate(commands) if 'scripts/downstream_checks.py' in c),[sys.executable,'tests/check_window_reads.py'])
commands.append([sys.executable,'scripts/verify_current_outputs.py'])
logs=[];started=time.monotonic();resumed_stages=0
if args.resume:
    state=rebuild_state.verify();previous=json.loads((D/'rebuild_log.json').read_text())
    resumed_stages=len(state['passed_commands'])
    assert commands[:resumed_stages]==state['passed_commands'], 'Completed command sequence changed'
    attempts_path=D/'rebuild_attempts.json'
    attempts=json.loads(attempts_path.read_text()) if attempts_path.exists() else []
    old_attempt=D/'rebuild_failed_attempt.json'
    if old_attempt.exists() and not attempts:attempts.append(json.loads(old_attempt.read_text()))
    attempts.append(previous);attempts_path.write_text(json.dumps(attempts,indent=2)+'\n')
    (D/'rebuild_failed_attempt.json').write_text(json.dumps(previous,indent=2)+'\n')
    logs=previous[:resumed_stages];commands=commands[resumed_stages:]
    print('RESUME after',resumed_stages,'hash-verified successful stages',flush=True)
for cmd in commands:
    t=time.monotonic();print('RUN',' '.join(cmd),flush=True)
    run=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    logs.append(dict(command=cmd,returncode=run.returncode,elapsed_s=time.monotonic()-t,output=run.stdout))
    (D/'rebuild_log.json').write_text(json.dumps(logs,indent=2)+'\n')
    if run.returncode:
        rebuild_state.freeze(logs)
        (D/'rebuild_status.json').write_text(json.dumps(dict(build_passed=False,failed_command=cmd,returncode=run.returncode,scientific_reproduction_complete=False),indent=2)+'\n')
        print(run.stdout[-5000:]);raise SystemExit(run.returncode)
    print('PASS',round(time.monotonic()-t,1),'seconds',flush=True)
status=dict(build_passed=True,fresh=args.fresh,resumed_stages=resumed_stages,elapsed_s=time.monotonic()-started,total_successful_stage_elapsed_s=sum(r['elapsed_s'] for r in logs),scientific_reproduction_complete=False,
            analysis=json.loads((D/'analysis_summary.json').read_text()),panels=json.loads((D/'panel_status.json').read_text()),
            velest=json.loads((D/'velest_summary.json').read_text()),checkpoint=json.loads((D/'acquisition_checkpoint.json').read_text()),
            documents=json.loads(Path('report/document_build.json').read_text()))
(D/'rebuild_status.json').write_text(json.dumps(status,indent=2)+'\n')
files=[]
for directory in ['data/continuation','scripts','config','report','docs']:
    files += [p for p in Path(directory).rglob('*') if p.is_file() and p.suffix in ['.py','.json','.csv','.tex','.pdf','.md','.txt','.mod','.sta','.cnv'] and p.name!='manifest.sha256']
(D/'manifest.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p)+'\n' for p in sorted(files)))
print('PASS: frozen observed-subset rebuild and both PDFs. Full scientific reproduction remains incomplete.')
