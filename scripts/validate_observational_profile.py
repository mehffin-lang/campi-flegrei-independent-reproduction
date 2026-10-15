"""Explain internal validation using saved observed-arrival residuals only."""
from pathlib import Path
import argparse,json,re
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/availability_extension/velocity_existing';W=ROOT/'tmp/availability_extension/velocity_existing'
def residuals(name):
    work=W/name;blocks=re.split(r'\n\s*\n',(work/'output.cnv').read_text().strip());rows=[]
    for event,block in enumerate(blocks):
        for line in block.splitlines()[1:]:
            for i in range(0,len(line),12):
                t=line[i:i+12]
                if t.strip():rows.append(dict(event_ordinal=event,alias=t[:4],phase=t[4]))
    arr=np.loadtxt(work/'residuals.txt',ndmin=2)[:,1];assert len(arr)==len(rows)
    frame=pd.DataFrame(rows);frame['residual_s']=arr;return frame
def main():
    global D,W
    ap=argparse.ArgumentParser();ap.add_argument('--profile',default='data/availability_extension/velocity_existing');args=ap.parse_args();D=ROOT/args.profile;W=ROOT/'tmp/availability_extension'/D.name
    aliases=pd.read_csv(D/'station_aliases.csv').set_index('alias').id
    rows=[]
    for trial in ['base','slow','fast','precision32','all_training','smaller_step']:
        train=residuals(trial+'_convergence3').groupby(['alias','phase']).size()
        a=residuals(trial+'_holdout_initialization');b=residuals(trial+'_holdout_fitted');assert a[['event_ordinal','alias','phase']].equals(b[['event_ordinal','alias','phase']])
        a['fitted_residual_s']=b.residual_s;a['training_phase_count']=[int(train.get((r.alias,r.phase),0)) for r in a.itertuples()];a['station']=a.alias.map(aliases);a.to_csv(D/(trial+'_holdout_paired_residuals.csv'),index=False)
        for (station,phase),g in a.groupby(['station','phase']):
            rows.append(dict(trial=trial,station=station,phase=phase,holdout_picks=len(g),training_picks=int(g.training_phase_count.iloc[0]),initial_rms_s=float(np.sqrt(np.mean(g.residual_s**2))),fitted_rms_s=float(np.sqrt(np.mean(g.fitted_residual_s**2))),fitted_mean_s=float(g.fitted_residual_s.mean())))
    table=pd.DataFrame(rows);table.to_csv(D/'holdout_station_phase.csv',index=False)
    details={}
    for trial in table.trial.unique():
        g=pd.read_csv(D/(trial+'_holdout_paired_residuals.csv'));details[trial]={}
        for label,mask in [('seen_in_training',g.training_phase_count.gt(0)),('unseen_in_training',g.training_phase_count.eq(0))]:
            h=g[mask];details[trial][label]=dict(phases=len(h),station_phase_pairs=len(h[['station','phase']].drop_duplicates()),initial_rms_s=float(np.sqrt(np.mean(h.residual_s**2))),fitted_rms_s=float(np.sqrt(np.mean(h.fitted_residual_s**2))))
    (D/'holdout_support.json').write_text(json.dumps(details,indent=2)+'\n')
    P=ROOT/'data/availability_extension/precision';r=[];updates=[]
    for bits in [32,64]:
        for l in (P/f'trace{bits}.txt').read_text().splitlines():
            f=l.split()
            if f[0]=='DIAG_UPDATE':updates.append(dict(bits=bits,iteration=int(f[1]),dt_s=float(f[2]),dx_km=float(f[3]),dy_km=float(f[4]),dz_km=float(f[5])))
            else:r.append(dict(bits=bits,iteration=int(f[1]),backup=int(f[2]),event_ordinal=int(f[3]),phase_ordinal=int(f[4]),ray_type=int(f[5]),layer=int(f[6]),x=float(f[7]),y=float(f[8]),z=float(f[9]),distance=float(f[10]),travel_s=float(f[11])))
    pd.DataFrame(r).to_csv(P/'ray_paths.csv',index=False);pd.DataFrame(updates).to_csv(P/'updates.csv',index=False)
    rays=pd.DataFrame(r);u=pd.DataFrame(updates);info=json.loads((P/'instrumentation.json').read_text());both=rays[rays.bits.eq(32)].merge(rays[rays.bits.eq(64)],on=['iteration','backup','event_ordinal','phase_ordinal'],suffixes=('_32','_64'));first=both[both.ray_type_32.ne(both.ray_type_64)].sort_values(['iteration','phase_ordinal']).iloc[0]
    step=u[u.iteration.eq(first.iteration+1)].set_index('bits');old=ROOT/'tmp/eida_continuation/merged4/Pozzuoli_Solfatara_prelocation/input.cnv';block=re.split(r'\n\s*\n',old.read_text().strip())[info['event_ordinal']-1];tokens=[line[i:i+12] for line in block.splitlines()[1:] for i in range(0,len(line),12) if line[i:i+12].strip()];token=tokens[int(first.phase_ordinal)-1];sta=pd.read_csv(ROOT/'data/eida_continuation/calibration/merged4/station_aliases.csv').set_index('alias').id[token[:4]]
    evidence=dict(event_index=info['event_index'],event_ordinal=info['event_ordinal'],phase_ordinal=int(first.phase_ordinal),phase=token[4],station=sta,first_large_divergence_iteration=int(first.iteration+1),branch_difference_iteration=int(first.iteration),branch32=int(first.ray_type_32),branch64=int(first.ray_type_64),depth_before32_km=float(first.z_32),depth_before64_km=float(first.z_64),depth_step32_km=float(step.loc[32,'dz_km']),depth_step64_km=float(step.loc[64,'dz_km']),source='build/velest-sparse.f RAYPATH, lines 8480–8503: tref<tdir selects refraction (6); direct otherwise (7).',interpretation='A direct/head-wave crossover amplifies small geometric/arithmetic differences through the travel-time derivative. Same inputs and unchanged diagnostic arithmetic reproduce saved files exactly. This identifies one first large path divergence; it does not prove every later discrepancy has this sole cause. No arbitrary branch tie-break or relaxed acceptance gate was adopted.')
    (P/'diagnosis.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(details,indent=2))
if __name__=='__main__':main()
