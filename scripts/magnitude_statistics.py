"""Completeness and likelihood b estimates from independently measured magnitudes.

Small, noncontinuous pilot exposure cannot establish multiyear completeness.
Duration magnitudes are calibration inputs, not an independent validation set.
"""
from pathlib import Path
import json,argparse,os
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/continuation'
parser=argparse.ArgumentParser();parser.add_argument('--grid',action='store_true');args=parser.parse_args()
if args.grid:D=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration')/'merged4/magnitude'
m=pd.read_csv(D/'magnitudes.csv');ref=pd.read_csv(D/'routine_matches.csv')
(D/'figure_S8B.csv').unlink(missing_ok=True)
joint=m.merge(ref,on='event_index').dropna(subset=['ML','Md']);joint.to_csv(D/'figure_S8A.csv',index=False)
result=dict(magnitudes=len(m),matched_Md=len(joint),bin_width=.1,Mc=None,b=None,status='Not estimable without independently measured magnitudes',full_catalog_completeness=False)
if len(m):
    # Round bin centers to 0.1, matching the stated maximum-curvature estimator.
    values=np.round(m.ML.to_numpy()/.1)*.1
    centers=np.arange(np.floor(values.min()*10)/10,np.ceil(values.max()*10)/10+.05,.1)
    edges=np.r_[centers-.05,centers[-1]+.05]
    counts,_=np.histogram(values,bins=edges)
    pd.DataFrame(dict(ML_bin=centers,count=counts,cumulative=np.cumsum(counts[::-1])[::-1])).to_csv(D/'figure_S8B.csv',index=False)
    mc=float(centers[np.argmax(counts)]);above=values[values>=mc-1e-8]
    result.update(Mc=mc,events_ge_Mc=len(above),status='Pilot maximum-curvature estimate; acquisition and magnitude selection incomplete')
    if len(above):
        b=float(np.log10(np.e)/(above.mean()-(mc-.05)))
        sigma=float(2.30*b*b*np.sqrt(np.sum((above-above.mean())**2)/(len(above)*(len(above)-1)))) if len(above)>1 else None
        result.update(b=b,b_sigma=sigma,estimator='Aki--Utsu maximum likelihood with half-bin correction; Shi--Bolt sampling error; does not include coverage/systematic errors')
        result['b_caveat']=f'Conditional descriptive estimate from only {len(above)} selected pilot magnitudes. Neither population completeness nor the regional b-value is established; the formal error excludes selection, magnitude calibration and coverage bias.'
(D/'magnitude_statistics.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
