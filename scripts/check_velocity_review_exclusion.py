"""One training-only sensitivity: omit a visually ambiguous coda association.

Event 1532 is not declared false. This tests its leverage without editing any
arrival or dropping any 2025 holdout event. It cannot override the failed
initialization/selection stability tests of the registered model family.
"""
import json
from pathlib import Path
import pandas as pd,numpy as np
import calibration_chain as c,run_velest as v
import test_velocity_parameterizations as t
from estimate_observational_profile import canonical_cnv,station_delta
R=c.ROOT;D=R/'data/velocity_holdout_review';O=D/'coda_sensitivity';W=R/'tmp/velocity_holdout_review/coda_sensitivity'
def main():
    O.mkdir(exist_ok=True);W.mkdir(parents=True,exist_ok=True);c.OUT=O;c.WORK=W;v.controls=t.controls;t.SETTINGS['velocity_damping']=1.
    C=R/'data/availability_extension/catalog_december';p=pd.read_csv(C/'picks.csv');a=pd.read_csv(C/'associations.csv')
    train=pd.read_csv(D/'training_cap5.csv');assert 1532 in set(train.event_index)
    train=train[train.event_index!=1532];train.to_csv(O/'training_events.csv',index=False)
    hold=pd.read_csv(D/'holdout_events.csv');assert not set(train.event_index)&set(hold.event_index)
    aliases=pd.read_csv(D/'station_aliases.csv');alias=dict(zip(aliases.id,aliases.alias));ids=train.event_index.tolist()
    src=R/'tmp/velocity_holdout_review/runs/three_zero_delays_base_prelocation'
    model=(src/'input.mod').read_text();sta=(src/'input.sta').read_text();cnv=canonical_cnv(train,p,a,alias)
    rec=dict(reason=__doc__,excluded_training_event=1532,review='data/velocity_holdout_review/review/event_1532.png',training_events=len(train),holdout_sha256=c.sha(D/'frozen_holdout.cnv'),accepted=False,runs=[],inputs={str(f.relative_to(R)):c.sha(f) for f in [D/'training_cap5.csv',D/'frozen_holdout.cnv',C/'picks.csv',C/'associations.csv',Path(__file__)]})
    w,loc,r=c.run('prelocation',model,sta,cnv,ids,fixed=True,iterations=21);rec['runs'].append(r);cnv=(w/'output.cnv').read_text()
    for stage in ['velocity_only','joint1','joint2','joint3','joint4','joint5']:
        old=loc
        w,loc,r=c.run(stage,model,sta,cnv,ids,corrections=False,iterations=14);model=(w/'velout.mod').read_text();cnv=(w/'output.cnv').read_text();r['location_change']=c.compare(old,loc);rec['runs'].append(r)
    (O/'fitted.mod').write_text(model);v.model_table(w/'velout.mod').to_csv(O/'profile.csv',index=False)
    hw,hl,hr=c.run('holdout',model,sta,(D/'frozen_holdout.cnv').read_text(),hold.event_index.tolist(),fixed=True,iterations=35);rec['holdout']=hr
    ew,el,er=c.run('holdout_extra',model,sta,(hw/'output.cnv').read_text(),hold.event_index.tolist(),fixed=True,iterations=35);er['location_change']=c.compare(hl,el);rec['holdout_extra']=er
    rec['difference_from_all_training']=c.compare(pd.read_csv(D/'three_zero_delays_base_holdout_fitted_locations.csv'),hl)
    rec['holdout_unchanged']=c.sha(D/'frozen_holdout.cnv')==rec['holdout_sha256'];assert rec['holdout_unchanged']
    (O/'summary.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))
if __name__=='__main__':main()
