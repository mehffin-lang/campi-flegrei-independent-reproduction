"""Compare numerical vertical travel times to exact layered-ray integrals."""
from pathlib import Path
import copy,json,os
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2')
import numpy as np
import pandas as pd
from gamma.seismic_ops import initialize_eikonal,calc_time
D=ROOT/'data/continuation';table=pd.read_csv(D/'alternative_starting_profile.csv')
base=json.loads((ROOT/'config/continuation_association.json').read_text())['eikonal']
rows=[]
for spacing in [.1,.05]:
    cfg=copy.deepcopy(base);cfg['h']=spacing;eik=initialize_eikonal(cfg)
    for phase,column in [('p','vp_km_s'),('s','vs_km_s')]:
        for depth in [.25,.75,2.,4.,6.]:
            tops=table.depth_top_km_bsl.to_numpy();bottoms=np.r_[tops[1:],np.inf]
            exact=float(np.sum(np.maximum(0,np.minimum(depth,bottoms)-tops)/table[column].to_numpy()))
            actual=float(calc_time(np.array([[0.,0.,depth,0.]]),np.array([[0.,0.,0.]]),np.array([phase]),eikonal=eik)[0,0])
            rows.append(dict(grid_km=spacing,phase=phase,depth_km=depth,analytic_s=exact,numerical_s=actual,error_s=actual-exact))
frame=pd.DataFrame(rows);frame.to_csv(D/'profile_ray_checks.csv',index=False)
maxerr=frame.groupby(['grid_km','phase']).error_s.apply(lambda x:float(abs(x).max()))
checks={}
for phase,column in [('p','vp_km_s'),('s','vs_km_s')]:
    # A vertical path samples each discontinuity once. First-order grid bias
    # must fit within one grid-cell time at the slowest speed and decrease on
    # refinement; neither tolerance uses a published result.
    checks[phase+'_grid_error_bound']=bool(maxerr.loc[(.1,phase)]<.1/table[column].min())
    checks[phase+'_refinement']=bool(maxerr.loc[(.05,phase)]<.55*maxerr.loc[(.1,phase)])
assert all(checks.values()),checks
summary=dict(checks=checks,max_coarse_P_error_s=maxerr.loc[(.1,'p')],max_coarse_S_error_s=maxerr.loc[(.1,'s')],max_fine_P_error_s=maxerr.loc[(.05,'p')],max_fine_S_error_s=maxerr.loc[(.05,'s')],
    scope='Numerical vertical layered-ray consistency and refinement only; does not establish the alternative profile as the exact 2018 model or validate earthquake locations.')
(D/'profile_ray_checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
