"""Verify a frozen observational checkpoint, plot it, and build both documents.

--run-analysis creates a NEW checkpoint and runs inference, association, six
independent VELEST fits, separated holdouts, and five whole-cohort location
passes. Without that switch, numerical results are verified and reused.
Acquisition is a separate, resumable process and is never implied complete.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys,tarfile
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/availability_extension'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-analysis',action='store_true');ap.add_argument('--catalog');ap.add_argument('--profile');ap.add_argument('--locations',default='locations_canonical');a=ap.parse_args()
    current=json.loads((D/'current_analysis.json').read_text()) if (D/'current_analysis.json').exists() else dict(catalog='data/availability_extension/catalog',profile='data/availability_extension/velocity_canonical',locations='locations_canonical')
    for k in ['catalog','profile']:
        if getattr(a,k):current[k]=getattr(a,k)
    if a.run_analysis:current['locations']=a.locations
    C=ROOT/current['catalog'];V=ROOT/current['profile'];logs=[]
    log=D/('rebuild_'+C.name+'.json');env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CF_AVAIL_CATALOG=current['catalog'])
    def run(script,*args):
        command=[str(ROOT/'.venv/bin/python'),'scripts/'+script,*args];out=ROOT/'tmp/availability_extension'/('rebuild_'+C.name+'_'+script+'.log');out.parent.mkdir(exist_ok=True)
        start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with out.open('w') as f:r=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
        logs.append(dict(command=command,returncode=r.returncode,log=str(out.relative_to(ROOT)),started_utc=start,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));write(log,logs)
        print(script,r.returncode,str(out.relative_to(ROOT)),flush=True)
        if r.returncode:raise RuntimeError('Stage failed; inspect '+str(out))
    if a.run_analysis:
        assert a.catalog and a.profile,'New versioned output paths required'
        assert not C.exists() and not V.exists(),'Preserve earlier checkpoints: select new paths'
        run('process_availability_extension.py','--freeze','--workers','4')
        run('prepare_observational_selection.py','--observations',current['catalog'])
        run('compare_observational_cohorts.py','--observations',current['catalog'])
        run('estimate_observational_profile.py','--observations',current['catalog'],'--selection',current['catalog']+'/selection','--output',current['profile'])
        run('validate_observational_profile.py','--profile',current['profile'])
        run('locate_observational_profile.py','--observations',current['catalog'],'--profile',current['profile'],'--result-name',current['locations'])
    # Exact input identities are checked before an existing result is reused.
    for path,h in json.loads((C/'processing_checkpoint.json').read_text())['files'].items():assert sha(ROOT/path)==h,path
    s=json.loads((V/'summary.json').read_text())
    for path,h in s['inputs'].items():assert sha(ROOT/path)==h,path
    assert sha(ROOT/'scripts/estimate_observational_profile.py')==s['code_sha256']
    location=json.loads((C/current['locations']/'summary.json').read_text())
    assert sha(ROOT/location['model'])==location['model_sha256']
    for trial in s['runs'].values():
        assert 'error' not in trial,trial
        for result in trial['runs']+list(trial['holdout'].values()):
            assert sha(ROOT/('build/velest'+str(result['bits'])))==result['binary_sha256']
    write(D/'current_analysis.json',current)
    # Retain controls, input arrivals, residuals and iteration logs in Git.
    archive=D/(V.name+'_run_evidence.tar.gz')
    if not archive.exists():
        with tarfile.open(archive,'w:gz') as tar:
            for directory in [ROOT/'tmp/availability_extension'/V.name,ROOT/'tmp/availability_extension'/C.name/current['locations']]:
                for path in sorted(directory.rglob('*')):
                    if path.is_file():tar.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
    write(D/(V.name+'_run_evidence.json'),dict(file=str(archive.relative_to(ROOT)),sha256=sha(archive),bytes=archive.stat().st_size,role='Own observed arrivals, solver inputs, residuals, and logs; no author event solutions.'))
    run('check_availability_overlap.py');run('plot_observational_profile.py');run('availability_report.py');run('build_documents.py','--clean','--live-acquisition')
    print('Frozen numerical checkpoint verified; plots and both PDFs rebuilt. Acceptance:',s['accepted'],flush=True)
if __name__=='__main__':main()
