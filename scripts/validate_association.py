"""Recover an analytically specified event; do not use author results as targets."""
import os,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2')
import numpy as np
import pandas as pd
from gamma.utils import association
cfg=json.loads(Path('config/continuation_association.json').read_text());cfg['eikonal']=None;cfg['vel']={'p':4.,'s':2.}
xyz=np.array([[4*np.cos(a),4*np.sin(a),0.] for a in np.arange(8)*np.pi/4])
sta=pd.DataFrame(xyz,columns=cfg['dims']);sta['id']=['T'+str(i) for i in range(8)]
truth=np.array([.5,-.5,2.]);origin=pd.Timestamp('2024-01-01',tz='UTC');p=[]
for ident,point in zip(sta.id,xyz):
    for phase,v in cfg['vel'].items():
        p.append(dict(id=ident,type=phase,prob=1.,timestamp=origin+pd.Timedelta(seconds=np.linalg.norm(point-truth)/v)))
events,assignments=association(pd.DataFrame(p),sta,copy.deepcopy(cfg))
assert len(events)==1,(events,assignments)
e=events[0];error=float(np.linalg.norm(np.array([e[k] for k in cfg['dims']])-truth))
time_error=abs((pd.Timestamp(e['time'],tz='UTC')-origin).total_seconds())
assert error<.02 and time_error<.005 and len(assignments)==16
result=dict(events=len(events),assignments=len(assignments),location_error_km=error,origin_error_s=time_error,passed=True,
    scope='Analytic homogeneous-medium association check, not observational accuracy or validation of alternative 1D profile')
Path('tests/results/association_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
