"""Whole-cohort five-pass location trial using the new own provisional model.

No scientific acceptance is inferred from residual/pick/gap filter passage.
Do not promote this catalog into empirical inference when validation fails.
"""
import argparse,json,os
from pathlib import Path
import pandas as pd
import estimate_observational_profile as ep
c=ep.c;v=ep.v;ROOT=c.ROOT
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--observations',default='data/availability_extension/catalog');ap.add_argument('--profile',default='data/availability_extension/velocity_expanded');a=ap.parse_args();D=ROOT/a.observations;P=ROOT/a.profile;O=D/'locations_observational';O.mkdir(exist_ok=True);W=ROOT/'tmp/availability_extension'/D.name/'locations_observational';W.mkdir(parents=True,exist_ok=True);c.OUT=O;c.WORK=W;v.controls=ep.controls
    summary=json.loads((P/'summary.json').read_text());trial='all_training' if summary['runs'].get('all_training',{}).get('last_change_gate') else 'base'
    model=(P/(trial+'_fitted.mod')).read_text();sta=(P/(trial+'_fitted.sta')).read_text();aliases=pd.read_csv(P/'station_aliases.csv').set_index('id').alias.to_dict()
    ev=pd.read_csv(D/'initial_events.csv');q=pd.read_csv(D/'selection/input_quality.csv');ev=ev[ev.event_index.isin(q[q.causal].event_index)].sort_values('time');p=pd.read_csv(D/'picks.csv');assign=pd.read_csv(D/'associations.csv');assign=assign[assign.event_index.isin(ev.event_index)]
    missing=sorted(set(p.iloc[assign.pick_index].trace_id)-set(aliases))
    if missing:raise ValueError('Uncalibrated station aliases require explicit zero-delay augmentation: '+str(missing))
    ids=ev.event_index.tolist();text=v.cnv(ev,p,assign,aliases)
    rec=dict(accepted=False,profile_trial=trial,selection_reason='Prefer full training fit only if its iteration-change gate passes; otherwise retain predeclared balanced base. Holdout never chooses the preferred fit.',model=str((P/(trial+'_fitted.mod')).relative_to(ROOT)),model_sha256=c.sha(P/(trial+'_fitted.mod')),profile_validated=summary['accepted'],input_events=len(ev),runs=[],status='running provisional whole-catalog calculation')
    for n in range(1,6):
        if n in [4,5]:text,ids,reject=v.reject_residuals(w,ids,.4 if n==4 else .3);rec.setdefault('rejections',[]).append(reject)
        w,loc,r=c.run(f'pass{n}',model,sta,text,ids,corrections=True,fixed=True,iterations=7);text=(w/'output.cnv').read_text();rec['runs'].append(r);(O/'summary.json').write_text(json.dumps(rec,indent=2)+'\n')
    loc['paper_filter_pass']=(loc.num_picks>=6)&(loc.rms_s<=.25)&(loc.azimuthal_gap_deg<=300);loc.to_csv(O/'located_events.csv',index=False);loc[loc.paper_filter_pass].to_csv(O/'filtered_events.csv',index=False);(O/'located_events.cnv').write_text(text)
    rec.update(status='five passes executed; provisional, not a validated catalog',filtered_events=int(loc.paper_filter_pass.sum()),downstream='This model fails validation unless profile_validated is true. Existing fixed-grid TomoDD results remain a separately identified older checkpoint; they are not relabeled as relocations of this trial.')
    (O/'summary.json').write_text(json.dumps(rec,indent=2)+'\n')
if __name__=='__main__':main()
