"""Rebuild the focused velocity assessment and the existing two documents.

Default: verify frozen inputs, restore own solver evidence if needed, inspect
saved numerical results, regenerate diagnostics and compile both PDFs.
--fit: preserve the previous summary/evidence, rerun the registered fits and
the training-only review sensitivity. No waveform download is started here.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys,tarfile
R=Path(__file__).resolve().parents[1];D=R/'data/velocity_holdout_review';W=R/'tmp/velocity_holdout_review'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def restore(archive,manifest,allowed):
    record=json.loads(manifest.read_text());assert sha(archive)==record['sha256']
    with tarfile.open(archive) as tar:
        for m in tar.getmembers():assert (R/m.name).resolve().is_relative_to(allowed.resolve()) and not m.issym() and not m.islnk()
        tar.extractall(R,filter='data')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--fit',action='store_true');args=ap.parse_args();logs=[]
    plan=json.loads((D/'experiment_plan.json').read_text())
    prior=R/'tmp/availability_extension/velocity_december'
    if not all((prior/name).exists() for name in ['base_holdout_initialization/input.cnv','base_prelocation/input.mod','base_prelocation/input.sta']):
        parent=R/'data/availability_extension'
        restore(parent/'velocity_december_run_evidence.tar.gz',parent/'velocity_december_run_evidence.json',prior.parent)
    for f,h in plan['inputs'].items():assert sha(R/f)==h,f
    assert sha(D/'frozen_holdout.cnv')==plan['holdout_sha256']
    archive=D/'solver_evidence.tar.gz'
    if not (W/'runs/four_regularized_base_joint5/output.cnv').exists():
        restore(archive,D/'solver_evidence.json',W)
    def run(script,*arguments):
        command=[sys.executable,'scripts/'+script,*arguments];p=subprocess.run(command,cwd=R,capture_output=True,text=True)
        log=W/(script+'.build.log');log.parent.mkdir(parents=True,exist_ok=True);log.write_text(p.stdout+p.stderr)
        logs.append(dict(command=command,returncode=p.returncode,log=str(log.relative_to(R))));dump(D/'rebuild_result.json',dict(complete=False,steps=logs))
        if p.returncode:raise RuntimeError(str(log))
    if args.fit:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S');checkpoint=D/'checkpoints'/stamp;checkpoint.mkdir(parents=True)
        (D/'summary.json').rename(checkpoint/'summary.json')
        if archive.exists():archive.rename(checkpoint/'solver_evidence.tar.gz');(D/'solver_evidence.json').rename(checkpoint/'solver_evidence.json')
        run('test_velocity_parameterizations.py','--run')
        run('check_velocity_review_exclusion.py')
        run('analyze_velocity_holdout.py','--ablations')
        run('review_velocity_unstable_events.py')
    else:
        run('analyze_velocity_holdout.py')
    run('present_velocity_holdout.py')
    # Retain native CNV, models, station corrections, residuals, ray points,
    # controls and console logs. These are our solver outputs, not author data.
    if not archive.exists():
        with tarfile.open(archive,'w:gz') as tar:
            for name in ['runs','ablations','coda_sensitivity']:tar.add(W/name,arcname=str((W/name).relative_to(R)))
        dump(D/'solver_evidence.json',dict(file=str(archive.relative_to(R)),bytes=archive.stat().st_size,sha256=sha(archive),role='Own numerical run evidence. Extract only inside the project root.'))
    # Do not mutate scientific inputs while the presentation builder verifies
    # their hashes. Its live-acquisition flag excludes only named live ledgers.
    run('build_documents.py','--clean','--live-acquisition')
    build=json.loads((R/'report/document_build.json').read_text())
    dump(D/'rebuild_result.json',dict(complete=True,mode='refit and rebuild' if args.fit else 'saved numerical verification and document rebuild',steps=logs,holdout_unchanged=True,accepted=False,documents={str(p.relative_to(R)):sha(p) for p in [R/'report/report.pdf',R/'report/comparison.pdf']},document_checks=build))
    print('Verified saved numerical results and rebuilt report/report.pdf and report/comparison.pdf')
if __name__=='__main__':main()
