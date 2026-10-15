"""Post-fit consistency and support statistics; no fitting or model selection."""
import re,json
import numpy as np,pandas as pd
from extend_velocity_training import R,D,dump

def main():
    F=D/'fits';W=R/'tmp/velocity_holdout_review'/D.name/'fits'
    aliases=pd.read_csv(R/'data/velocity_holdout_review/station_aliases.csv').set_index('alias').id
    rows=[];checks=[]
    for family in ['four_regularized','three_regularized','three_zero_delays']:
        name=family+'_base';tr=pd.read_csv(F/(name+'_training_residuals.csv'));counts=tr.groupby(['alias','phase']).size()
        a=pd.read_csv(F/(name+'_holdout_initialization_residuals.csv'));b=pd.read_csv(F/(name+'_holdout_fitted_residuals.csv'));assert a[['event_index','alias','phase']].equals(b[['event_index','alias','phase']])
        a['fitted_residual_s']=b.residual_s;a['training_count']=[int(counts.get((r.alias,r.phase),0)) for r in a.itertuples()];a['station']=a.alias.map(aliases)
        for label,g in a.groupby(a.training_count.gt(0).map({True:'represented',False:'unrepresented'})):
            rows.append(dict(family=family,support=label,arrivals=len(g),station_phase_pairs=len(g[['station','phase']].drop_duplicates()),initial_rms_s=float(np.sqrt(np.mean(g.residual_s**2))),fitted_rms_s=float(np.sqrt(np.mean(g.fitted_residual_s**2)))))
        work=W/(name+'_joint5');rays=pd.read_csv(F/(name+'_joint5_rays.csv'));model=pd.read_csv(F/(name+'_profile.csv'))
        speed={(ph,t):v for ph,col in [('P','Vp_km_s'),('S','Vs_km_s')] for t,v in zip(model.layer_top_km,model[col])}
        rays['travel_s']=[r.ray_length_km/speed[(r.phase,r.layer_top_km)] for r in rays.itertuples()];travel=rays.groupby(['event_index','alias','phase']).travel_s.sum()
        delay={(l[:4],ph):float(l[x:y]) for l in (work/'output.sta').read_text().splitlines()[1:] if l[:4].strip() for ph,x,y in [('P',34,39),('S',41,46)]}
        blocks=re.split(r'\n\s*\n',(work/'output.cnv').read_text().strip());times=[float(token[6:12]) for block in blocks for line in block.splitlines()[1:] for token in [line[j:j+12] for j in range(0,len(line),12)] if token.strip()]
        assert len(times)==len(tr)
        delta=[obs-travel[(r.event_index,r.alias,r.phase)]-delay[(r.alias,r.phase)]-r.residual_s for r,obs in zip(tr.itertuples(),times)]
        checks.append(dict(family=family,arrivals=len(times),ray_travel_vs_serialized_residual_rms_s=float(np.sqrt(np.mean(np.array(delta)**2))),max_abs_s=float(np.max(np.abs(delta))),note='Independent layerwise travel-time sum with station delays; native vertices/velocities/arrival times rounded. Not a test of true phase identity.'))
    pd.DataFrame(rows).to_csv(D/'evaluation_only_support.csv',index=False);dump(D/'ray_consistency.json',checks);print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
