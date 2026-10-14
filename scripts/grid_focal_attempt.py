"""Observed first-motion screening and an explicitly unreviewed SKHASH attempt.

This is a provisional alternative to Tan's manual polarity review. No supplied
mechanism, polarity or S/P ratio is read. Default geometric gates are retained.
"""
from pathlib import Path
import json,hashlib,subprocess,os
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
import run_velest as v
ROOT=Path(__file__).resolve().parents[1];B=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration')/'merged4';OUT=B/'focal'

def main():
    OUT.mkdir(exist_ok=True)
    events=pd.read_csv(B/'uncertainty/relocated_events.csv').set_index('event_index');picks=pd.read_csv(B/'tomodd/retained_picks.csv');p=picks[(picks.phase=='P')&picks.event_index.isin(events.index)]
    counts=p.groupby('event_index').size();ids=counts[counts>=8].index;p=p[p.event_index.isin(ids)]
    identity_files=[B/'tomodd/retained_picks.csv',B/'uncertainty/relocated_events.csv',B/'independent_calibrated.mod',B/'summary.json',B/'validation.json',Path(__file__),ROOT/'scripts/run_velest.py']
    identity_files += [ROOT/f for f in sorted(set(p.source))]+[ROOT/f'inputs/continuation/{n}_responses.xml' for n in ['IV','2I']]
    identity_files += list((ROOT/'.venv-skhash/lib/python3.11/site-packages/SKHASH').rglob('*.py'))
    identity={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in identity_files};manifest=OUT/'execution_manifest.json'
    if manifest.exists():
        cached=json.loads(manifest.read_text())
        if cached['inputs']==identity and all((ROOT/n).exists() and hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in cached['outputs'].items()):
            print('Reused automatic polarity screen after exact input/software/output hash checks.');return
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'))+read_inventory(str(ROOT/'inputs/continuation/2I_responses.xml'))
    rows=[];stations=[];waves={};failures=[]
    regional=json.loads((B/'summary.json').read_text())['starting_model_dependence']
    precision=json.loads((B/'validation.json').read_text())['precision_difference']
    horizontal=max(regional['max_horizontal_m'],precision['max_horizontal_m'])/1000
    vertical=max(regional['max_depth_km'],precision['max_depth_km'])
    for source,group in p.groupby('source'):
        st=read(str(ROOT/source)).merge(method=0).split()
        for r in group.itertuples():
            try:
                net,sta,loc=r.trace_id.split('.');t=UTCDateTime(r.time)
                traces=st.select(network=net,station=sta,location=loc,component='Z').slice(t-10,t+5).copy()
                if len(traces)!=1:raise ValueError('Missing single continuous vertical trace')
                tr=traces[0];meta=inv.select(network=net,station=sta,location=loc,channel=tr.stats.channel,time=t)[0][0][0]
                if not abs(float(meta.dip)+90)<1:raise ValueError('Vertical orientation not verified upward')
                tr.detrend('demean');tr.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                # No acausal filter: retain onset sign, with disclosed response
                # deconvolution uncertainty. Adjacent peak windows must agree.
                noise=tr.copy().trim(t-.5,t-.05).data;noise_rms=np.sqrt(np.mean(noise**2));signs=[];ratios=[]
                for dt in [.06,.10,.15]:
                    y=tr.copy().trim(t+.01,t+dt).data
                    peak=y[np.argmax(abs(y))];signs.append(int(np.sign(peak)));ratios.append(float(abs(peak)/max(noise_rms,np.finfo(float).tiny)))
                stable=len(set(signs))==1 and min(ratios)>=3
                a=tr.copy().trim(t-.5,t+.6);key=f'e{r.event_index}_{sta}';waves[key]=np.vstack([a.times()+float(a.stats.starttime-t),a.data])
                e=events.loc[r.event_index]
                rows.append(dict(event_id=str(r.event_index),network=net,station=sta,location=loc or '--',channel=tr.stats.channel,p_polarity=.5*signs[0] if stable else 0.,origin_latitude=e.latitude,origin_longitude=e.longitude,origin_depth_km=e.depth_km,
                    horz_uncert_km=horizontal,vert_uncert_km=vertical,source=source,p_time=r.time,array_key=key,sign_60ms=signs[0],sign_100ms=signs[1],sign_150ms=signs[2],minimum_peak_noise_ratio=min(ratios),stable=stable,reviewed=False))
                stations.append(dict(network=net,station=sta,location=loc or '--',channel=tr.stats.channel,latitude=meta.latitude,longitude=meta.longitude,elevation=meta.elevation))
            except Exception as exc:failures.append(dict(event_index=r.event_index,station=r.trace_id,error=repr(exc)))
    frame=pd.DataFrame(rows);frame.to_csv(OUT/'polarity_screen.csv',index=False);frame[frame.stable].to_csv(OUT/'polarities.csv',index=False);pd.DataFrame(stations).drop_duplicates().to_csv(OUT/'stations.csv',index=False);np.savez_compressed(OUT/'review_windows.npz',**waves)
    model=v.model_table(B/'independent_calibrated.mod');z=[];vp=[]
    # SKHASH accepts a piecewise linear velocity profile. Near-duplicate knots
    # encode our independently fitted piecewise constant layers, without fitting.
    for i,r in model.iterrows():
        z.append(max(0.,r.layer_top_km));vp.append(r.Vp_km_s)
        if i+1<len(model):z.append(model.layer_top_km.iloc[i+1]-.0001);vp.append(r.Vp_km_s)
    z.append(20.);vp.append(vp[-1]);np.savetxt(OUT/'velocity.csv',np.c_[z,vp],delimiter=',',header='depth_km,velocity_km_s')
    control={'input_format':'skhash','fpfile':str(OUT/'polarities.csv'),'stfile':str(OUT/'stations.csv'),'outfile1':str(OUT/'solutions.csv'),'outfile2':str(OUT/'acceptable_planes.csv'),'outfile_pol_info':str(OUT/'used_polarities.csv'),'vmodel_paths':str(OUT/'velocity.csv'),'npolmin':8,'max_agap':90,'max_pgap':60,'nmc':30,'look_dep':'0 10 1','look_del':'0 120 1','nd0':11,'nx0':121,'num_cpus':1,'overwrite_output_file':'True'}
    # Names must be verified against this pinned method release.
    source=ROOT/'.venv-skhash/lib/python3.11/site-packages/SKHASH/SKHASH.py'
    for k in list(control):
        if f"'{k}'" not in source.read_text():raise ValueError('Unknown control '+k)
    (OUT/'control.txt').write_text('\n'.join('$'+k+'\n'+str(val) for k,val in control.items())+'\n')
    if (OUT/'run.log').exists():
        n=len(list(OUT.glob('previous_run*.log')))+1;(OUT/f'previous_run{n}.log').write_bytes((OUT/'run.log').read_bytes())
    (OUT/'solutions.csv').unlink(missing_ok=True)
    result=subprocess.run([str(ROOT/'.venv-skhash/bin/SKHASH'),str(OUT/'control.txt')],cwd=ROOT,capture_output=True,text=True,timeout=300);(OUT/'run.log').write_text(result.stdout+result.stderr)
    solutions=pd.read_csv(OUT/'solutions.csv') if (OUT/'solutions.csv').exists() and (OUT/'solutions.csv').stat().st_size else pd.DataFrame()
    summary=dict(candidate_events=len(ids),measured_polarities=len(frame),stable_screen_polarities=int(frame.stable.sum()),events_with_eight_stable=int((frame[frame.stable].groupby('event_id').size()>=8).sum()),returncode=result.returncode,solutions=len(solutions),scientifically_accepted=0,reviewed_polarities=0,failures=failures,
        method='SKHASH 1.1.5 generic USGS software; https://code.usgs.gov/esc/SKHASH ; Skoumal et al. 2024 doi:10.1785/0220230329. Isolated .venv-skhash; no example/author event data used.',
        assumptions='Peak signs agree in 0.01–0.06/0.10/0.15 s after own P and exceed 3x preceding 0.45-s RMS. Upward Z metadata verified. Weight 0.5. This screen is not manual polarity review; S/P ratios not supplied. Perturbation scales use maxima of the current own regional-start and precision shifts; these are sensitivity-based assumptions, not measured Gaussian uncertainties. Default eight-polarity, 90-degree azimuth and 60-degree plunge-gap gates are not relaxed.',
        gcap='This automatic screening stage does not run gCAP. Separate waveform review and FK/gCAP execution records determine its status.',
        perturbation_scales_km=dict(horizontal=horizontal,vertical=vertical),
        sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B/'tomodd/retained_picks.csv',B/'uncertainty/relocated_events.csv',B/'independent_calibrated.mod',source]})
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
    manifest.write_text(json.dumps(dict(inputs=identity,outputs={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.is_file() and f!=manifest}),indent=2)+'\n')

if __name__=='__main__':main()
