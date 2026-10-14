"""Two fixed-3D TomoDD rounds from own arrivals and grid-calibrated trial locations."""
from pathlib import Path
import json,shutil,subprocess,os,argparse,tarfile,io
import numpy as np
import pandas as pd
from obspy import UTCDateTime
from pyproj import Geod
import relocation_followup as rf
ROOT=rf.ROOT;OUT=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration')/'merged4';DEST=OUT/'tomodd';D=ROOT/os.environ.get('CF_OBSERVATIONS','data/calibration_followup/expanded');WORK=ROOT/os.environ.get('CF_GRID_WORK','tmp/grid_calibration')/'tomodd'

def write_inputs(work,events,stations,picks,ct,cc):
    work.mkdir(parents=True,exist_ok=True);ids=set(events.index);initial=pd.read_csv(OUT/'filtered_events.csv').set_index('event_index')
    shifts={i:float(UTCDateTime(events.loc[i,'time'])-UTCDateTime(initial.loc[i,'time'])) for i in ids}
    for name,table in [('dt.ct',ct),('dt.cc',cc)]:
        rows=[];table=table[table.event_a.isin(ids)&table.event_b.isin(ids)]
        for (a,b),g in table.groupby(['event_a','event_b']):
            rows.append(f'# {a+1} {b+1}'+(' 0.0' if name=='dt.cc' else ''))
            for r in g.itertuples():
                rows.append(f'{r.alias} {r.dt_s-shifts[a]+shifts[b]:.6f} {r.weight:.6f} {r.phase}' if name=='dt.cc' else f'{r.alias} {r.tt_a-shifts[a]:.6f} {r.tt_b-shifts[b]:.6f} 1.0 {r.phase}')
        (work/name).write_text('\n'.join(rows)+'\n')
    rows=[]
    for eid,e in events.iterrows():
        t=UTCDateTime(e.time);clock=t.hour*1000000+t.minute*10000+round((t.second+t.microsecond/1e6)*100)
        rows.append(f'{t.strftime("%Y%m%d")} {clock:08d} {e.latitude:.6f} {e.longitude:.6f} {e.depth_km:.4f} 0 0 0 {e.rms_s:.4f} {eid+1} 0')
    (work/'event.dat').write_text('\n'.join(rows)+'\n')
    (work/'station.dat').write_text('\n'.join(f'{a} {r.latitude:.6f} {r.longitude:.6f} {-r["z(km)"]*1000:.1f}' for a,r in stations.iterrows())+'\n')
    rows=[]
    for eid,g in picks[picks.event_index.isin(ids)].groupby('event_index'):
        rows.append(f'# {eid+1}');rows.extend(f'{r.alias} {float(UTCDateTime(r.time)-UTCDateTime(events.loc[eid,"time"])):.6f} 1.0 {r.phase}' for r in g.itertuples())
    (work/'absolute.dat').write_text('\n'.join(rows)+'\n')
    shutil.copyfile(ROOT/'data/grid_calibration/reference_grid.original',work/'MOD')
    # Generic solver's mandatory global reference/layer tables, not Tan results.
    with tarfile.open(ROOT/'inputs/continuation/tomodd_training.tar') as tar:
        for filename in ['ak135.15.SKS','layer-16.dat']:
            member=tar.getmember('USTC-tomoDD-SE-training2020/Example/RealData-Inversion/'+filename)
            assert member.isfile()
            (work/filename).write_bytes(tar.extractfile(member).read())
    control=['dt.cc','dt.ct','event.dat','station.dat','output.loc','output.reloc','output.sta','output.res','output.src','output.vel','output.vp','output.vs','absolute.dat','3 3 100','0 6 0','2 2 2','2 0 0 1','40.82 14.14 0','0 0 0 1',
             '4 0.1 0.05 -9 -9 1 0.5 -9 -9 1 50 0 10','4 1 0.5 0.15 -9 0.1 0.05 0.3 -9 1 50 0 10','0']
    (work/'tomoDD.inp').write_text('\n'.join(control)+'\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-measurements',action='store_true');args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True);rf.OUT=OUT;rf.D=D;rf.DEST=DEST
    for pattern in ['round[12]_*.csv','round[12]_raw.txt']:
        for path in DEST.glob(pattern):path.unlink()
    ev,stations,picks=rf.observations()
    if args.reuse_measurements:
        receipt=json.loads((DEST/'measurement.json').read_text())
        for p,h in receipt['files'].items():assert rf.sha(ROOT/p)==h,p
        ct=pd.read_csv(DEST/'phase_pair_times.csv');cc=pd.read_csv(DEST/'accepted_differential_times.csv');measurement=receipt['summary']
    else:
        # Expanded event IDs differ from the previous 1003-event cohort.
        # No cache from that cohort is eligible, even when integers coincide.
        ct,cc,measurement=rf.measure(ev,picks,cache_path=WORK/'no_previous_cohort_cache.npz')
        files=[OUT/'filtered_events.csv',D/'picks.csv',D/'associations.csv',DEST/'retained_picks.csv',DEST/'observed_windows.npz',DEST/'phase_pair_times.csv',DEST/'accepted_differential_times.csv']
        (DEST/'measurement.json').write_text(json.dumps(dict(summary=measurement,files={str(p.relative_to(ROOT)):rf.sha(p) for p in files}),indent=2)+'\n')
    record=dict(status='running',accepted_scientific_catalog=False,measurement=measurement,runs=[],grid_sha256=rf.sha(ROOT/'data/grid_calibration/reference_grid.original'),
        settings='JOINT=0 fixed 3D; ten nearest neighbors; 2-second response-corrected windows; 1–15 Hz; coherence/correlation >=0.6; maximum lag .25 s; six common phase links; LSQR damping 50; 4+4 iterations; all connected clusters; absolute and phase-pair times from own picks, no author corrections; unnamed settings are explicit assumptions, not recovered Tan settings. Unused event magnitude/error format fields are zero, never empirical magnitudes.')
    for n in [1,2]:
        work=WORK/f'round{n}';write_inputs(work,ev,stations,picks,ct,cc)
        for path in work.glob('output.*'):path.unlink()
        try:
            r=subprocess.run([str(ROOT/'build/grid_tomodd/tomoDD-SE'),'tomoDD.inp'],cwd=work,capture_output=True,text=True,errors='replace',timeout=600);(work/'console.log').write_text(r.stdout+r.stderr)
            rec=dict(round=n,starting_events=len(ev),returncode=r.returncode,workdir=str(work.relative_to(ROOT)))
            path=work/'output.reloc'
            if r.returncode or not path.exists() or not path.stat().st_size:raise RuntimeError((r.stdout+r.stderr)[-2000:])
            a=np.loadtxt(path,ndmin=2);np.savetxt(DEST/f'round{n}_raw.txt',a);assert np.isfinite(a).all()
            # TomoDD's earthquake output is the generic HypoDD 24-column layout.
            assert a.shape[1]==24,a.shape
            output=pd.DataFrame(dict(event_index=a[:,0].astype(int)-1,latitude=a[:,1],longitude=a[:,2],depth_km=a[:,3],error_x_m=a[:,7],error_y_m=a[:,8],error_z_m=a[:,9],time=[str(UTCDateTime(*map(int,row[10:15]))+row[15]) for row in a],ncc_p=a[:,17].astype(int),ncc_s=a[:,18].astype(int),nct_p=a[:,19].astype(int),nct_s=a[:,20].astype(int),rms_cc_s=a[:,21],rms_s=a[:,22],cluster=a[:,23].astype(int))).set_index('event_index')
            residual=pd.read_csv(io.StringIO('\n'.join(line for line in (work/'output.res').read_text().splitlines() if not line.startswith('STA'))),sep=r'\s+',names=['alias','dt_s','event_a','event_b','phase_index','quality','residual_ms','weight','offset_m'])
            active=residual[residual.weight>0]
            assert set(output.index+1)<=set(active.event_a)|set(active.event_b),'Missing cluster residuals'
            gaps=[]
            for eid,e in output.iterrows():
                used=active.loc[(active.event_a==eid+1)|(active.event_b==eid+1),'alias'].unique()
                sta=stations.loc[used];az,_,_=Geod(ellps='WGS84').inv(np.full(len(sta),e.longitude),np.full(len(sta),e.latitude),sta.longitude,sta.latitude);aa=np.sort(np.mod(az,360));gaps.append(float(np.diff(np.r_[aa,aa[0]+360]).max()) if len(aa) else 360.)
            output['gap_deg']=gaps;output.to_csv(DEST/f'round{n}_locations.csv');ev=output[output.gap_deg<=300].copy()
            rec.update(output_events=len(output),gap_passing_events=len(ev),clusters=int(output.cluster.nunique()),depth_range_km=[float(output.depth_km.min()),float(output.depth_km.max())])
            assert rf.sha(work/'MOD')==record['grid_sha256']
            raw=np.fromstring((work/'MOD').read_text(),sep=' ');nx,ny,nz=raw[1:4].astype(int);vol=raw[4+nx+ny+nz:].reshape(2,nz,ny,nx)
            for label,expected in [('vp',vol[0]),('vs',vol[0]/vol[1])]:
                actual=np.loadtxt(work/('output.'+label)).reshape(nz,ny,nx);difference=float(abs(actual-expected).max())
                assert difference<=.000501,'Fixed grid changed beyond three-decimal serialization'
                rec['fixed_'+label+'_max_rounding_km_s']=difference
            residual.to_csv(DEST/f'round{n}_residuals.csv',index=False)
            rec['residual_RMS_s']={label:float(np.sqrt(np.mean(q.residual_ms**2))/1000) for label,q in [('waveform',active[active.phase_index<=2]),('phase',active[active.phase_index>2])]}
            rec['gap_observation_basis']='Stations with positive-weight final residuals in every cluster; rejected or downweighted-to-zero observations do not count.'
            rec['residual_events']=len(set(active.event_a)|set(active.event_b))
            rec['solver_statistic_caution']='output.reloc RMS columns divide summed residual squares by cluster event count, not observation count. Per-observation RMS is recomputed separately from output.res.'
            record['runs'].append(rec)
        except Exception as exc:
            record['runs'].append(dict(round=n,error=repr(exc),workdir=str(work.relative_to(ROOT))));break
        (DEST/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    record['status']='both fixed-grid rounds executed; validation pending' if len(record['runs'])==2 and 'error' not in record['runs'][-1] else 'relocation failed; diagnostic preserved'
    record['limitations']='Incomplete waveform coverage; calibration subset unreviewed; alternative GaMMA start and explicit inversion assumptions. Iteration passage does not establish correct event identity or absolute depth. No exact reproduction claim.'
    (DEST/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
    if record['status'].startswith('relocation failed'):raise SystemExit(1)
if __name__=='__main__':main()
