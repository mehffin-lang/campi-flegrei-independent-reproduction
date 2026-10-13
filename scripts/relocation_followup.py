"""Exploratory HypoDD processing of this project's alternative-model locations.

This is not TomoDD or a reproduction of S7. No published location, magnitude,
background grid or event list is used. Saved observed windows may be reused;
neighbor pairs and differential times are recomputed for the new locations.
"""
from pathlib import Path
import os,json,re,subprocess,hashlib,concurrent.futures,multiprocessing,argparse
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from obspy import UTCDateTime
from pyproj import Transformer
import differential_times as dd
from calibration_chain import ROOT,OUT,WORK,sha

D=ROOT/'data/continuation'
DEST=OUT/'relocation'
BIN=ROOT/'build/hypodd21/src/hypoDD/hypoDD'


def observations():
    events=pd.read_csv(OUT/'filtered_events.csv').set_index('event_index')
    all_events=pd.read_csv(OUT/'located_events.csv')
    aliases=pd.read_csv(OUT/'station_aliases.csv').set_index('alias')
    picks=pd.read_csv(D/'picks.csv')
    assigned=pd.read_csv(D/'associations.csv').merge(picks,left_on='pick_index',right_index=True)
    lookup=assigned.set_index(['event_index','trace_id','phase'])
    rows=[];errors=[]
    blocks=re.split(r'\n\s*\n',(OUT/'located_events.cnv').read_text().strip())
    assert len(blocks)==len(all_events)
    for eid,block in zip(all_events.event_index,blocks):
        if eid not in events.index:continue
        for line in block.splitlines()[1:]:
            for i in range(0,len(line.rstrip()),12):
                tok=line[i:i+12];alias=tok[:4];phase=tok[4];station=aliases.loc[alias,'id']
                original=lookup.loc[(eid,station,phase)]
                assert isinstance(original,pd.Series),'Ambiguous event/station/phase'
                travel=float(UTCDateTime(original.time)-UTCDateTime(events.loc[eid,'time']))
                # Check CNV handoff against original absolute pick, including
                # accumulated centisecond serialization. Never replace the pick.
                error=float(tok[6:12])-travel
                errors.append(error)
                rows.append(dict(event_index=int(eid),alias=alias,trace_id=station,phase=phase,
                                 pick_index=int(original.pick_index),time=original.time,
                                 travel_s=travel,source=original.source,cnv_drift_s=error))
    frame=pd.DataFrame(rows)
    assert frame.shape[0]==int(events.num_picks.sum())
    assert np.max(np.abs(errors))<=.06, 'CNV handoff changed absolute arrivals beyond rounding'
    frame.to_csv(DEST/'retained_picks.csv',index=False)
    return events,aliases,frame


def measure(events,picks):
    arrays=dict(np.load(D/'differential_waveform_windows.npz'))
    missing=[]
    for r in picks.to_dict('records'):
        if any(f'e{r["event_index"]}_{r["trace_id"]}_{r["phase"]}_{c}' not in arrays for c in (['Z'] if r['phase']=='P' else ['N','E'])):missing.append(r)
    errors=[]
    if missing:
        jobs=[(source,g.to_dict('records')) for source,g in pd.DataFrame(missing).groupby('source')]
        with concurrent.futures.ProcessPoolExecutor(max_workers=6,mp_context=multiprocessing.get_context('spawn')) as pool:
            for wave,failed in pool.map(dd.windows,jobs):
                arrays.update({f'e{e}_{s}_{p}_{c}':v for (e,s,p,c),v in wave.items()});errors.extend(failed)
    # Save only observed windows actually belonging to this event/phase set.
    keys={f'e{r.event_index}_{r.trace_id}_{r.phase}_{c}' for r in picks.itertuples() for c in (['Z'] if r.phase=='P' else ['N','E'])}
    np.savez_compressed(DEST/'observed_windows.npz',**{k:v for k,v in arrays.items() if k in keys})
    transform=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    x,y=transform.transform(events.longitude.to_numpy(),events.latitude.to_numpy())
    tree=cKDTree(np.c_[x,y,events.depth_km]);near=tree.query(tree.data,k=min(11,len(events)))[1]
    pairs=sorted({tuple(sorted((int(events.index[i]),int(events.index[j])))) for i,neighbors in enumerate(near) for j in neighbors if i!=j})
    groups={eid:g.set_index(['trace_id','phase']) for eid,g in picks.groupby('event_index')}
    rows=[];ct=[]
    for a,b in pairs:
        for station,phase in groups[a].index.intersection(groups[b].index):
            pa,pb=groups[a].loc[(station,phase)],groups[b].loc[(station,phase)]
            ct.append(dict(event_a=a,event_b=b,alias=pa.alias,phase=phase,tt_a=pa.travel_s,tt_b=pb.travel_s,weight=1.0))
            for comp in (['Z'] if phase=='P' else ['N','E']):
                ka=f'e{a}_{station}_{phase}_{comp}';kb=f'e{b}_{station}_{phase}_{comp}'
                if ka not in arrays or kb not in arrays:continue
                result=dd.delay(arrays[ka],arrays[kb])
                rows.append(dict(event_a=a,event_b=b,alias=pa.alias,station=station,phase=phase,component=comp,
                                 differential_time_s=pa.travel_s-pb.travel_s-result['delay_y_minus_x_s'],**result))
    rows=pd.DataFrame(rows);ct=pd.DataFrame(ct)
    rows.to_csv(DEST/'waveform_differential_times.csv',index=False);ct.to_csv(DEST/'phase_pair_times.csv',index=False)
    good=rows[rows.measurement_pass];cc=[]
    for (a,b,sta,phase),g in good.groupby(['event_a','event_b','alias','phase']):
        cc.append(dict(event_a=a,event_b=b,alias=sta,phase=phase,dt_s=float(np.average(g.differential_time_s,weights=g.mean_coherence)),weight=float(g.mean_coherence.mean()),components=len(g)))
    cc=pd.DataFrame(cc);cc.to_csv(DEST/'accepted_differential_times.csv',index=False)
    (DEST/'window_failures.json').write_text(json.dumps(errors,indent=2)+'\n')
    return ct,cc,dict(neighbor_pairs=len(pairs),catalog_pair_phases=len(ct),measured_channels=len(rows),accepted_channels=len(good),accepted_phase_delays=len(cc),window_failures=len(errors),max_cnv_rounding_s=float(picks.cnv_drift_s.abs().max()))


def write_inputs(work,events,aliases,ct,cc,svd=False):
    work.mkdir(parents=True,exist_ok=True)
    ids=set(events.index);ct=ct[ct.event_a.isin(ids)&ct.event_b.isin(ids)];cc=cc[cc.event_a.isin(ids)&cc.event_b.isin(ids)]
    # Rebase original travel-time differences when the starting origins change.
    initial=pd.read_csv(OUT/'filtered_events.csv').set_index('event_index')
    shifts={i:float(UTCDateTime(events.loc[i,'time'])-UTCDateTime(initial.loc[i,'time'])) for i in ids}
    text=[]
    for (a,b),g in ct.groupby(['event_a','event_b']):
        text.append(f'# {a+1} {b+1}')
        text.extend(f'{r.alias} {r.tt_a-shifts[a]:.6f} {r.tt_b-shifts[b]:.6f} 1.0 {r.phase}' for r in g.itertuples())
    (work/'dt.ct').write_text('\n'.join(text)+'\n')
    text=[]
    for (a,b),g in cc.groupby(['event_a','event_b']):
        text.append(f'# {a+1} {b+1} 0.0')
        text.extend(f'{r.alias} {r.dt_s-shifts[a]+shifts[b]:.6f} {r.weight:.6f} {r.phase}' for r in g.itertuples())
    (work/'dt.cc').write_text('\n'.join(text)+'\n')
    text=[]
    for eid,e in events.iterrows():
        t=UTCDateTime(e.time);date=t.strftime('%Y%m%d');clock=t.hour*1000000+t.minute*10000+round((t.second+t.microsecond/1e6)*100)
        text.append(f'{date} {clock:08d} {e.latitude:.6f} {e.longitude:.6f} {e.depth_km:.4f} 0.0 0.0 0.0 {e.rms_s:.4f} {eid+1}')
    (work/'event.dat').write_text('\n'.join(text)+'\n')
    text=[f'{a} {r.latitude:.6f} {r.longitude:.6f} {-r["z(km)"]*1000:.1f}' for a,r in aliases.iterrows()]
    (work/'station.dat').write_text('\n'.join(text)+'\n')
    model=pd.read_csv(OUT/'calibration_64_round2_model.csv')
    # Readable numerical settings, not fitted to published plots. Clustering
    # needs six common phase links. SVD uses no LSQR damping.
    lines=['hypoDD_2','dt.cc','dt.ct','event.dat','station.dat','output.loc','output.reloc','output.sta','output.res','output.src',
           '3 3 100','0 6 0 100 300',f'2 {1 if svd else 2} 1 2',
           '4 0.1 0.05 -999 -999 1 0.5 -999 -999 50',
           '4 1 0.5 0.15 -999 0.1 0.05 0.3 -999 50','1',
           ' '.join(map(str,model.layer_top_km)), ' '.join(map(str,model.Vp_km_s)), ' '.join(map(str,model.VpVs)), '1' if svd else '0']
    (work/'hypoDD.inp').write_text('\n'.join(lines)+'\n')


def execute(name,events,aliases,ct,cc,svd=False):
    work=ROOT/'tmp/calibration_followup'/name
    write_inputs(work,events,aliases,ct,cc,svd)
    for pattern in ['output.*','hypoDD.log']:
        for path in work.glob(pattern):path.unlink()
    r=subprocess.run([str(BIN),'hypoDD.inp'],cwd=work,capture_output=True,text=True,errors='replace',timeout=300)
    (work/'console.log').write_text(r.stdout+r.stderr)
    record=dict(name=name,returncode=r.returncode,starting_events=len(events),svd=svd,workdir=str(work.relative_to(ROOT)),
                cluster_selection='largest connected component only' if svd else 'all connected clusters')
    path=work/'output.reloc'
    if r.returncode or not path.exists() or not path.stat().st_size:
        record['error']=(r.stdout+r.stderr)[-1500:];return None,record
    a=np.loadtxt(path,ndmin=2)
    output=pd.DataFrame(dict(event_index=a[:,0].astype(int)-1,latitude=a[:,1],longitude=a[:,2],depth_km=a[:,3],
                  error_x_m=a[:,7],error_y_m=a[:,8],error_z_m=a[:,9],
                  time=[str(UTCDateTime(int(row[10]),int(row[11]),int(row[12]),int(row[13]),int(row[14]))+row[15]) for row in a],
                  ncc_p=a[:,17].astype(int),ncc_s=a[:,18].astype(int),nct_p=a[:,19].astype(int),nct_s=a[:,20].astype(int),rms_cc_s=a[:,21],rms_ct_s=a[:,22],cluster=a[:,23].astype(int))).set_index('event_index')
    assert np.isfinite(a).all();output['rms_s']=output.rms_ct_s
    output.to_csv(DEST/(name+'.csv'))
    record.update(output_events=len(output),clusters=int(output.cluster.nunique()),median_depth_km=float(output.depth_km.median()),
                  max_error_z_m=float(output.error_z_m.max()),max_depth_km=float(output.depth_km.max()))
    return output,record


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-measurements',action='store_true');args=parser.parse_args()
    events,aliases,picks=observations()
    if args.reuse_measurements:
        receipt=json.loads((DEST/'measurement.json').read_text())
        for p,h in receipt['files'].items():assert sha(ROOT/p)==h,p
        ct=pd.read_csv(DEST/'phase_pair_times.csv');cc=pd.read_csv(DEST/'accepted_differential_times.csv');measurement=receipt['summary']
    else:
        ct,cc,measurement=measure(events,picks)
        receipt=dict(summary=measurement,files={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'filtered_events.csv',DEST/'retained_picks.csv',DEST/'phase_pair_times.csv',DEST/'accepted_differential_times.csv',DEST/'observed_windows.npz']})
        (DEST/'measurement.json').write_text(json.dumps(receipt,indent=2)+'\n')
    record=dict(status='exploratory',not_TomoDD=True,not_published_S7=True,accepted_scientific_result=False,
                events=len(events),measurement=measurement,runs=[],
                settings='10 nearest neighbors; existing 2 s observed windows and coherency delay method; six-phase cluster links; variable Vp/Vs alternative fit; two four-iteration weight blocks; LSQR damping 50, no SVD damping; SVD restricted to largest connected component in each quadrant after recorded failures of underconstrained smaller components. Magnitudes and initial errors zero only as unused format fields.',
                input_sha256={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'filtered_events.csv',OUT/'located_events.cnv',OUT/'calibration_64_round2_model.csv',D/'picks.csv',D/'associations.csv',D/'differential_waveform_windows.npz']})
    current=events
    for n in [1,2]:
        result,r=execute('hypodd_round'+str(n),current,aliases,ct,cc);record['runs'].append(r)
        if result is None:break
        current=result
    if len(record['runs'])==2 and 'error' not in record['runs'][-1]:
        # Geographic quadrant tests are explicit alternatives; Tan's four
        # selection boxes are not supplied numerically in the written methods.
        for name,mask in [('NW',(current.longitude<14.14)&(current.latitude>=40.82)),('NE',(current.longitude>=14.14)&(current.latitude>=40.82)),('SW',(current.longitude<14.14)&(current.latitude<40.82)),('SE',(current.longitude>=14.14)&(current.latitude<40.82))]:
            sample=current[mask]
            if len(sample)>175:sample=sample.sample(175,random_state=42).sort_index()
            if len(sample)<4:record['runs'].append(dict(name='svd_'+name,error='Fewer than four candidate events',starting_events=len(sample)));continue
            _,r=execute('svd_'+name,sample,aliases,ct,cc,svd=True);record['runs'].append(r)
    record['limitation']='HypoDD pilot is a separate alternative-model test, not the requested fixed-3D TomoDD rounds or S7 after accepted calibration. Weak/disconnected components and waveform identities require review; covariance is conditional, not absolute accuracy.'
    (DEST/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':main()
