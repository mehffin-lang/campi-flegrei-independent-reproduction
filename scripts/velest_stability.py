"""Exploratory arithmetic check with the published 2021 alternative only.

No fitted output here is accepted as a scientific location or velocity result.
The same observation subset, input serialization, damping and compiler -O2
are used for both real precisions. No quarantined background grid is read.
"""
from pathlib import Path
import json,subprocess,shutil
import numpy as np
import pandas as pd
from obspy import UTCDateTime
import run_velest as v

ROOT=v.ROOT;D=ROOT/'data/continuation';OUT=ROOT/'data/exploratory/velest_stability'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for bits in [32,64]:
        for name in [f'raw_model_{bits}.txt',f'model_{bits}.csv',f'locations_{bits}.csv']:
            (OUT/name).unlink(missing_ok=True)
    events=pd.read_csv(D/'initial_events.csv');picks=pd.read_csv(D/'picks.csv')
    assignments=pd.read_csv(D/'associations.csv');quality=pd.read_csv(D/'location_quality.csv');stations=pd.read_csv(D/'stations.csv')
    origins={r.event_index:float(UTCDateTime(r.time)) for r in events.itertuples()}
    travel=np.array([float(UTCDateTime(picks.iloc[int(r.pick_index)].time))-origins[r.event_index] for r in assignments.itertuples()])
    assignments=assignments[(travel>0)&(travel<999)].copy()
    count=assignments.groupby('event_index').size()
    eligible=set(quality.loc[quality.calibration_eligible,'event_index'])&set(count[count>6].index)
    # Keep the whole currently eligible set within the generic compiled capacity.
    events=events[events.event_index.isin(eligible)].sort_values('time').copy()
    record=dict(scope='Exploratory alternative-profile precision experiment; not S6 or Table S1',accepted_independent_result=False,
                starting_profile='data/continuation/alternative_starting_profile.csv',selection='Positive travel time; >6 picks and initial azimuthal gap <180 degrees; not manually reviewed',events=len(events),runs=[])
    if len(events)<5 or len(events)>1024:
        record['blocker']='Current eligible sample outside 5--1024 event capacity.'
        (OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n');return
    assignments=assignments[assignments.event_index.isin(eligible)]
    stations=stations[stations.id.isin(picks.iloc[assignments.pick_index.to_numpy(int)].trace_id)].sort_values('id')
    aliases={ident:f'S{i:03d}' for i,ident in enumerate(stations.id)}
    counts=picks.iloc[assignments.pick_index.to_numpy(int)].groupby('trace_id').size();reference=counts.idxmax()
    order=[s for s in stations.id if s!=reference]+[reference];icc={s:i+1 for i,s in enumerate(order)}
    station_text=['(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)']
    for r in stations.to_dict('records'):
        station_text.append(f'{aliases[r["id"]]:4s}{r["latitude"]:7.4f}N {r["longitude"]:8.4f}E {round(-r["z(km)"]*1000):4d} 1 {icc[r["id"]]:3d} {0.:5.2f}  {0.:5.2f}')
    station_text='\n'.join(station_text)+'\n\n';cnv=v.cnv(events,picks,assignments,aliases)
    profile=pd.read_csv(D/'alternative_starting_profile.csv');profile.loc[0,'depth_top_km_bsl']=-.5
    text=['Exploratory Tramelli2021 Table1; top extended to -0.5 km; no 2008 grid']
    for column in ['vp_km_s','vs_km_s']:
        text.append(str(len(profile)))
        text.extend(f'{r[column]:5.2f}     {r["depth_top_km_bsl"]:7.2f}  {1.:7.3f}' for r in profile.to_dict('records'))
    model='\n'.join(text)+'\n';events.to_csv(OUT/'selected_initial_events.csv',index=False)
    fits={}
    for bits in [32,64]:
        binary=ROOT/'build'/f'velest{bits}'
        command=['gfortran','-std=legacy','-O2','-fcheck=bounds']+(['-fdefault-real-8','-fdefault-double-8'] if bits==64 else [])+['-I','build','build/velest-portable.f','-o',str(binary)]
        compile_run=subprocess.run(command,capture_output=True,text=True);compile_run.check_returncode()
        work=ROOT/'tmp/continuation'/f'velest_stability_{bits}'
        if work.exists():shutil.rmtree(work)
        work.mkdir()
        for name,content in [('input.mod',model),('input.sta',station_text),('input.cnv',cnv),('velest.cmn',v.controls(len(events)))]:
            (work/name).write_text(content)
        try:
            r=subprocess.run([str(binary)],cwd=work,capture_output=True,text=True,timeout=180)
            (work/'console.log').write_text(r.stdout+r.stderr)
            result=dict(bits=bits,command=command,workdir=str(work.relative_to(ROOT)),returncode=r.returncode)
            if r.returncode==0 and (work/'velout.mod').exists():
                raw=(work/'velout.mod').read_text();(OUT/f'raw_model_{bits}.txt').write_text(raw)
                lines=iter(raw.splitlines());next(lines);arrays=[]
                for phase in ['P','S']:
                    count=int(next(lines));arrays.append(np.array([list(map(float,next(lines).split()[:3])) for _ in range(count)]))
                assert np.array_equal(arrays[0][:,1],arrays[1][:,1])
                fitted=pd.DataFrame(dict(layer_top_km=arrays[0][:,1],Vp_km_s=arrays[0][:,0],Vs_km_s=arrays[1][:,0]))
                fitted['VpVs']=fitted.Vp_km_s/fitted.Vs_km_s
                fitted.to_csv(OUT/f'model_{bits}.csv',index=False)
                result['physical_velocity_check']=bool((fitted.Vp_km_s>fitted.Vs_km_s).all() and (fitted.Vs_km_s>0).all())
                located=v.parse_events(work/'output.cnv',events.event_index.tolist());located.to_csv(OUT/f'locations_{bits}.csv',index=False)
                fits[bits]=(fitted,located);result['rms_s']=float(np.sqrt(np.mean(located.rms_s**2)))
            else:result['error']=(r.stdout+r.stderr)[-2000:]
        except Exception as e:result=dict(bits=bits,error=repr(e))
        record['runs'].append(result)
    if len(fits)==2:
        a,b=fits[32],fits[64]
        record['maximum_velocity_difference_km_s']={c:float(abs(a[0][c]-b[0][c]).max()) for c in ['Vp_km_s','Vs_km_s']}
        record['maximum_depth_difference_km']=float(abs(a[1].depth_km-b[1].depth_km).max())
        record['numerically_agrees_at_output_resolution']=all(x<=.0100001 for x in record['maximum_velocity_difference_km_s'].values()) and record['maximum_depth_difference_km']<=.0100001
    record['interpretation']='Precision agreement tests numerical reproducibility only; physical velocity checks are separate. Exact profile, independently reviewed phases and validated regional calibration remain missing; these fits cannot authorize TomoDD/S7 or be used as S6 results.'
    (OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':main()
