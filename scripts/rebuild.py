"""Offline rebuild: compile, validate, save data, plot, audit, compile report."""
from pathlib import Path
import os,subprocess,json,sys,time,hashlib,platform
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
for d in ['build','tmp','data','figures','report']: (ROOT/d).mkdir(exist_ok=True)
env=os.environ.copy()
env.update(TMPDIR=str(ROOT/'tmp'),MPLCONFIGDIR=str(ROOT/'tmp'/'matplotlib'),PYTHONDONTWRITEBYTECODE='1',SOURCE_DATE_EPOCH='1791504000')
os.environ.update(env)
commands=[['g++','-std=c++17','-O3','-Wall','-Wextra','-pedantic','src/validation.cpp','-o','build/validation'],
          ['./build/validation','config/validation.txt','data'],[sys.executable,'scripts/plot.py'],
          [sys.executable,'scripts/audit.py'],
          ['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory=report','report/report.tex']]
log=[]
for command in commands+commands[-1:]:
    start=time.monotonic(); p=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
    log.append({'command':command,'exit_code':p.returncode,'elapsed_s':time.monotonic()-start,'output':p.stdout})
    (ROOT/'data'/'build_log.json').write_text(json.dumps(log,indent=2)+'\n')
    print(' '.join(command),':',p.returncode,flush=True)
    if p.returncode: print(p.stdout); sys.exit(p.returncode)
import numpy,matplotlib
status={'build_passed':True,'scientific_reproduction_complete':False,'manuscript_panels_reproduced':0,
        'python':sys.version,'numpy':numpy.__version__,'matplotlib':matplotlib.__version__,
        'platform':platform.platform(),'compiler':subprocess.check_output(['g++','--version'],universal_newlines=True).splitlines()[0],
        'latex':subprocess.check_output(['pdflatex','--version'],universal_newlines=True).splitlines()[0],
        'temporary_directory':'tmp/','matplotlib_cache':'tmp/matplotlib/',
        'outside_repo_project_cache_created':False}
(ROOT/'data'/'build_status.json').write_text(json.dumps(status,indent=2)+'\n')
paths=[p for d in ['src','scripts','config','docs','figures','data','report'] for p in (ROOT/d).glob('*')
       if p.is_file() and p.suffix in ['.cpp','.py','.txt','.json','.csv','.pdf','.tex','.md','.png']
       and p.name not in ['manifest.sha256']]
(ROOT/'data'/'manifest.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))+'\n' for p in sorted(paths)))
print('PASS: validation and PDF build. Publication reproduction remains blocked.')
