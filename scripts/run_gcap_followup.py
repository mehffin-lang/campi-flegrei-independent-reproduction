"""Exploratory FK/gCAP runs from own observations, own model and own locations.

No example data or author solution is read. Missing event-specific settings are
explicit assumptions; these fits do not establish publication-quality mechanisms.
FK theoretical Green functions are model predictions, not synthetic observations.
"""
from pathlib import Path
import os,json,subprocess,re,hashlib,sys
import numpy as np,pandas as pd
from obspy import read,read_inventory,UTCDateTime,Trace
import run_velest as v
ROOT=Path(__file__).resolve().parents[1];D=ROOT/os.environ.get('CF_MECH_OUT','data/mechanism_followup');WROOT=ROOT/os.environ.get('CF_MECH_WORK','tmp/mechanism_followup');W=WROOT/'gcap';FK=ROOT/'build/method_followup/fk';CAP=ROOT/'build/method_followup/gcap/cap_followup'

def main():
    global W
    high='--high-band' in sys.argv;band=(1.,5.) if high else (.2,2.)
    G=D/('gcap_1_5' if high else 'gcap')
    W=WROOT/G.name
    W.mkdir(parents=True,exist_ok=True);G.mkdir(exist_ok=True)
    location_file=ROOT/os.environ.get('CF_MECH_LOCATIONS','data/coverage_extension/calibration/merged4/uncertainty/relocated_events.csv')
    model_file=ROOT/os.environ.get('CF_MECH_MODEL','data/coverage_extension/calibration/merged4/independent_calibrated.mod')
    f=pd.read_csv(D/'review_decisions.csv');events=pd.read_csv(location_file).set_index('event_index')
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'))+read_inventory(str(ROOT/'inputs/continuation/2I_responses.xml'))
    model=v.model_table(model_file)
    thick=np.r_[np.diff(model.layer_top_km),0.]
    # FK's vacuum free surface is at the own model's -0.5-km top. Source
    # depths move by +0.5 km; all receivers use this flat surface approximation.
    lines=[f'{h:.5f} {r.Vs_km_s:.5f} {r.Vp_km_s:.5f} {(.77+.32*r.Vp_km_s):.5f} 500 1000' for h,r in zip(thick,model.itertuples())]
    records=[];solutions=[];fits=[];saved={};env=dict(os.environ,PATH=str(FK)+':'+os.environ['PATH'])
    for eid,g in f.groupby('event_id'):
        selected=g[g.sp_accepted].copy();run=dict(event_id=int(eid),stations_requested=len(selected),accepted=False,runs=[],errors=[])
        if len(selected)<4:
            run['blocker']='Fewer than four reviewed three-component P/S packets; no waveform inversion attempted';records.append(run);continue
        e=events.loc[eid];t=UTCDateTime(e.time);depth=float(e.depth_km)+.5;name=f'e{eid}';work=W/name;work.mkdir(exist_ok=True);(work/'model').write_text('\n'.join(lines)+'\n');obs=work/'obs';obs.mkdir(exist_ok=True);green=work/'green';green.mkdir(exist_ok=True)
        distances=[f'{x:.3f}' for x in selected.distance_km];control=[];used=[]
        try:
            cmd=['perl',str(FK/'fk.pl'),f'-Mmodel/{depth:.3f}','-N1024/0.05','-H0.02/0.04',*distances]
            r=subprocess.run(cmd,cwd=work,env=env,capture_output=True,text=True,timeout=180);(G/f'{name}_fk.log').write_text(r.stdout+r.stderr);run['runs'].append(dict(command=cmd,cwd=str(work.relative_to(ROOT)),returncode=r.returncode))
            if r.returncode:raise RuntimeError('FK wrapper returned nonzero')
            source=work/f'model_{depth:.3f}';target=green/f'model_{depth:.3f}';target.mkdir(exist_ok=True)
            for path in sorted(source.glob('*.grn.*')):
                tr=read(str(path))[0]
                if not np.isfinite(tr.data).all():raise ValueError('Nonfinite Green function '+path.name)
                tr.filter('bandpass',freqmin=band[0],freqmax=band[1],corners=4,zerophase=True);tr.write(str(target/path.name),format='SAC')
            if len(list(target.glob('*.grn.*')))!=9*len(set(distances)):raise ValueError('Missing FK Green functions')
            run['green_functions']=len(list(target.glob('*.grn.*')))
            for row in selected.itertuples():
                try:
                    st=read(str(ROOT/row.source),starttime=t-40,endtime=t+50).merge(method=0).split().select(network=row.network,station=row.station,location='' if row.location=='--' else row.location)
                    assert all(len(st.select(component=c))==1 for c in 'ZNE')
                    st.detrend('demean').taper(.03)
                    for tr in st:tr.remove_response(inventory=inv,output='VEL',pre_filt=[.05,.1,8,9],water_level=60)
                    st.filter('bandpass',freqmin=band[0],freqmax=band[1],corners=4,zerophase=True)
                    for tr in st:tr.interpolate(20,starttime=t-15,npts=901,method='lanczos',a=10)
                    z,n,ee=[st.select(component=c)[0].data for c in 'ZNE'];az=np.deg2rad(row.azimuth)
                    # FK README defines upward Z, outward R, counterclockwise T.
                    radial=n*np.cos(az)+ee*np.sin(az);trans=n*np.sin(az)-ee*np.cos(az)
                    assert np.allclose(n*n+ee*ee,radial*radial+trans*trans,rtol=1e-10,atol=1e-24)
                    p=float(UTCDateTime(row.p_time)-t);s=float(UTCDateTime(row.s_time)-t)
                    for comp,y in [('z',z),('r',radial),('t',trans)]:
                        tr=Trace((100*y).astype(np.float32),header=dict(sampling_rate=20,starttime=t-15))
                        tr.stats.sac=dict(b=-15.,o=0.,dist=row.distance_km,az=row.azimuth,evdp=e.depth_km,t1=p-.3,t2=p+1.2,t3=s-.3,t4=s+4.7)
                        tr.write(str(obs/f'{row.station}.{comp}'),format='SAC')
                    control.append(f'{row.station} {row.distance_km:.3f} 1 1 1 1 1 {p:.5f} 0')
                    used.append(dict(event_id=int(eid),station=row.station,source=row.source,p_time=row.p_time,s_time=row.s_time,azimuth_deg=row.azimuth,distance_km=row.distance_km,origin_time=e.time,depth_km_bsl=e.depth_km))
                except Exception as exc:run['errors'].append(dict(station=row.station,error=repr(exc)))
            if len(control)<4:raise ValueError('Fewer than four valid rotated records')
            (G/f'{name}_stations.csv').write_text(pd.DataFrame(used).to_csv(index=False))
            # Same band for both windows is externally applied to whole traces.
            # No SAC proprietary filter is called. Fixed source, DC only, 10-deg
            # orientation grid, Mw step .1, source duration .2 s are assumptions.
            text='3 6 0.5 1 0 0 2 0.5\n0 0\n-1 -1 -1\n1 0.5 2 0.01\n1\n0 0\ngreen/\n0.05 0.2 0.1\n0 0 0 0\n2.0 0.1\n0 0\n0 0\n0 360 10\n0 90 10\n-180 180 10\n'+str(len(control))+'\n'+'\n'.join(control)+'\n'
            (G/f'{name}_control.txt').write_text(text)
            cmd=[str(CAP),'obs',f'model_{depth:.3f}'];r=subprocess.run(cmd,input=text,cwd=work,capture_output=True,text=True,timeout=180);(G/f'{name}_cap.log').write_text(r.stdout+r.stderr);run['runs'].append(dict(command=cmd,cwd=str(work.relative_to(ROOT)),returncode=r.returncode))
            if r.returncode:raise RuntimeError('gCAP returned nonzero')
            result=obs/f'model_{depth:.3f}.out'
            if not result.exists():raise ValueError('No gCAP solution file')
            output=result.read_text();(G/f'{name}.out').write_text(output)
            first=output.splitlines()[0].split();idx=first.index('FM');mi=first.index('Mw');vr=float(re.search(r'Variance reduction\s+([-+.\deE]+)',output)[1])
            solutions.append(dict(event_id=int(eid),strike=float(first[idx+1]),dip=float(first[idx+2]),rake=float(first[idx+3]),Mw_exploratory=float(first[mi+1]),variance_reduction_percent=vr,stations=len(control),latitude=e.latitude,longitude=e.longitude,depth_km=e.depth_km,accepted=False,status='Provisional fixed-source DC waveform fit; unvalidated model, windows, density and Q; no publication-quality selection'))
            for file in sorted(obs.glob('model_*.*')):
                if file.suffix=='.out':continue
                try:
                    tr=read(str(file))[0]
                    if not np.isfinite(tr.data).all():raise ValueError('Nonfinite fit output')
                    key=name+'_'+file.name.replace('.','_');saved[key]=np.vstack([tr.times()+tr.stats.sac.a,tr.data]);fits.append(dict(event_id=int(eid),file=file.name,key=key,time_origin='SAC a = fitted window start; includes optimized lag for theoretical trace',role='Observed waveform divided by fitted moment scale' if int(file.suffix[1:])%2==0 else 'Theoretical best-fit waveform; not an observation'))
                except Exception as exc:run['errors'].append(dict(file=file.name,error=repr(exc)))
            run.update(stations_used=len(control),variance_reduction_percent=vr,computed=True)
        except Exception as exc:run['blocker']=repr(exc)
        records.append(run);(G/'execution.json').write_text(json.dumps(records,indent=2)+'\n');print(run,flush=True)
    pd.DataFrame(solutions).to_csv(G/'solutions.csv',index=False);pd.DataFrame(fits).to_csv(G/'fit_index.csv',index=False);np.savez_compressed(G/'fit_waveforms.npz',**saved)
    (G/'execution.json').write_text(json.dumps(records,indent=2)+'\n')
    (G/'method.json').write_text(json.dumps(dict(classification='Independent exploratory waveform inversion using generic gCAP/FK; no synthetic observations',source_model='data/coverage_extension/calibration/merged4/independent_calibrated.mod',model=lines,source_depth='Own bsl depth +0.5 km; reference free surface at -0.5 km bsl',receiver_depth='Flat model surface; topographic receiver correction not implemented',rho='FK documented fallback rho=0.77+0.32 Vp in g/cm3',Q='FK defaults Qs=500 Qp=1000; not measured here',filter=f'Both data and Green functions prefiltered {band[0]}–{band[1]} Hz, 4-pole zero-phase, then 20 Hz. Different ordering from stock gCAP segment filtering; exploratory assumption.',windows='Own P-.3 to P+1.2; own S-.3 to S+4.7 s; maximum shifts .5 and 1 s; Pnl weight 2 and distance powers 1/.5; no automatic trace rejection',source='Fixed own provisional location/depth, DC only, 10-degree strike/dip/rake grid, Mw step .1, 0.2-s trapezoidal duration. Settings are generic/disclosed, not recovered Tan event controls.',rotation='Metadata-verified ZNE -> upward Z, outward radial R, counterclockwise T; cm/s; horizontal energy check passed for saved records',validation='Finite Green functions and fit arrays; counts; rotation energy; eigensolver consistency. No model/path or source-depth sensitivity acceptance. Raw variance reduction is not a validation of source mechanism.',software='Official FK 3.3 and generic Zhu gCAP, with disclosed cap_followup eigensolver/external-filter port; archive/extraction manifests in inputs/method_followup/'),indent=2)+'\n')
    method=json.loads((G/'method.json').read_text());method.update(source_model=str(model_file.relative_to(ROOT)),source_locations=str(location_file.relative_to(ROOT)),source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [model_file,location_file,D/'review_decisions.csv']});(G/'method.json').write_text(json.dumps(method,indent=2)+'\n')
if __name__=='__main__':main()
