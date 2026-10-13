"""Evaluate independent locations and attempt documented magnitude measurements.

No supplied Tan result file is read. Routine Md is used only after independent
association, as the external regularization input described by the magnitude methods.
Unanchored components, events without amplitude-difference equations, and
unqualified locations do not receive fabricated calibrated magnitudes.
"""
from pathlib import Path
import os,json,itertools,argparse,concurrent.futures,multiprocessing,faulthandler
faulthandler.enable()
from collections import Counter
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'))
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
from gamma.seismic_ops import initialize_eikonal,calc_time
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--dataset',choices=['extended','continuation','grid'],default='extended')
ap.add_argument('--workers',type=int,default=16)
args=ap.parse_args()
GRID=Path(os.environ.get('CF_GRID_BASE','data/grid_calibration'))/'merged4'
OUT=GRID/'magnitude' if args.dataset=='grid' else Path('data')/args.dataset
OUT.mkdir(parents=True,exist_ok=True)
INPUT=Path(os.environ.get('CF_OBSERVATIONS','data/calibration_followup/expanded')) if args.dataset=='grid' else OUT
events=pd.read_csv(INPUT/'initial_events.csv');picks=pd.read_csv(INPUT/'picks.csv')
assign=pd.read_csv(INPUT/'associations.csv');stations=pd.read_csv(INPUT/'stations.csv').set_index('id')
coverage=pd.read_csv(INPUT/'processed_coverage.csv') if args.dataset in ['continuation','grid'] else None
config=json.loads(Path('config/continuation_association.json' if args.dataset in ['continuation','grid'] else 'config/association.json').read_text())
if args.dataset=='grid':
    from pyproj import Transformer
    import run_velest as v
    events=pd.read_csv(GRID/'uncertainty/relocated_events.csv')
    transform=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    events['x(km)'],events['y(km)']=transform.transform(events.longitude.to_numpy(),events.latitude.to_numpy());events['z(km)']=events.depth_km
    model=v.model_table(GRID/'independent_calibrated.mod')
    z=[];vp=[];vs=[]
    for i,r in model.iterrows():
        bottom=float(model.layer_top_km.iloc[i+1]-.00001) if i+1<len(model) else max(16.,events.depth_km.max()+1)
        z.extend([r.layer_top_km,bottom]);vp.extend([r.Vp_km_s]*2);vs.extend([r.Vs_km_s]*2)
    config['eikonal']['vel']=dict(z=z,p=vp,s=vs);config['eikonal']['zlim']=[-.5,16]
    # Original picks are still used where available. This own 1-D fit supplies
    # only missing theoretical P windows; station corrections are omitted and
    # this approximation is disclosed. No routine arrival or location is used.
eik=initialize_eikonal(config['eikonal'])
quality=[];measurements=[];waveforms={};errors=[];inventories={}
causality=(pd.read_csv(OUT/'association_quality.csv').set_index('event_index').passes_causality.to_dict()
           if args.dataset=='continuation' else {int(e):True for e in events.event_index})
@lru_cache(maxsize=32)
def original_stream(source):
    # Per-worker cache of unchanged observations. Every measured window is copied
    # before detrending or response removal, so the cached samples stay original.
    return read(source)

def evaluate_event(e):
    quality=[];measurements=[];waveforms={};errors=[]
    ep=picks.iloc[assign.loc[assign.event_index==e['event_index'],'pick_index'].to_numpy(int)].copy()
    xyz=stations.loc[ep.trace_id,['x(km)','y(km)','z(km)']].to_numpy()
    loc=np.array([[e['x(km)'],e['y(km)'],e['z(km)'],0.]])
    calculated=calc_time(loc,xyz,ep.phase.str.lower().to_numpy(),eikonal=eik).ravel()
    residual=np.array([UTCDateTime(t)-UTCDateTime(e['time']) for t in ep.time])-calculated
    unique_xyz=np.unique(xyz,axis=0)
    az=np.sort(np.mod(np.degrees(np.arctan2(unique_xyz[:,0]-loc[0,0],unique_xyz[:,1]-loc[0,1])),360))
    gap=float(np.diff(np.r_[az,az[0]+360]).max());rms=float(np.sqrt(np.mean(residual**2)))
    # Generic VELEST guidance defines geometry/minimum observations; Tan's
    # 0.25-s RMS rejection belongs AFTER location, not before calibration.
    causal=bool(causality[e['event_index']])
    eligible=len(ep)>6 and gap<180 and causal
    quality.append(dict(event_index=e['event_index'],picks=len(ep),stations=len(unique_xyz),rms_s=rms,azimuthal_gap_deg=gap,
        passes_causality=causal,calibration_eligible=eligible,reason='Necessary travel-time and S>P causality, >6 picks, gap<180 degrees; candidates still require waveform review. Causality is an explicit additional screen.'))
    grouped={ident:g for ident,g in ep.groupby('trace_id')}
    # Include recorded stations even when the picker/association has no phase
    # there; the written method explicitly permits theoretical P arrivals.
    for ident in (stations.index if coverage is not None else grouped):
        g=grouped.get(ident,ep.iloc[:0])
        pp=g[g.phase=='P']
        point=stations.loc[[ident],['x(km)','y(km)','z(km)']].to_numpy()
        ptime=UTCDateTime(pp.time.iloc[0]) if len(pp) else UTCDateTime(e['time'])+float(calc_time(loc,point,np.array(['p']),eikonal=eik)[0,0])
        if len(g):source=g.source.iloc[0]
        else:
            spans=coverage[(coverage.channel.str.startswith(ident+'.'))&(coverage.start<=float(ptime)-2)&(coverage.end>=float(ptime)+5)]
            if spans.empty:continue
            source=spans.sort_values('file').iloc[0].file
        try:
            st=original_stream(source).select(network=ident.split('.')[0],station=ident.split('.')[1],location=ident.split('.')[2]).slice(ptime-30,ptime+30).copy()
            st.merge(method=0);st=st.split()
            response=Path('inputs/continuation')/(ident.split('.')[0]+'_responses.xml') if args.dataset in ['continuation','grid'] else Path('inputs/extended/responses')/('_'.join(ident.split('.')[:2])+'.xml')
            if not response.exists():response=Path('inputs/extended/responses')/('_'.join(ident.split('.')[:2])+'.xml')
            if str(response) not in inventories:inventories[str(response)]=read_inventory(str(response))
            inv=inventories[str(response)]
            st.detrend('demean');st.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
            for tr in st:
                fs=tr.stats.sampling_rate
                signal=tr.copy().trim(ptime,ptime+5-1/fs);noise=tr.copy().trim(ptime-2,ptime-1/fs)
                if len(signal.data)!=round(5*fs) or len(noise.data)!=round(2*fs):continue
                snr=10*np.log10(np.mean(signal.data**2)/max(np.mean(noise.data**2),np.finfo(float).tiny))
                amp=float(np.max(abs(signal.data)))
                key=(e['event_index'],tr.id);waveforms[key]=signal.data
                measurements.append(dict(event_index=e['event_index'],channel=tr.id,station=ident,arrival=str(ptime),arrival_kind='picked' if len(pp) else 'theoretical',snr_db=float(snr),peak_velocity_m_s=amp,snr_pass=snr>=5,source=source))
        except Exception as exc: errors.append(dict(event_index=e['event_index'],station=ident,error=repr(exc)))
    return quality,measurements,waveforms,errors

def main():
    quality=[];measurements=[];waveforms={};errors=[]
    # Independent event measurements share read-only input tables. Spawned processes
    # keep response removal and miniSEED decoding practical for the larger sample.
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        for i,(qr,mr,wr,er) in enumerate(pool.map(evaluate_event,events.to_dict('records'))):
            quality.extend(qr);measurements.extend(mr);waveforms.update(wr);errors.extend(er)
            if i%25==0:print('Measured events',i+1,'of',len(events),flush=True)
    q=pd.DataFrame(quality);q.to_csv(OUT/'location_quality.csv',index=False)
    m=pd.DataFrame(measurements,columns=['event_index','channel','station','arrival','arrival_kind','snr_db','peak_velocity_m_s','snr_pass','source']);m.to_csv(OUT/'amplitude_measurements.csv',index=False)
    eligible=set(q.loc[q.calibration_eligible,'event_index']);edges=[];pair_audit=[]
    # Magnitude diagnostics use all independently associated events. The narrower
    # VELEST calibration-subset geometry screen must not silently restrict the
    # whole-catalog magnitude procedure. No pair is a final calibrated result until
    # the independent location stages have been completed.
    if len(m):
        passing={int(eid):{r['channel']:r for r in group.to_dict('records')} for eid,group in m[m.snr_pass].groupby('event_index')}
        positions={key:row[config['dims']].to_numpy(float) for key,row in stations.iterrows()}
        normalized={}
        for key,values in waveforms.items():
            centered=values-values.mean();norm=np.linalg.norm(centered)
            if norm>0:normalized[key]=centered/norm
        for a,b in itertools.combinations(events.to_dict('records'),2):
            aid,bid=a['event_index'],b['event_index']
            xa=np.array([a[k] for k in config['dims']]);xb=np.array([b[k] for k in config['dims']]);separation=np.linalg.norm(xa-xb)
            left=passing.get(aid,{});right=passing.get(bid,{})
            common=sorted(set(left)&set(right));valid=[]
            causal_pair=bool(causality[aid] and causality[bid])
            for channel in (common if causal_pair else []):
                la,rb=left[channel],right[channel];st=positions[la['station']]
                if separation>=min(np.linalg.norm(xa-st),np.linalg.norm(xb-st))/5:continue
                wa=normalized.get((aid,channel));wb=normalized.get((bid,channel))
                if wa is None or wb is None or len(wa)!=len(wb):continue
                cc=float(np.dot(wa,wb));valid.append(dict(event_a=aid,event_b=bid,station=la['station'],channel=channel,delta_M=np.log10(la['peak_velocity_m_s']/rb['peak_velocity_m_s']),weight=cc**2))
            passing_stations=len({r['station'] for r in valid})
            pair_audit.append(dict(event_a=aid,event_b=bid,separation_km=float(separation),snr_common_stations=len({left[c]['station'] for c in common}),qualifying_common_stations=passing_stations,causality_eligible_pair=causal_pair,accepted=passing_stations>=2))
            if passing_stations>=2:edges.extend(valid)
    pd.DataFrame(pair_audit,columns=['event_a','event_b','separation_km','snr_common_stations','qualifying_common_stations','causality_eligible_pair','accepted']).to_csv(OUT/'magnitude_pair_audit.csv',index=False)
    pd.DataFrame(edges,columns=['event_a','event_b','station','channel','delta_M','weight']).to_csv(OUT/'magnitude_edges.csv',index=False)
    external=pd.read_csv(Path('data/continuation/routine_catalog.csv') if args.dataset=='grid' else OUT/('routine_catalog.csv' if args.dataset=='continuation' else 'external_routine_catalog.csv'));external['epoch']=pd.to_datetime(external.time,utc=True,format='ISO8601').map(lambda t:t.timestamp())
    matches=[]
    for e in events.to_dict('records'):
        if not causality[e['event_index']]:continue
        # Match after independent detection/location. Never seeds the event list.
        near=external[abs(external.epoch-float(UTCDateTime(e['time'])))<=2]
        if len(near)==1:
            r=near.iloc[0]
            matches.append(dict(event_index=e['event_index'],external_id=r.id,Md=r.Md,time_difference_s=float(UTCDateTime(e['time']))-r.epoch,role='external routine duration-magnitude calibration prior; not an independent detection or validation'))
    # A unique candidate for one event can still be claimed by several independent
    # events. Do not turn that ambiguous coincidence into multiple calibration
    # anchors. This changes no detected event or location.
    reference_counts=Counter(r['external_id'] for r in matches)
    ambiguous=[r for r in matches if reference_counts[r['external_id']]>1]
    pd.DataFrame(ambiguous,columns=['event_index','external_id','Md','time_difference_s','role']).to_csv(OUT/'ambiguous_routine_matches.csv',index=False)
    matches=[r for r in matches if reference_counts[r['external_id']]==1]
    pd.DataFrame(matches,columns=['event_index','external_id','Md','time_difference_s','role']).to_csv(OUT/'routine_matches.csv',index=False)
    # Solve only components containing measured relative-amplitude equations.
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse import coo_matrix
    estimates=[];inversion_checks=[]
    if edges:
        ids=sorted({r['event_a'] for r in edges}|{r['event_b'] for r in edges});index={v:i for i,v in enumerate(ids)}
        graph=coo_matrix((np.ones(len(edges)),([index[r['event_a']] for r in edges],[index[r['event_b']] for r in edges])),shape=(len(ids),len(ids)))
        _,labels=connected_components(graph,directed=False)
        for group in np.unique(labels):
            nodes=[v for v in ids if labels[index[v]]==group];ix={v:i for i,v in enumerate(nodes)}
            priors=[r for r in matches if r['event_index'] in nodes and np.isfinite(r['Md'])]
            if not priors:continue
            A=[];b=[]
            for r in edges:
                if r['event_a'] not in ix:continue
                row=np.zeros(len(nodes));w=np.sqrt(r['weight']);row[ix[r['event_a']]]=w;row[ix[r['event_b']]]=-w;A.append(row);b.append(w*r['delta_M'])
            for r in priors:
                row=np.zeros(len(nodes));row[ix[r['event_index']]]=1.;A.append(row);b.append(r['Md'])
            A=np.asarray(A);b=np.asarray(b)
            sol,_,rank,singular=np.linalg.lstsq(A,b,rcond=None)
            dof=len(b)-rank;residual=A@sol-b
            check=dict(component=int(group),events=len(nodes),equations=len(b),rank=int(rank),residual_dof=int(dof),calibration_priors=len(priors),weighted_residual_sum_squares=float(residual@residual),accepted=bool(rank==len(nodes)))
            inversion_checks.append(check)
            if rank!=len(nodes):continue
            sigma=np.sqrt(np.maximum(np.diag(np.linalg.pinv(A.T@A))*(residual@residual)/dof,0)) if dof>0 else np.full(len(nodes),np.nan)
            estimates.extend(dict(event_index=v,ML=float(sol[ix[v]]),formal_sigma_ML=float(sigma[ix[v]]),residual_dof=int(dof),regularization_lambda=1.,status='provisional; independent grid-based relocation' if args.dataset=='grid' else 'provisional; alternative initial locations; formal uncertainty conditional on weighting/prior assumptions') for v in nodes)
    pd.DataFrame(estimates,columns=['event_index','ML','formal_sigma_ML','residual_dof','regularization_lambda','status']).to_csv(OUT/'magnitudes.csv',index=False)
    (OUT/'magnitude_inversion_checks.json').write_text(json.dumps(dict(components=inversion_checks,
        uncertainty='Residual-scaled inverse normal matrix of the weighted amplitude/prior system. Conditional on unit Md prior weight and independent homoscedastic weighted errors; excludes absolute calibration, response, association, location and exposure errors. Undefined when residual degrees of freedom are zero.'),indent=2)+'\n')
    summary=dict(events_evaluated=len(events),causality_excluded_events=sum(not bool(v) for v in causality.values()),calibration_eligible=len(eligible),amplitude_measurements=len(m),snr_passing=int(m.snr_pass.sum()) if len(m) else 0,event_pairs_checked=len(pair_audit),pairs_with_two_snr_stations=sum(r['snr_common_stations']>=2 for r in pair_audit),magnitude_edges=len(edges),calibrated_magnitudes=len(estimates),routine_matches=len(matches),ambiguous_reference_claims_rejected=len(ambiguous),measurement_errors=errors,
        focal_mechanisms=0,relocated_events=0,remaining='This magnitude pilot uses initial associations. See the separate VELEST record for its later inversion. TomoDD, HypoDD and focal processing remain unfinished; these magnitudes are not final relocated-catalog values.')
    if args.dataset=='grid':
        summary.update(relocated_events=len(events),remaining='Own two-round TomoDD trial locations, with unresolved calibration path sensitivity. Routine Md anchors only after independent detection/location. Theoretical P windows use own calibrated 1D fit without station delay; amplitudes are response-corrected velocity maxima. Unit regularization and unshifted normalized correlation squared are disclosed assumptions. Formal errors exclude location, calibration and coverage bias.')
        import hashlib
        summary['sources']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [INPUT/'picks.csv',INPUT/'associations.csv',INPUT/'stations.csv',GRID/'uncertainty/relocated_events.csv',GRID/'independent_calibrated.mod',Path('data/continuation/routine_catalog.csv')]}
    (OUT/'downstream_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)

if __name__=='__main__':main()
