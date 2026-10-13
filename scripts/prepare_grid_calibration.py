"""Disclosed regional starting profiles from the specifically authorized Tan grid."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import pandas as pd
from obspy import UTCDateTime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/grid_calibration';D=ROOT/'data/calibration_followup/expanded'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    original=ROOT/'inputs/grid_reference/tan_distributed_3d_vmod';copy=OUT/'reference_grid.original'
    if original.exists():shutil.copyfile(original,copy)
    assert sha(copy)==json.loads((OUT/'source_access.json').read_text())['sha256']
    raw=np.fromstring(copy.read_text(),sep=' ');bld=raw[0];nx,ny,nz=raw[1:4].astype(int);i=4
    x=raw[i:i+nx];i+=nx;y=raw[i:i+ny];i+=ny;z=raw[i:i+nz];i+=nz
    assert len(raw)-i==2*nx*ny*nz
    vp,ratio=raw[i:].reshape(2,nz,ny,nx);vs=vp/ratio
    assert all(np.all(np.diff(a)>0) for a in [x,y,z]);assert (vp>0).all() and (ratio>1).all()
    bounds={'caldera':[14.01,14.21,40.76,40.87],'Pozzuoli_Solfatara':[14.11,14.16,40.80,40.84]}
    rows=[];layers=[];tops=np.array([-.5,.5,1,2,3,4,5,7.])
    for region,(xmin,xmax,ymin,ymax) in bounds.items():
        mask=(x[None,:]>=xmin)&(x[None,:]<=xmax)&(y[:,None]>=ymin)&(y[:,None]<=ymax)
        weights=np.broadcast_to(np.cos(np.deg2rad(y))[:,None],mask.shape)
        means=[]
        for k,depth in enumerate(z):
            valid=mask & ~np.isclose(vp[k],.1,rtol=0,atol=1e-8)
            w=weights[valid];p=np.average(vp[k][valid],weights=w) if len(w) else np.nan;s=np.average(vs[k][valid],weights=w) if len(w) else np.nan
            means.append([p,s]);rows.append(dict(region=region,depth_node_km_bsl=depth,vp_km_s=p,vs_km_s=s,rock_nodes=int(valid.sum()),excluded_air_nodes=int((mask&~valid).sum())))
        means=np.array(means)
        # 0.1 km is the first entirely solid horizontal plane. Its velocities
        # extend upward in the layered approximation; no .1-km/s air enters it.
        for n,top in enumerate(tops):
            upper=max(.1,top);lower=tops[n+1] if n+1<len(tops) else top
            sample=np.unique(np.r_[upper,z[(z>upper)&(z<lower)],lower]) if lower>upper else np.array([upper])
            values=np.array([np.interp(sample,z,means[:,j]) for j in range(2)])
            v= np.trapezoid(values,sample,axis=1)/(lower-upper) if len(sample)>1 else values[:,0]
            layers.append(dict(region=region,layer_top_km=top,Vp_km_s=v[0],Vs_km_s=v[1],VpVs=v[0]/v[1]))
    pd.DataFrame(rows).to_csv(OUT/'regional_node_means.csv',index=False);pd.DataFrame(layers).to_csv(OUT/'starting_profiles.csv',index=False)
    provenance=dict(**json.loads((OUT/'source_access.json').read_text()),reference_file=str(copy.relative_to(ROOT)),
      citation='Tan et al. (2025) distribution, pinned f84c9c9dc6bb1501a95a833f6634199a63d4f3b3; attributed to Battaglia et al. (2008), doi:10.1111/j.1365-2478.2007.00687.x',
      dimensions_xyz=[int(nx),int(ny),int(nz)],bld=float(bld),longitude_deg_E=x.tolist(),latitude_deg_N=y.tolist(),depth_km_below_sea_level=z.tolist(),
      encoding='SIMUL/TomoDD: x fastest, then y, then z; Vp km/s followed by dimensionless Vp/Vs. Vs calculated pointwise as Vp/(Vp/Vs).',
      format_basis='Generic TomoDD file-format manual and RaySPDR2.f model reader; geographic latitude/longitude ray tracing; depth negative above sea level.',
      original_2008_description='18 x 18 x 9 km, 0.5 km spacing, top 0.5 km above sea level; distributed irregular/padded grid differs and its historical transformation is unverified.',
      authorization='Current user explicitly permits this Tan-distributed grid as a disclosed starting/reference input. Not claimed independently sourced original 2008 bytes.',
      transforms='Original unchanged; only regional 1D approximation derived. No 3D regridding.',
      averaging=dict(boxes_deg=bounds,weights='cos(latitude) node weights, Vp and Vs averaged separately',excluded='Outer horizontal padding outside stated boxes; exact Vp=0.1 km/s nonsolid/air nodes; terminal depth 200 km not used to define shallow layers',
        layering='Layer tops -0.5,0.5,1,2,3,4,5,7 km; arithmetic depth integral of interpolated regional velocities; deepest layer uses 7-km node. First wholly solid plane (0.1 km) extends upward.',
        limitation='Boxes, coarse layer boundaries, node/depth weighting and air treatment are explicit assumptions; Tan gives region names but no numerical masks or discretization.'))
    (OUT/'grid_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    e=pd.read_csv(D/'initial_events.csv');p=pd.read_csv(D/'picks.csv');a=pd.read_csv(D/'associations.csv');sta=pd.read_csv(D/'stations.csv').set_index('id');q=[]
    for event in e.to_dict('records'):
        g=p.iloc[a.loc[a.event_index==event['event_index'],'pick_index']];travel=np.array([UTCDateTime(t)-UTCDateTime(event['time']) for t in g.time])
        xy=sta.loc[g.trace_id,['x(km)','y(km)']].drop_duplicates().to_numpy();az=np.sort(np.mod(np.degrees(np.arctan2(xy[:,0]-event['x(km)'],xy[:,1]-event['y(km)'])),360));gap=float(np.diff(np.r_[az,az[0]+360]).max())
        invalid_sp=0
        for _,h in g.groupby('trace_id'):
            pp=h[h.phase=='P'];ss=h[h.phase=='S']
            if len(pp)==len(ss)==1:invalid_sp+=int(UTCDateTime(ss.time.iloc[0])<=UTCDateTime(pp.time.iloc[0]))
        P=int((g.phase=='P').sum());S=int((g.phase=='S').sum());causal=bool((travel>0).all() and (travel<999).all() and invalid_sp==0)
        # Selection fixed before inversion, supported by generic best-P/gap
        # guidance; automated necessary checks do not replace manual review.
        calibration=causal and P>=4 and S>=2 and len(g)>10 and gap<180 and .001<event['z(km)']<7.999
        q.append(dict(event_index=event['event_index'],P=P,S=S,picks=len(g),gap_deg=gap,causal=causal,invalid_sp=invalid_sp,min_travel_s=float(travel.min()),calibration=calibration))
    quality=pd.DataFrame(q);quality.to_csv(OUT/'input_quality.csv',index=False)
    record=dict(events=len(e),usable_causal_events=int(quality.causal.sum()),calibration_events=int(quality.calibration.sum()),
      period=[e.time.min(),e.time.max()],processed_files=json.loads((D/'analysis_summary.json').read_text())['files'],stations=len(json.loads((D/'analysis_summary.json').read_text())['stations']),channel_hours=json.loads((D/'analysis_summary.json').read_text())['processed_channel_hours'],
      files={str((D/n).relative_to(ROOT)):sha(D/n) for n in ['picks.csv','associations.csv','initial_events.csv','stations.csv','processed_coverage_union.json']},
      selection='All causally consistent associations enter whole-catalog runs; calibration requires >=4 P, >=2 S, >10 total picks, gap<180 and no initial 0/8-km bound hit. Not the authors\' manually selected 373-event subset.',
      planned_correction='Set LOWVELOCLAY=0 per VELEST guide, replacing previous 1; coarse grid-derived layering; fixed-model prelocation before the two calibration rounds per guide p7. Retain original observations and thresholds.')
    (OUT/'input_inventory.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
if __name__=='__main__':main()
