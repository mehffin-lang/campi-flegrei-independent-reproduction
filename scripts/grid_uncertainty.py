"""Validate saved two-round relocation and run conditional regional SVD fits."""
import json,os
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pyproj import Geod
import relocation_followup as rf
import run_velest as v
ROOT=rf.ROOT;BASE=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration')/'merged4';T=BASE/'tomodd';OUT=BASE/'uncertainty'

def main():
    OUT.mkdir(exist_ok=True)
    a=pd.read_csv(T/'round1_locations.csv').set_index('event_index');b=pd.read_csv(T/'round2_locations.csv').set_index('event_index');a=a.loc[b.index]
    _,_,distance=Geod(ellps='WGS84').inv(a.longitude.to_numpy(),a.latitude.to_numpy(),b.longitude.to_numpy(),b.latitude.to_numpy())
    changes=pd.DataFrame(dict(event_index=b.index,horizontal_change_m=distance,depth_change_km=b.depth_km.to_numpy()-a.depth_km.to_numpy(),gap_deg=b.gap_deg,cc_count=b.ncc_p+b.ncc_s))
    changes.to_csv(OUT/'round_changes.csv',index=False)
    stats=dict(common_events=len(b),max_horizontal_m=float(distance.max()),median_horizontal_m=float(np.median(distance)),max_depth_km=float(changes.depth_change_km.abs().max()),median_absolute_depth_km=float(changes.depth_change_km.abs().median()),
               gap_passing=int((b.gap_deg<=300).sum()),zero_cc_events=int(((b.ncc_p+b.ncc_s)==0).sum()),more_than_100_cc=int(((b.ncc_p+b.ncc_s)>100).sum()),
               interpretation='Between-round changes test stability; LSQR errors are not SVD uncertainties. Different accepted observations prevent treating aggregate RMS change as a like-for-like fit improvement.')
    tables=[]
    for n in [1,2]:
        r=pd.read_csv(T/f'round{n}_residuals.csv');r=r[r.weight>0]
        # Stable key includes phase type and station; absolute constraints have
        # event_a == event_b. Preserve all rows without collapsing duplicates.
        assert not r.duplicated(['event_a','event_b','alias','phase_index']).any()
        tables.append(r)
    common=tables[0].merge(tables[1],on=['event_a','event_b','alias','phase_index'],suffixes=('_1','_2'))
    common.to_csv(OUT/'matched_round_residuals.csv',index=False)
    stats['matched_observations']={label:dict(n=len(r),round1_rms_s=float(np.sqrt(np.mean(r.residual_ms_1**2))/1000),round2_rms_s=float(np.sqrt(np.mean(r.residual_ms_2**2))/1000)) for label,r in [('cc',common[common.phase_index<=2]),('picked',common[common.phase_index>2])]}
    picks=pd.read_csv(T/'retained_picks.csv');events=b[b.gap_deg<=300].copy();events.to_csv(OUT/'relocated_events.csv')
    rf.OUT=BASE;rf.D=ROOT/os.environ.get('CF_OBSERVATIONS','data/calibration_followup/expanded');rf.DEST=OUT;rf.RUN_ROOT=ROOT/os.environ.get('CF_GRID_WORK','tmp/grid_calibration')/'uncertainty'
    model=v.model_table(BASE/'independent_calibrated.mod');model.to_csv(OUT/'model.csv',index=False);rf.MODEL_PATH=OUT/'model.csv'
    aliases=pd.read_csv(BASE/'station_aliases.csv').set_index('alias');ct=pd.read_csv(T/'phase_pair_times.csv');cc=pd.read_csv(T/'accepted_differential_times.csv')
    # These numerical masks are explicit alternatives because the original
    # regional selection boundaries are not supplied numerically. No graph is digitized.
    masks={'Central':(events.latitude>=40.82)&(events.longitude<14.14),'North':(events.latitude>=40.82)&(events.longitude>=14.14),'Southwest':(events.latitude<40.82)&(events.longitude<14.14),'East':(events.latitude<40.82)&(events.longitude>=14.14)}
    results=[];runs=[]
    for region,mask in masks.items():
        group=events[mask];ids=group.index.tolist();index={e:i for i,e in enumerate(ids)}
        pairs=ct[ct.event_a.isin(ids)&ct.event_b.isin(ids)].groupby(['event_a','event_b']).size();pairs=pairs[pairs>=6]
        graph=coo_matrix((np.ones(len(pairs)),([index[a] for a,b in pairs.index],[index[b] for a,b in pairs.index])),shape=(len(ids),len(ids)))
        if not ids:runs.append(dict(region=region,starting_events=0,error='No provisional relocated events in this explicit region'));continue
        n,labels=connected_components(graph,directed=False)
        for k in range(n):
            subset=group.iloc[np.flatnonzero(labels==k)];name=f'svd_{region}_{k}'
            if len(subset)<4:runs.append(dict(region=region,component=k,starting_events=len(subset),error='Fewer than four connected events for regional SVD'));continue
            out,r=rf.execute(name,subset,aliases,ct,cc,svd=True);r.update(region=region,component=k);runs.append(r)
            if out is not None:
                out=out.reset_index();out['region']=region;out['component']=k
                out['finite_positive_errors']=(out[['error_x_m','error_y_m','error_z_m']]>0).all(axis=1)
                results.append(out)
    combined=pd.concat(results,ignore_index=True) if results else pd.DataFrame(columns=['event_index','region','error_x_m','error_y_m','error_z_m'])
    combined.to_csv(OUT/'regional_svd.csv',index=False)
    stats.update(svd_runs=runs,svd_events=len(combined),masks={k:'longitude 14.14 E and latitude 40.82 N quadrant boundary; explicit alternative to unspecified paper masks' for k in masks},
        uncertainty='Generic HypoDD SVD reported 2-sigma errors in m; includes conditional measurement covariance, excludes velocity-grid/calibration/association/systematic bias. Every >=4-event six-phase-linked component attempted, not only the largest.',
        sources={str(p.relative_to(ROOT)):rf.sha(p) for p in [T/'round1_locations.csv',T/'round2_locations.csv',T/'phase_pair_times.csv',T/'accepted_differential_times.csv',BASE/'independent_calibrated.mod']})
    (OUT/'summary.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
