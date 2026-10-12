"""Evaluate independent locations and attempt documented magnitude measurements.

No supplied Tan result file is read. Routine Md is used only after independent
association, as the external regularization input explicitly required by S6.
Unanchored components, events without amplitude-difference equations, and
unqualified locations do not receive fabricated calibrated magnitudes.
"""
from pathlib import Path
import os,json,itertools,argparse,concurrent.futures,multiprocessing,faulthandler
faulthandler.enable()
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',NUMBA_CACHE_DIR=str(ROOT/'tmp/numba'))
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
from gamma.seismic_ops import initialize_eikonal,calc_time
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--dataset',choices=['extended','continuation'],default='extended')
args=ap.parse_args()
OUT=Path('data')/args.dataset
events=pd.read_csv(OUT/'initial_events.csv');picks=pd.read_csv(OUT/'picks.csv')
assign=pd.read_csv(OUT/'associations.csv');stations=pd.read_csv(OUT/'stations.csv').set_index('id')
config=json.loads(Path('config/continuation_association.json' if args.dataset=='continuation' else 'config/association.json').read_text());eik=initialize_eikonal(config['eikonal'])
quality=[];measurements=[];waveforms={};errors=[];inventories={}
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
    eligible=len(ep)>6 and gap<180
    quality.append(dict(event_index=e['event_index'],picks=len(ep),stations=len(unique_xyz),rms_s=rms,azimuthal_gap_deg=gap,
        calibration_eligible=eligible,reason='VELEST manual geometry screen: >6 picks and gap<180 degrees; candidates still require waveform review'))
    for ident,g in ep.groupby('trace_id'):
        pp=g[g.phase=='P']
        point=stations.loc[[ident],['x(km)','y(km)','z(km)']].to_numpy()
        ptime=UTCDateTime(pp.time.iloc[0]) if len(pp) else UTCDateTime(e['time'])+float(calc_time(loc,point,np.array(['p']),eikonal=eik)[0,0])
        source=g.source.iloc[0]
        try:
            st=read(source,starttime=ptime-30,endtime=ptime+30).select(network=ident.split('.')[0],station=ident.split('.')[1],location=ident.split('.')[2])
            st.merge(method=0);st=st.split()
            response=Path('inputs/continuation')/(ident.split('.')[0]+'_responses.xml') if args.dataset=='continuation' else Path('inputs/extended/responses')/('_'.join(ident.split('.')[:2])+'.xml')
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
    # Independent event measurements share read-only input tables. Four processes
    # keep response removal and miniSEED decoding practical for the larger sample.
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
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
            for channel in common:
                la,rb=left[channel],right[channel];st=positions[la['station']]
                if separation>=min(np.linalg.norm(xa-st),np.linalg.norm(xb-st))/5:continue
                wa=normalized.get((aid,channel));wb=normalized.get((bid,channel))
                if wa is None or wb is None or len(wa)!=len(wb):continue
                cc=float(np.dot(wa,wb));valid.append(dict(event_a=aid,event_b=bid,station=la['station'],channel=channel,delta_M=np.log10(la['peak_velocity_m_s']/rb['peak_velocity_m_s']),weight=cc**2))
            passing_stations=len({r['station'] for r in valid})
            pair_audit.append(dict(event_a=aid,event_b=bid,separation_km=float(separation),snr_common_stations=len({left[c]['station'] for c in common}),qualifying_common_stations=passing_stations,accepted=passing_stations>=2))
            if passing_stations>=2:edges.extend(valid)
    pd.DataFrame(pair_audit,columns=['event_a','event_b','separation_km','snr_common_stations','qualifying_common_stations','accepted']).to_csv(OUT/'magnitude_pair_audit.csv',index=False)
    pd.DataFrame(edges,columns=['event_a','event_b','station','channel','delta_M','weight']).to_csv(OUT/'magnitude_edges.csv',index=False)
    external=pd.read_csv(OUT/('routine_catalog.csv' if args.dataset=='continuation' else 'external_routine_catalog.csv'));external['epoch']=pd.to_datetime(external.time,utc=True,format='ISO8601').map(lambda t:t.timestamp())
    matches=[]
    for e in events.to_dict('records'):
        # Match after independent detection/location. Never seeds the event list.
        near=external[abs(external.epoch-float(UTCDateTime(e['time'])))<=2]
        if len(near)==1:
            r=near.iloc[0]
            matches.append(dict(event_index=e['event_index'],external_id=r.id,Md=r.Md,time_difference_s=float(UTCDateTime(e['time']))-r.epoch,role='final comparison; potential S6 calibration prior only'))
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
    estimates=[]
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
            sol=np.linalg.lstsq(A,b,rcond=None)[0]
            estimates.extend(dict(event_index=v,ML=float(sol[ix[v]]),regularization_lambda=1.,status='provisional; alternative initial locations, no VELEST/TomoDD') for v in nodes)
    pd.DataFrame(estimates,columns=['event_index','ML','regularization_lambda','status']).to_csv(OUT/'magnitudes.csv',index=False)
    summary=dict(events_evaluated=len(events),calibration_eligible=len(eligible),amplitude_measurements=len(m),snr_passing=int(m.snr_pass.sum()) if len(m) else 0,event_pairs_checked=len(pair_audit),pairs_with_two_snr_stations=sum(r['snr_common_stations']>=2 for r in pair_audit),magnitude_edges=len(edges),calibrated_magnitudes=len(estimates),routine_matches=len(matches),ambiguous_reference_claims_rejected=len(ambiguous),measurement_errors=errors,
        focal_mechanisms=0,relocated_events=0,remaining='This magnitude pilot uses initial associations. See the separate VELEST record for its later inversion. TomoDD, HypoDD and focal processing remain unfinished; these magnitudes are not final relocated-catalog values.')
    (OUT/'downstream_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)

if __name__=='__main__':main()
