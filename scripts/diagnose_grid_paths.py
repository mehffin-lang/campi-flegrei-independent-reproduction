"""Controlled arithmetic/path and held-out checks; never changes accepted data."""
from pathlib import Path
import json,re,subprocess,shutil
import numpy as np
import pandas as pd
import run_grid_velest as g
c=g.c;v=g.v;ROOT=g.ROOT
BASE=ROOT/'data/grid_calibration/merged4';OUT=BASE/'diagnosis';WORK=ROOT/'tmp/grid_calibration/path_diagnosis'

def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')

def log_metrics(work):
    text=(work/'run.out').read_text()
    return dict(iterations=[int(x) for x in re.findall(r'ITERATION no\s+(\d+)',text)],
                weighted_rms_s=[float(x) for x in re.findall(r'RMS RESIDUAL=\s+([\d.]+)',text)],
                backup_iterations=re.findall(r'\(Iteration nr\s+(\d+)\)\s+BACKUP nr\s+(\d+)',text),
                stop=[x.strip() for x in text.splitlines() if 'stop iterations' in x.lower()],
                rays=re.findall(r'(\d+) straight and direct rays',text))

def main():
    OUT.mkdir(exist_ok=True);WORK.mkdir(parents=True,exist_ok=True);c.OUT=OUT;c.WORK=WORK
    original=ROOT/'tmp/grid_calibration/merged4';ids=pd.read_csv(BASE/'selected_initial_events.csv').event_index.tolist()
    record=dict(setup={},stages=[],common_start=[],heldout={},interpretation='provisional')
    for f in ['input.mod','input.sta','input.cnv','velest.cmn']:
        record['setup'][f]=dict(identical=c.sha(original/'caldera_prelocation'/f)==c.sha(original/'precision32_prelocation'/f),sha256=c.sha(original/'caldera_prelocation'/f))
    for stage in ['prelocation','round1','round2','convergence1','convergence2','convergence3']:
        a=original/('caldera_'+stage);b=original/('precision32_'+stage)
        ca=pd.read_csv(BASE/('caldera_'+stage+'_locations.csv'));cb=pd.read_csv(BASE/('precision32_'+stage+'_locations.csv'))
        record['stages'].append(dict(stage=stage,change=c.compare(ca,cb),run64=log_metrics(a),run32=log_metrics(b),
            numerical_start_model_equal=np.array_equal(v.model_table(a/'input.mod').to_numpy(),v.model_table(b/'input.mod').to_numpy()),
            station_start_equal=(a/'input.sta').read_bytes()==(b/'input.sta').read_bytes(),
            observation_hashes={str(p.relative_to(ROOT)):c.sha(p) for p in [a/'input.cnv',b/'input.cnv']},
            control_identical=(a/'velest.cmn').read_bytes()==(b/'velest.cmn').read_bytes()))
        # Same 64-bit serialized stage input in both arithmetic modes. Separates
        # propagation of changed upstream estimates from local precision effects.
        if stage in ['round1','round2']:
            w,loc,rr=c.run('common_start32_'+stage,(a/'input.mod').read_text(),(a/'input.sta').read_text(),(a/'input.cnv').read_text(),ids,bits=32,corrections=stage=='round2')
            record['common_start'].append(dict(stage=stage,change=c.compare(ca,loc),run=rr,log=log_metrics(w)))
    # Instrument only a copy of generic code, before factorization. Dump the
    # damped normal matrix; no change to equations, branching, or saved inputs.
    source=(ROOT/'build/velest-portable.f').read_text()
    needle='      call LUDECP(g,g,nvar,d1,d2,ier)'
    assert source.count(needle)>=1
    source=source.replace(needle,"      open(77,file='normal_matrices.txt',status='unknown',\n     &     position='append')\n      write(77,*) nitt,nvar\n      write(77,*) (g(k),k=1,nvar*(nvar+1)/2)\n      close(77)\n"+needle,1)
    instrument=ROOT/'build/velest-matrix-diagnostic.f';instrument.write_text(source)
    matrices=[]
    for bits in [32,64]:
        binary=ROOT/f'build/velest_matrix{bits}'
        cmd=['gfortran','-std=legacy','-O2','-fcheck=bounds']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I',str(ROOT/'build'),str(instrument),'-o',str(binary)]
        subprocess.run(cmd,check=True,capture_output=True)
        w=WORK/f'matrix{bits}';w.mkdir(exist_ok=True)
        for f in ['input.mod','input.sta','input.cnv','velest.cmn']:shutil.copyfile(original/'caldera_prelocation'/f,w/f)
        (w/'normal_matrices.txt').unlink(missing_ok=True)
        r=subprocess.run([str(binary)],cwd=w,capture_output=True,text=True,timeout=300);(w/'console.log').write_text(r.stdout+r.stderr);r.check_returncode()
        assert (w/'output.cnv').read_bytes()==(original/('caldera_prelocation' if bits==64 else 'precision32_prelocation')/'output.cnv').read_bytes()
        tokens=iter((w/'normal_matrices.txt').read_text().split())
        while True:
            try:iteration=int(next(tokens));n=int(next(tokens))
            except StopIteration:break
            values=np.array([float(next(tokens)) for _ in range(n*(n+1)//2)])
            a=np.zeros((n,n));ix=np.tril_indices(n);a[ix]=values;a+=np.tril(a,-1).T;eig=np.linalg.eigvalsh(a)
            matrices.append(dict(bits=bits,iteration=iteration,unknowns=n,min_eigenvalue=float(eig[0]),max_eigenvalue=float(eig[-1]),condition_number=float(eig[-1]/eig[0])))
    pd.DataFrame(matrices).to_csv(OUT/'normal_matrix_condition.csv',index=False)
    record['instrumentation']=dict(source_sha256=c.sha(instrument),equations_changed=False,output_identity_check=True,condition_number_range=[min(x['condition_number'] for x in matrices),max(x['condition_number'] for x in matrices)])
    # Every fifth candidate in chronological order is withheld, independent of
    # a reference catalog. Refit the same sequence with the remaining events.
    blocks=re.split(r'\n\s*\n',(original/'caldera_prelocation/input.cnv').read_text().strip())
    hold=ids[::5];train=[i for i in ids if i not in hold]
    def cnv(selected):return '\n\n'.join(b for i,b in zip(ids,blocks) if i in selected)+'\n\n'
    model=(original/'caldera_prelocation/input.mod').read_text();sta=(original/'caldera_prelocation/input.sta').read_text()
    record['heldout'].update(training_events=len(train),heldout_events=len(hold),selection='Every fifth chronological calibration candidate; no external catalog.')
    try:
        w,loc,r=c.run('heldout_train_prelocation',model,sta,cnv(train),train,fixed=True,iterations=14)
        w,loc,r=c.run('heldout_train_round1',model,sta,(w/'output.cnv').read_text(),train)
        for name in ['round2','convergence1','convergence2','convergence3']:
            w,loc,r=c.run('heldout_train_'+name,(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),train,corrections=True)
        for name,mod,st in [('starting',model,sta),('fitted',(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()))]:
            _,_,rr=c.run('heldout_'+name,mod,st,cnv(hold),hold,corrections=True,fixed=True,iterations=21);record['heldout'][name]=rr
    except Exception as exc:record['heldout']['error']=repr(exc)
    record['interpretation']='Identical initial numerical inputs, observation order, control settings and stopping rules. Paths diverge during fixed-model prelocation and subsequent coupled updates. The saved stage logs and same-start trials distinguish branching from upstream propagation. Two-decimal model/depth output serialization also propagates differences between restarts. No acceptance threshold is changed; held-out improvement is assessed separately from path robustness.'
    record['sources']={str(p.relative_to(ROOT)):c.sha(p) for p in [BASE/'filtered_events.csv',BASE/'independent_calibrated.mod',BASE/'validation.json']}
    write('summary.json',record);print(json.dumps(record,indent=2))

if __name__=='__main__':main()
