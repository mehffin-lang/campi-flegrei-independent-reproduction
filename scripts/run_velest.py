"""Run independent pilot VELEST inversions; do not substitute a Tan-fitted model.

The limited calibration sample and explicitly assumed regional boxes prevent
an exact reproduction. All control files and failure logs remain reviewable.
"""
from pathlib import Path
import json
import io
import os
import re
import shutil
import subprocess
import numpy as np
import pandas as pd
from obspy import UTCDateTime

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
D=ROOT/'data/continuation'
WORK=ROOT/'tmp/continuation/velest'


def model_table(path):
    lines=iter(path.read_text().splitlines());next(lines);phases=[]
    for phase in ['Vp','Vs']:
        n=int(next(lines));values=np.array([list(map(float,next(lines).split()[:3])) for _ in range(n)])
        assert np.all(np.diff(values[:,1])>0) and np.all(values[:,0]>0), 'Invalid physical layer values'
        phases.append(values)
    assert np.array_equal(phases[0][:,1],phases[1][:,1]), 'Vp/Vs interfaces differ'
    assert np.all(phases[0][:,0]>phases[1][:,0]), 'Nonphysical Vp <= Vs'
    return pd.DataFrame(dict(layer_top_km=phases[0][:,1],Vp_km_s=phases[0][:,0],Vs_km_s=phases[1][:,0],VpVs=phases[0][:,0]/phases[1][:,0]))


def cnv(events,picks,assign,aliases):
    lines=[]
    for e in events.to_dict('records'):
        origin=UTCDateTime(e['time']);rounded=UTCDateTime(np.floor(float(origin)*100)/100)
        # Md is an unused required CNV field. Zero is a format placeholder,
        # never exported as an independently measured magnitude.
        lines.append(f'{rounded.year%100:02d}{rounded.month:02d}{rounded.day:02d} {rounded.hour:02d}{rounded.minute:02d} {rounded.second+rounded.microsecond/1e6:5.2f} {e["latitude"]:7.4f}N {e["longitude"]:8.4f}E{e["z(km)"]:7.2f}{0.:7.2f} 0')
        ep=picks.iloc[assign.loc[assign.event_index==e['event_index'],'pick_index'].to_numpy(int)]
        tokens=[]
        for p in ep.itertuples():
            delta=UTCDateTime(p.time)-rounded
            if delta < 0 or delta>=999:raise ValueError('Invalid associated travel time')
            tokens.append(f'{aliases[p.trace_id]:4s}{p.phase}0{delta:6.2f}')
        assert len(tokens)<=180
        lines += [''.join(tokens[i:i+6]) for i in range(0,len(tokens),6)]+['']
    return '\n'.join(lines)+'\n'


def controls(n,station_corrections=False,location_only=False,iterations=7):
    values=['Independent Campi Flegrei pilot; no author-derived solution',
            '40.82 -14.14 0 0.0 0 0.0 0',f'{n} 0 0.0','0 0',
            '100.0 0 0.0 0.20 1.0 1','2 0.5 1.78 2',
            '0.01 0.01 0.01 1.0 0.1',f'{int(station_corrections and not location_only)} 0 0 1 {int(station_corrections)}',
            '0 1 2 0','0 0 0 0 0 0 1',f'0.01 {iterations} {iterations+1 if location_only else 1}',
            'input.mod','input.sta','','','','','','input.cnv','',
            'run.out','','output.cnv','output.sta','','','','','','','','residuals.txt']
    return '\n'.join(values)+'\n'


def execute(name,model,stations,event_text,n,corrections=False,location_only=False):
    capacity=json.loads((ROOT/'data/extended/velest_build.json').read_text()).get('event_capacity',658)
    if n>capacity:raise ValueError(f'{n} events exceed compiled VELEST capacity {capacity}; rebuild with suitable dimensions or implement documented fixed-model batching')
    work=WORK/name
    if work.exists():shutil.rmtree(work)
    work.mkdir(parents=True,exist_ok=True)
    (work/'input.mod').write_text(model);(work/'input.sta').write_text(stations);(work/'input.cnv').write_text(event_text)
    (work/'velest.cmn').write_text(controls(n,corrections,location_only))
    r=subprocess.run([str(ROOT/'build/velest')],cwd=work,capture_output=True,text=True,timeout=120)
    (work/'console.log').write_text(r.stdout+r.stderr)
    output=(work/'run.out').read_text(errors='replace') if (work/'run.out').exists() else ''
    valid=r.returncode==0 and all((work/name).exists() and (work/name).stat().st_size>0 for name in ['output.cnv','velout.mod','output.sta'])
    result=dict(name=name,returncode=r.returncode,valid_outputs=valid,workdir=str(work.relative_to(ROOT)),console_tail=(r.stdout+r.stderr)[-1500:])
    print(result,flush=True)
    if not valid:raise RuntimeError(json.dumps(result))
    # Upstream writes a list-directed layer count but reads that count with I3.
    # Canonicalize only the serialization; preserve the original numerical file.
    raw=(work/'velout.mod').read_text();(work/'velout.raw.mod').write_text(raw)
    source=iter(raw.splitlines());next(source);normalized=['Independent VELEST output model; normalized layer-count fields']
    for phase in ['P','S']:
        count=int(next(source));normalized.append(str(count))
        for _ in range(count):
            vp,z,damp=map(float,next(source).split()[:3]);normalized.append(f'{vp:5.2f}     {z:7.2f}  {damp:7.3f}')
    (work/'velout.mod').write_text('\n'.join(normalized)+'\n')
    return work,result


def parse_events(file,ids):
    records=[]
    blocks=re.split(r'\n\s*\n',file.read_text().strip())
    if len(blocks)!=len(ids):raise ValueError('VELEST changed event cardinality')
    for block,eid in zip(blocks,ids):
        line=block.splitlines()[0]
        # Fortran writes blank padding in i2 fields; parse by format positions.
        y,mo,d=int(line[:2]),int(line[2:4]),int(line[4:6]);hh,mm=int(line[7:9]),int(line[9:11])
        t=UTCDateTime(2000+y,mo,d,hh,0)+mm*60+float(line[12:17])
        rec=dict(event_index=int(eid),time=str(t),latitude=float(line[18:25]),longitude=float(line[27:35]),depth_km=float(line[36:43]),azimuthal_gap_deg=int(line[54:57]),rms_s=float(line[62:67]))
        records.append(rec)
    if len(records)!=len(ids):raise ValueError('VELEST changed event cardinality')
    return pd.DataFrame(records)


def reject_residuals(work,ids,threshold):
    blocks=re.split(r'\n\s*\n',(work/'output.cnv').read_text().strip())
    residuals=np.loadtxt(work/'residuals.txt',ndmin=2)[:,1]
    all_tokens=[]
    for block in blocks:
        tokens=[]
        for line in block.splitlines()[1:]:
            tokens += [line[i:i+12] for i in range(0,len(line),12) if line[i:i+12].strip()]
        all_tokens.append(tokens)
    assert sum(map(len,all_tokens))==len(residuals),(len(residuals),sum(map(len,all_tokens)))
    kept_ids=[];lines=[];i=0;removed=0;unsupported=[]
    for block,tokens,eid in zip(blocks,all_tokens,ids):
        keep=[token for token,r in zip(tokens,residuals[i:i+len(tokens)]) if abs(r)<=threshold]
        removed+=len(tokens)-len(keep);i+=len(tokens)
        # A zero/one-pick event cannot be inverted. Preserve this numerical
        # departure explicitly rather than silently passing empty events.
        if len(keep)<4:unsupported.append(int(eid));continue
        kept_ids.append(eid);lines.append(block.splitlines()[0]);lines+=[''.join(keep[j:j+6]) for j in range(0,len(keep),6)]+['']
    return '\n'.join(lines)+'\n',kept_ids,dict(threshold_s=threshold,removed_picks=removed,events_too_few_for_next_solve=unsupported)


def main():
    # No failed current solve may inherit a successful earlier output file.
    for pattern in ['velest_*.csv','velest_*.cnv','independent_velest_model.*','independent_station_corrections.sta','figure_S6.csv']:
        for path in D.glob(pattern):path.unlink()
    events=pd.read_csv(D/'initial_events.csv');picks=pd.read_csv(D/'picks.csv');assign=pd.read_csv(D/'associations.csv');q=pd.read_csv(D/'location_quality.csv');stations=pd.read_csv(D/'stations.csv')
    # Nonpositive propagation times cannot be passed as physical observations
    # to a layered ray tracer. Preserve every rejected initial association.
    origins={e['event_index']:float(UTCDateTime(e['time'])) for e in events.to_dict('records')}
    travel=np.array([float(UTCDateTime(picks.iloc[int(r.pick_index)].time))-origins[r.event_index] for r in assign.itertuples()])
    valid=(travel>0)&(travel<999)
    rejected=assign.loc[~valid].copy();rejected['observed_travel_time_s']=travel[~valid]
    rejected.to_csv(D/'velest_rejected_input_picks.csv',index=False)
    assign=assign.loc[valid].copy()
    counts=assign.groupby('event_index').size();usable=set(counts[counts>=6].index)
    events=events[events.event_index.isin(usable)].copy();assign=assign[assign.event_index.isin(usable)].copy()
    ids=[int(i) for i in q.loc[q.calibration_eligible,'event_index'] if counts.get(i,0)>6 and i in usable]
    # The generic geometry screen is recomputed after the physical-time filter.
    station_xyz=stations.set_index('id')[['x(km)','y(km)','z(km)']]
    stable=[]
    for e in events[events.event_index.isin(ids)].to_dict('records'):
        ep=picks.iloc[assign.loc[assign.event_index==e['event_index'],'pick_index'].to_numpy(int)]
        xyz=np.unique(station_xyz.loc[ep.trace_id].to_numpy(),axis=0)
        az=np.sort(np.mod(np.degrees(np.arctan2(xyz[:,0]-e['x(km)'],xyz[:,1]-e['y(km)'])),360))
        if np.diff(np.r_[az,az[0]+360]).max()<180:stable.append(e['event_index'])
    ids=stable
    selected=events[events.event_index.isin(ids)].copy()
    selected.to_csv(D/'velest_calibration_selection.csv',index=False)
    record=dict(calibration_events=len(selected),nonpositive_or_invalid_travel_times_removed=len(rejected),eligible_whole_catalog_events=len(events),selection='Positive propagation times, more than six retained picks and azimuthal gap <180 deg (generic VELEST guidance). Positive-time filtering is an explicit additional consistency rule. Pilot subset lacks full-study coverage and independent manual review; not the published 373-event selection.',runs=[],completed=False)
    if len(selected)<5:
        record['blocker']='Fewer than five geometry-qualified events; insufficient for the proposed multi-layer/station calibration pilot.'
        (D/'velest_summary.json').write_text(json.dumps(record,indent=2)+'\n');return
    used=set(picks.iloc[assign.pick_index.to_numpy(int)].trace_id)
    stations=stations[stations.id.isin(used)].sort_values('id')
    counts=picks.iloc[assign[assign.event_index.isin(ids)].pick_index.to_numpy(int)].groupby('trace_id').size()
    reference=counts.idxmax();record['reference_station']=reference
    aliases={ident:f'S{i:03d}' for i,ident in enumerate(stations.id)}
    pd.DataFrame([dict(id=k,alias=v) for k,v in aliases.items()]).to_csv(D/'velest_station_aliases.csv',index=False)
    order=[s for s in stations.id if s!=reference]+[reference]
    icc={s:i+1 for i,s in enumerate(order)}
    sta=['(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)']
    for s in stations.to_dict('records'):
        sta.append(f'{aliases[s["id"]]:4s}{s["latitude"]:7.4f}N {s["longitude"]:8.4f}E {round(-s["z(km)"]*1000):4d} 1 {icc[s["id"]]:3d} {0.:5.2f}  {0.:5.2f}')
    sta='\n'.join(sta)+'\n\n'
    averages=pd.read_csv('data/extended/background_averages.csv')
    try:
        alternatives=[]
        for region in ['caldera','central']:
            a=averages[(averages.region==region)&(averages.depth_km>=0)&(averages.depth_km<=7)].copy()
            # The fixed grid includes air cells above sea level. Do not average
            # those as crust. Extend the surface value upward and move the next
            # interface to +0.05 km so all stations lie in VELEST's top layer.
            first=a.iloc[0].copy();first.depth_km=-.5;a.loc[a.index[0],'depth_km']=.05
            a=pd.concat([first.to_frame().T,a],ignore_index=True)
            model=[f'Independent {region} average of permitted fixed external 3D grid']
            for phase in ['vp_km_s','vs_km_s']:
                model.append(str(len(a)))
                model += [f'{float(r[phase]):5.2f}     {float(r["depth_km"]):7.2f}  {1.:7.3f}' for r in a.to_dict('records')]
            model='\n'.join(model)+'\n'
            w,r=execute(region+'_round1',model,sta,cnv(selected,picks,assign,aliases),len(selected));record['runs'].append(r)
            w2,r2=execute(region+'_round2',(w/'velout.mod').read_text(),(w/'output.sta').read_text(),(w/'output.cnv').read_text(),len(selected),True);record['runs'].append(r2)
            output=parse_events(w2/'output.cnv',selected.event_index.tolist());output.to_csv(D/('velest_'+region+'_calibration.csv'),index=False)
            model_table(w2/'velout.mod').to_csv(D/('velest_'+region+'_model.csv'),index=False)
            alternatives.append((float(np.mean(output.rms_s**2)),region,w2))
        score,region,w=min(alternatives,key=lambda r:r[0]);record.update(chosen_region=region,calibration_rms_s=float(np.sqrt(score)))
        shutil.copy2(w/'velout.mod',D/'independent_velest_model.mod');shutil.copy2(w/'output.sta',D/'independent_station_corrections.sta')
        fitted=model_table(D/'independent_velest_model.mod');fitted.to_csv(D/'independent_velest_model.csv',index=False)
        left=pd.read_csv(D/'velest_caldera_model.csv');right=pd.read_csv(D/'velest_central_model.csv')
        record['model_checks']=dict(positive_velocities=True,Vp_greater_than_Vs=True,ordered_interfaces=True,
            minimum_VpVs=float(fitted.VpVs.min()),maximum_VpVs=float(fitted.VpVs.max()),
            between_starting_models_rms_Vp_km_s=float(np.sqrt(np.mean((left.Vp_km_s-right.Vp_km_s)**2))),
            between_starting_models_rms_Vs_km_s=float(np.sqrt(np.mean((left.Vs_km_s-right.Vs_km_s)**2))),
            independent_accuracy_validated=False)
        previous=D/'velest_single_precision_failed_attempt.json'
        if previous.exists():
            old=json.loads(previous.read_text())['single_precision_models']
            comparisons={}
            for name,new in [('caldera',left),('central',right)]:
                prior=pd.read_csv(io.StringIO(old[f'velest_{name}_model.csv']))
                assert np.array_equal(prior.layer_top_km,new.layer_top_km)
                comparisons[name]={phase:float(np.max(np.abs(new[phase]-prior[phase]))) for phase in ['Vp_km_s','Vs_km_s']}
            record['precision_check']=dict(compilation_real_bits=64,maximum_calibration_velocity_changes_km_s=comparisons,
                note='Same inputs, equations and damping; table differences include upstream 0.01 km/s output rounding. This checks arithmetic sensitivity, not scientific accuracy.')
        # Run the documented first three whole-catalog fixed-model passes.
        text=cnv(events,picks,assign,aliases)
        for n in range(1,4):
            w,r=execute('whole_catalog_'+str(n),(D/'independent_velest_model.mod').read_text(),(D/'independent_station_corrections.sta').read_text(),text,len(events),True,True);record['runs'].append(r);text=(w/'output.cnv').read_text()
        output=parse_events(w/'output.cnv',events.event_index.tolist());output.to_csv(D/'velest_locations_before_rejection.csv',index=False)
        ids=events.event_index.tolist();record['residual_rejection']=[]
        for n,threshold in [(4,.4),(5,.3)]:
            text,ids,audit=reject_residuals(w,ids,threshold);record['residual_rejection'].append(audit)
            if not ids:raise ValueError('No event retains enough picks after residual rejection')
            w,r=execute('whole_catalog_'+str(n),(D/'independent_velest_model.mod').read_text(),(D/'independent_station_corrections.sta').read_text(),text,len(ids),True,True);record['runs'].append(r)
        output=parse_events(w/'output.cnv',ids)
        blocks=re.split(r'\n\s*\n',(w/'output.cnv').read_text().strip())
        output['num_picks']=[sum(len(line.rstrip())//12 for line in block.splitlines()[1:]) for block in blocks]
        output['quality_pass']=(output.num_picks>=6)&(output.rms_s<=.25)&(output.azimuthal_gap_deg<=300)
        output.to_csv(D/'velest_locations.csv',index=False)
        output[output.quality_pass].to_csv(D/'velest_filtered.csv',index=False)
        shutil.copy2(w/'output.cnv',D/'velest_final.cnv')
        record.update(completed=True,events_located=len(output),quality_passing=int(output.quality_pass.sum()),remaining='TomoDD and regional SVD not run. Calibration is a limited pilot without the full period or manual review; not an exact reproduction.',status='partial')
    except Exception as e:record.update(error=repr(e),status='failed pilot; outputs must not be treated as calibrated results')
    (D/'velest_summary.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':main()
