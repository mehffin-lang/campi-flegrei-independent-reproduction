"""Offline verified rebuild of bounded observational analysis, figures and report."""
from pathlib import Path
import os,sys,json,hashlib,zipfile,subprocess,time
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
assert sys.argv[1:] in ([],['--clean'])
for d in ['tmp','build','data','figures','report']:(ROOT/d).mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(ROOT/'tmp'),MPLCONFIGDIR=str(ROOT/'tmp/matplotlib'),SEISBENCH_CACHE_ROOT=str(ROOT/'tmp/seisbench'),SOURCE_DATE_EPOCH='1791504000',PYTHONDONTWRITEBYTECODE='1')
for item in json.loads(Path('docs/file_inventory.json').read_text()):
 p=Path(item['file']);assert p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
 if p.suffix=='.pdf':subprocess.check_call(['pdftotext','-layout',str(p),'tmp/'+p.stem+'.txt'])
 else:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
assert all('Figure S'+str(i)+':' in Path('tmp/tanmodelsupp.txt').read_text() for i in range(1,16))
assert all('Fig. '+str(i)+'.' in Path('tmp/tanmodel.txt').read_text() for i in range(1,5))
for row in json.loads(Path('docs/observation_inputs.json').read_text()):
 if 'sha256' in row:assert hashlib.sha256(Path(row['file']).read_bytes()).hexdigest()==row['sha256']
 else:raise RuntimeError('Required download failed: '+row['file'])
if '--clean' in sys.argv:
 for folder,patterns in {'data/observations':['*.csv','*.npz','*.json'],'figures':['stations_partial.*','coverage_partial.*','hybrid_E*.*','independent_picks.*'],'report':['report.pdf','report.aux','report.log','report.out','*_table.tex','results.tex','observations.tex'],'build':['method_checks']}.items():
  for pat in patterns:
   for p in Path(folder).glob(pat):p.unlink()
cmds=[['g++','-std=c++17','-O3','-Wall','-Wextra','-pedantic','src/method_checks.cpp','-o','build/method_checks'],['./build/method_checks','config/method_checks.cfg','data'],[sys.executable,'scripts/analyze_observations.py'],[sys.executable,'scripts/plot_observations.py'],[sys.executable,'scripts/update_panel_record.py'],[sys.executable,'scripts/report_tables.py']]
latex=['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory=report','report/report.tex'];cmds.extend([latex,latex]);logs=[]
for cmd in cmds:
 start=time.monotonic();print('RUN '+' '.join(cmd),flush=True)
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
 logs.append(dict(command=cmd,returncode=p.returncode,elapsed_s=time.monotonic()-start,output=p.stdout))
 Path('data/build_log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:print(p.stdout);raise SystemExit(p.returncode)
 print('PASS '+str(round(time.monotonic()-start,2))+'s',flush=True)
text=subprocess.check_output(['pdftotext','report/report.pdf','-'],universal_newlines=True)
assert 'No main-manuscript panel is reproduced' in ' '.join(text.split())
issues=[line for line in Path('report/report.log').read_text().splitlines() if 'Overfull' in line or 'LaTeX Warning' in line]
assert not issues, '\n'.join(issues)
obs=json.loads(Path('data/observations/summary.json').read_text());rows=json.loads(Path('docs/panels.json').read_text())
status=dict(build_passed=True,scientific_reproduction_complete=False,publication_panels_reproduced=0,publication_panels_partial=[r['panel'] for r in rows if r['status']=='partially reproduced'],observation_summary=obs,python=sys.version,clean='--clean' in sys.argv)
Path('data/build_status.json').write_text(json.dumps(status,indent=2)+'\n')
paths=[]
for folder in ['src','scripts','config','docs','data','figures','report','sources']:
 paths.extend(p for p in Path(folder).rglob('*') if p.is_file() and p.suffix in ['.md','.cpp','.py','.cfg','.json','.csv','.tex','.pdf','.png','.npz','.txt'] and p.name!='manifest.sha256')
paths.extend(Path(x) for x in ['README.md','.gitignore'])
Path('data/manifest.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p)+'\n' for p in sorted(paths)))
print('PASS: bounded observational rebuild. Full scientific reproduction is incomplete.')
