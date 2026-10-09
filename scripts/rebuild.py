"""Offline, source-verified rebuild. No observational ZIP data enter calculations."""
from pathlib import Path
import csv,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1]; os.chdir(str(ROOT))
if any(a!='--clean' for a in sys.argv[1:]): raise SystemExit('usage: python3 scripts/rebuild.py [--clean]')
for d in ['build','tmp','data','figures','report']: (ROOT/d).mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(ROOT/'tmp'),MPLCONFIGDIR=str(ROOT/'tmp/matplotlib'),PYTHONDONTWRITEBYTECODE='1',SOURCE_DATE_EPOCH='1791504000')
# Check source identity/readability BEFORE cleaning any generated outputs.
inv=json.loads((ROOT/'docs/file_inventory.json').read_text())
for entry in inv:
    p=ROOT/entry['file']; assert p.stat().st_size==entry['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'], 'Source checksum changed; review needed'
    if p.suffix=='.zip':
        with zipfile.ZipFile(str(p)) as z:
            assert [(f.filename,f.file_size) for f in z.infolist()]==[(x['name'],x['bytes']) for x in entry['members']]
    else:
        subprocess.check_call(['pdftotext','-layout',str(p),str(ROOT/'tmp'/(p.stem+'.txt'))])
s=(ROOT/'tmp/tanmodelsupp.txt').read_text();m=(ROOT/'tmp/tanmodel.txt').read_text()
assert all('Figure S'+str(i)+':' in s for i in range(1,16))
assert all('Fig. '+str(i)+'.' in m for i in range(1,5))
assert 'Materials and Methods' in s and 'Frequency index' in s
if '--clean' in sys.argv:
    names={'build':['method_checks'],
      'data':['checks.csv','scaling.csv','frequency_index.csv','waveform.csv','regularization.csv','thresholds.csv','validation_summary.json','panel_attempts.json','build_log.json','build_status.json','manifest.sha256'],
      'figures':['method_checks.pdf','method_checks.png'],
      'report':['report.pdf','report.aux','report.log','report.out','checks_table.tex','files_table.tex','panels_table.tex','results.tex']}
    for folder,files in names.items():
        for f in files:
            p=ROOT/folder/f
            if p.exists(): p.unlink()
commands=[['g++','-std=c++17','-O3','-Wall','-Wextra','-pedantic','src/method_checks.cpp','-o','build/method_checks'],
          ['./build/method_checks','config/method_checks.cfg','data'],[sys.executable,'scripts/plot_methods.py'],
          [sys.executable,'scripts/report_tables.py']]
latex=['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory=report','report/report.tex']
log=[]
for command in commands+[latex,latex]:
    start=time.monotonic();p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
    log.append({'command':command,'returncode':p.returncode,'elapsed_s':time.monotonic()-start,'output':p.stdout})
    (ROOT/'data/build_log.json').write_text(json.dumps(log,indent=2)+'\n')
    print(' '.join(command)+': '+str(p.returncode),flush=True)
    if p.returncode: print(p.stdout);raise SystemExit(p.returncode)
logtex=(ROOT/'report/report.log').read_text()
issues=[x for x in logtex.splitlines() if 'Overfull' in x or 'LaTeX Warning' in x]
assert not issues, '\n'.join(issues)
assert (ROOT/'report/report.pdf').read_bytes().startswith(b'%PDF-')
txt=subprocess.check_output(['pdftotext','report/report.pdf','-'],universal_newlines=True)
assert 'No empirical manuscript or supplementary panel is reproduced' in ' '.join(txt.split())
assert 'M1a' in txt and 'V1a' not in txt
import numpy,matplotlib
validation=json.loads((ROOT/'data/validation_summary.json').read_text())
status={'build_passed':True,'clean':('--clean' in sys.argv),'scientific_reproduction_complete':False,
        'publication_panels_reproduced':0,'publication_panels_partial':0,'independent_method_panels':['M1a','M1b','M1c','M1d'],
        'validation':validation,'all_four_sources_verified':True,'zip_extraction':False,'archive_execution':False,
        'compiler':subprocess.check_output(['g++','--version'],universal_newlines=True).splitlines()[0],
        'python':sys.version,'numpy':numpy.__version__,'matplotlib':matplotlib.__version__,
        'latex':subprocess.check_output(['pdflatex','--version'],universal_newlines=True).splitlines()[0],
        'project_temporaries':'tmp/','matplotlib_cache':'tmp/matplotlib/','external_project_cache_created':False}
(ROOT/'data/build_status.json').write_text(json.dumps(status,indent=2)+'\n')
paths=[ROOT/x for x in ['README.md','.gitignore','AGENTS.md','brad-lipovsky-academic-style-guide.md']]+[ROOT/x['file'] for x in inv]
for directory in ['src','scripts','config','docs','data','figures','report','sources']:
    paths.extend(p for p in (ROOT/directory).glob('*') if p.is_file() and p.suffix in ['.md','.cpp','.py','.cfg','.json','.csv','.tex','.pdf','.png'])
(ROOT/'data/manifest.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))+'\n' for p in sorted(paths)))
print('PASS: source checks, equation checks, generated method figures and report build. Empirical reproduction remains blocked.')
