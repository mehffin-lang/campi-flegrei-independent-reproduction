"""Observed-data VELEST continuation with an explicitly alternative 1-D model.

No Battaglia/Tan grid or author event solution is read. High-quality selection
is not specified numerically in Tan: our causality, >6-pick and gap<180 screen
is an assumption. Its events remain unreviewed. Outputs are exploratory, even
when they pass Tan's subsequent numerical catalog filters.
"""
from pathlib import Path
import hashlib, json, re, subprocess, shutil, os, time
import numpy as np
import pandas as pd
from obspy import UTCDateTime
from pyproj import Geod
import run_velest as v

ROOT=v.ROOT
D=ROOT/'data/continuation'
OUT=ROOT/'data/calibration_followup'
WORK=ROOT/'tmp/calibration_followup/velest'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def normalize_model(text):
    source=iter(text.splitlines()); next(source)
    lines=['Independent alternative-profile VELEST fit; not Battaglia/Tan model']
    for phase in ['P','S']:
        n=int(next(source)); lines.append(str(n))
        for _ in range(n):
            speed,z,damp=map(float,next(source).split()[:3])
            lines.append(f'{speed:5.2f}     {z:7.2f}  {damp:7.3f}')
    return '\n'.join(lines)+'\n'


def normalize_stations(text):
    # Generic VELEST writes alternating P/S model indices but ignores this
    # field on input (INPUTPARAM forces mode=1). Make the actual choice explicit.
    lines=text.splitlines(); result=[lines[0].rstrip()]
    for line in lines[1:]:
        if line[:4].strip(): result.append(line[:28]+'1'+line[29:46])
    return '\n'.join(result)+'\n\n'


def run(name,model,stations,cnv,ids,bits=64,corrections=False,fixed=False,iterations=7):
    work=WORK/name; work.mkdir(parents=True,exist_ok=True)
    # A failed rerun cannot inherit old successes.
    for f in work.iterdir():
        if f.is_file():f.unlink()
    for f,text in [('input.mod',model),('input.sta',stations),('input.cnv',cnv),
                   ('velest.cmn',v.controls(len(ids),corrections,fixed,iterations))]:
        (work/f).write_text(text)
    binary_hash=sha(ROOT/f'build/velest{bits}')
    started=time.monotonic();timeout=int(os.environ.get('CF_VELEST_TIMEOUT','300'))
    r=subprocess.run([str(ROOT/f'build/velest{bits}')],cwd=work,capture_output=True,text=True,timeout=timeout)
    (work/'console.log').write_text(r.stdout+r.stderr)
    if r.returncode or not (work/'output.cnv').exists():
        raise RuntimeError(f'{name}: VELEST failed; inspect {work.relative_to(ROOT)}/console.log')
    located=v.parse_events(work/'output.cnv',ids)
    raw=(work/'velout.mod').read_text();(work/'velout.raw.mod').write_text(raw)
    (work/'velout.mod').write_text(normalize_model(raw))
    fitted=v.model_table(work/'velout.mod')
    residual=np.loadtxt(work/'residuals.txt',ndmin=2)[:,1]
    assert np.isfinite(residual).all() and np.isfinite(located[['latitude','longitude','depth_km','rms_s']]).all().all()
    counts=[sum(len(line.rstrip())//12 for line in b.splitlines()[1:]) for b in re.split(r'\n\s*\n',(work/'output.cnv').read_text().strip())]
    assert sum(counts)==len(residual)
    located['num_picks']=counts
    located.to_csv(OUT/f'{name}_locations.csv',index=False)
    fitted.to_csv(OUT/f'{name}_model.csv',index=False)
    record=dict(name=name,bits=bits,events=len(ids),picks=len(residual),returncode=r.returncode,
                residual_rms_s=float(np.sqrt(np.mean(residual**2))),
                event_rms_s=float(np.sqrt(np.mean(located.rms_s**2))),
                depth_min_km=float(located.depth_km.min()),depth_max_km=float(located.depth_km.max()),
                workdir=str(work.relative_to(ROOT)),wall_seconds=time.monotonic()-started,timeout_seconds=timeout,binary_sha256=binary_hash)
    if fixed:
        assert np.array_equal(v.model_table(work/'input.mod').to_numpy(),fitted.to_numpy()), 'Fixed model changed'
        before=normalize_stations(stations);after=normalize_stations((work/'output.sta').read_text())
        assert before==after, 'Fixed station corrections changed'
    print(json.dumps(record),flush=True)
    return work,located,record


def compare(a,b):
    assert a.event_index.tolist()==b.event_index.tolist()
    _,_,dist=Geod(ellps='WGS84').inv(a.longitude.to_numpy(),a.latitude.to_numpy(),b.longitude.to_numpy(),b.latitude.to_numpy())
    return dict(max_horizontal_m=float(np.max(dist)),max_depth_km=float(abs(a.depth_km-b.depth_km).max()),
                max_origin_s=max(abs(UTCDateTime(x)-UTCDateTime(y)) for x,y in zip(a.time,b.time)),
                max_rms_s=float(abs(a.rms_s-b.rms_s).max()))


def main():
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
    inputs=['initial_events.csv','picks.csv','associations.csv','association_quality.csv','location_quality.csv','stations.csv','alternative_starting_profile.csv']
    record=dict(status='running',accepted_exact_reproduction=False,accepted_scientific_calibration=False,
                inputs={str((D/f).relative_to(ROOT)):sha(D/f) for f in inputs},runs=[],
                selection='Necessary causality, >6 picks, initial azimuthal gap <180; unreviewed. Not a numerically specified Tan selection.',
                model='Tramelli et al. 2021 Table 1, first layer extended to -0.5 km; alternative, not Battaglia regional means',
                assumptions='7 iterations per pass; existing damping; equal CNV pick classes; S weight 0.5; zero initial station delays; best-observed station P delay fixed; other S/P corrections float in calibration round 2.')
    (OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    events=pd.read_csv(D/'initial_events.csv'); picks=pd.read_csv(D/'picks.csv'); assign=pd.read_csv(D/'associations.csv')
    quality=pd.read_csv(D/'association_quality.csv'); geometry=pd.read_csv(D/'location_quality.csv')
    events=events[events.event_index.isin(quality.loc[quality.passes_causality,'event_index'])].sort_values('time')
    assign=assign[assign.event_index.isin(events.event_index)]
    selected=events[events.event_index.isin(geometry.loc[geometry.calibration_eligible,'event_index'])]
    selected.to_csv(OUT/'calibration_selection.csv',index=False)
    selected.groupby(selected.time.str[:4]).size().rename('events').to_csv(OUT/'calibration_year_counts.csv')
    stations=pd.read_csv(D/'stations.csv');used=set(picks.iloc[assign.pick_index.to_numpy(int)].trace_id)
    stations=stations[stations.id.isin(used)].sort_values('id')
    ep=picks.iloc[assign.loc[assign.event_index.isin(selected.event_index),'pick_index'].to_numpy(int)]
    reference=ep[ep.phase=='P'].groupby('trace_id').size().idxmax()
    aliases={s:f'S{i:03d}' for i,s in enumerate(stations.id)}
    order=[s for s in stations.id if s!=reference]+[reference];icc={s:i+1 for i,s in enumerate(order)}
    sta=['(a4,f7.4,a1,1x,f8.4,a1,1x,i4,1x,i1,1x,i3,1x,f5.2,2x,f5.2)']
    for r in stations.to_dict('records'):
        sta.append(f'{aliases[r["id"]]:4s}{r["latitude"]:7.4f}N {r["longitude"]:8.4f}E {round(-r["z(km)"]*1000):4d} 1 {icc[r["id"]]:3d} {0.:5.2f}  {0.:5.2f}')
    sta='\n'.join(sta)+'\n\n'
    stations.assign(alias=stations.id.map(aliases),icc=stations.id.map(icc)).to_csv(OUT/'station_aliases.csv',index=False)
    profile=pd.read_csv(D/'alternative_starting_profile.csv');profile.loc[0,'depth_top_km_bsl']=-.5
    lines=['Tramelli 2021 alternative; top extended -0.5 km']
    for field in ['vp_km_s','vs_km_s']:
        lines.append(str(len(profile)));lines.extend(f'{r[field]:5.2f}     {r["depth_top_km_bsl"]:7.2f}  {1.:7.3f}' for r in profile.to_dict('records'))
    model='\n'.join(lines)+'\n'
    record.update(calibration_events=len(selected),whole_catalog_input_events=len(events),reference_station=reference)
    try:
        fits={}
        for bits in [32,64]:
            w,loc,r=run(f'calibration_{bits}_round1',model,sta,v.cnv(selected,picks,assign,aliases),selected.event_index.tolist(),bits=bits);record['runs'].append(r)
            w,loc,r=run(f'calibration_{bits}_round2',(w/'velout.mod').read_text(),normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),selected.event_index.tolist(),bits=bits,corrections=True);record['runs'].append(r);fits[bits]=(w,loc)
        a,b=fits[32],fits[64];record['precision_locations']=compare(a[1],b[1])
        record['precision_max_velocity_km_s']=float(np.max(abs(v.model_table(a[0]/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(b[0]/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy())))
        w=b[0];fixed_model=(w/'velout.mod').read_text();fixed_sta=normalize_stations((w/'output.sta').read_text())
        (OUT/'alternative_fitted_model.mod').write_text(fixed_model);(OUT/'alternative_station_corrections.sta').write_text(fixed_sta)
        # Another pass checks whether the nominal two-pass fit was converged;
        # it does not silently replace that fit or select a best-looking result.
        wcheck,check,r=run('calibration_convergence',fixed_model,fixed_sta,(w/'output.cnv').read_text(),selected.event_index.tolist(),corrections=True);record['runs'].append(r)
        record['extra_pass_location_change']=compare(b[1],check)
        record['extra_pass_max_velocity_change_km_s']=float(np.max(abs(v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy()-v.model_table(wcheck/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy())))
        # Held-out events are every fifth event in chronological order; no
        # reference catalog is used to select or score this internal test.
        hold=selected.iloc[::5];train=selected[~selected.event_index.isin(hold.event_index)]
        cw,_,r=run('validation_training_round1',model,sta,v.cnv(train,picks,assign,aliases),train.event_index.tolist());record['runs'].append(r)
        cw,_,r=run('validation_training_round2',(cw/'velout.mod').read_text(),normalize_stations((cw/'output.sta').read_text()),(cw/'output.cnv').read_text(),train.event_index.tolist(),corrections=True);record['runs'].append(r)
        record['heldout']={}
        for label,mod,st in [('starting',model,sta),('fitted',(cw/'velout.mod').read_text(),normalize_stations((cw/'output.sta').read_text()))]:
            _,_,r=run('heldout_'+label,mod,st,v.cnv(hold,picks,assign,aliases),hold.event_index.tolist(),corrections=True,fixed=True,iterations=21);record['runs'].append(r);record['heldout'][label]=r
        cnv=v.cnv(events,picks,assign,aliases);ids=events.event_index.tolist()
        for n in range(1,6):
            if n in [4,5]:
                cnv,ids,rejection=v.reject_residuals(w,ids,.4 if n==4 else .3)
                record.setdefault('rejection',[]).append(rejection)
            w,located,r=run(f'whole_catalog_pass{n}',fixed_model,fixed_sta,cnv,ids,corrections=True,fixed=True);record['runs'].append(r);cnv=(w/'output.cnv').read_text()
        located['paper_filter_pass']=(located.num_picks>=6)&(located.rms_s<=.25)&(located.azimuthal_gap_deg<=300)
        located.to_csv(OUT/'located_events.csv',index=False)
        located[located.paper_filter_pass].to_csv(OUT/'filtered_events.csv',index=False)
        (OUT/'located_events.cnv').write_text(cnv)
        record.update(status='executed exploratory chain',paper_filter_passing=int(located.paper_filter_pass.sum()),
                      limitations='Alternative profile, unreviewed calibration phases, incomplete observations and static station coordinates. Numerical filter passage is not validation of event identity or accurate depth. No accepted Battaglia calibration or TomoDD catalog.')
    except Exception as exc:
        record.update(status='failed exploratory chain',error=repr(exc))
    record['code_sha256']=sha(__file__)
    (OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='runs'},indent=2))

if __name__=='__main__':main()
