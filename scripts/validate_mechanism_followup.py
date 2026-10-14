"""Review input integrity and frequency-band sensitivity of own source fits."""
from pathlib import Path
import json,hashlib,zipfile,os,re
import numpy as np,pandas as pd
from obspy.imaging.beachball import aux_plane
ROOT=Path(__file__).resolve().parents[1];D=ROOT/os.environ.get('CF_MECH_OUT','data/mechanism_followup');WROOT=ROOT/os.environ.get('CF_MECH_WORK','tmp/mechanism_followup')
def axes(strike,dip,rake):
    s,d,r=np.deg2rad([strike,dip,rake]);along=np.array([np.cos(s),np.sin(s),0.]);down=np.array([-np.sin(s)*np.cos(d),np.cos(s)*np.cos(d),np.sin(d)])
    n=np.cross(along,down);slip=np.cos(r)*along-np.sin(r)*down;t=(n+slip)/np.sqrt(2);p=(n-slip)/np.sqrt(2);b=np.cross(p,t)
    q=np.column_stack([t,b,p]);assert np.allclose(q.T@q,np.eye(3),atol=1e-12) and np.linalg.det(q)>0
    return q
def angle(a,b):
    aa=axes(*a);bb=axes(*b);angles=[]
    for d in [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]:
        angles.append(np.rad2deg(np.arccos(np.clip((np.trace(aa@np.diag(d)@bb.T)-1)/2,-1,1))))
    return float(min(angles))
def main():
    test=[(12.,34.,56.),(224.,63.,-129.)];checks=[angle(x,aux_plane(*x)) for x in test];assert max(checks)<1e-5
    a=pd.read_csv(D/'gcap/solutions.csv');b=pd.read_csv(D/'gcap_1_5/solutions.csv');paired=a.merge(b,on='event_id',suffixes=('_low','_high'));rows=[]
    for r in paired.itertuples():
        low=[getattr(r,k+'_low') for k in ['strike','dip','rake']];high=[getattr(r,k+'_high') for k in ['strike','dip','rake']]
        rows.append(dict(event_id=r.event_id,low_band_VR_percent=r.variance_reduction_percent_low,high_band_VR_percent=r.variance_reduction_percent_high,double_couple_rotation_deg=angle(low,high),accepted=False,reason='Own location/model and event settings remain unvalidated; assess the measured waveform fits and frequency-band rotation separately, without an invented variance-reduction acceptance threshold.'))
    table=pd.DataFrame(rows);table.to_csv(D/'gcap_band_sensitivity.csv',index=False)
    requirements=pd.read_csv(D/'candidate_requirements.csv')
    sk_solutions=pd.read_csv(D/'solutions.csv');geometry={};event=None
    for line in (D/'skhash.log').read_text().splitlines():
        match=re.search(r'\d+ / \d+\s+\((\d+)\)',line)
        if match:event=int(match[1])
        gap=re.search(r'Maximum azimuthal gap \(([-.\d]+)\) > max_agap \(([-.\d]+)\)',line)
        if gap and event is not None:geometry[event]=(float(gap[1]),float(gap[2]))
    for i,r in requirements.iterrows():
        g=table[table.event_id==r.event_id]
        result=sk_solutions[sk_solutions.event_id==r.event_id]
        requirements.loc[i,'skhash_solution_returned']=len(result)>0
        if len(result):
            q=result.iloc[0];requirements.loc[i,'unmet_requirement']=f'SKHASH returned quality {q.quality}, fault/auxiliary-plane uncertainty {q.fault_plane_uncertainty}/{q.aux_plane_uncertainty} deg. Provisional geometry, AI polarity review, and method sensitivity prevent scientific acceptance.'
        elif r.event_id in geometry:
            gap,limit=geometry[r.event_id];requirements.loc[i,'unmet_requirement']=f'SKHASH log reports perturbed-ray azimuth gap {gap:.3f} deg > {limit:.0f} deg; nominal surface-polarity gap is a separate diagnostic, not this solver gate.'
        if r.event_id==101760:requirements.loc[i,'unmet_requirement']+=' Near/pre-origin CAAM/COLB motion flags possible association/origin error.'
        if len(g):requirements.loc[i,'unmet_requirement']+=f' gCAP ran: VR {g.low_band_VR_percent.iloc[0]:.1f}% / {g.high_band_VR_percent.iloc[0]:.1f}%; orientation changes {g.double_couple_rotation_deg.iloc[0]:.1f} deg across bands. Reliable location/model and validated windows remain necessary.'
        else:
            reviewed=pd.read_csv(D/'review_decisions.csv');n=int(reviewed.loc[reviewed.event_id==r.event_id,'sp_accepted'].sum())
            requirements.loc[i,'unmet_requirement']+=f' {n} reviewed usable S/P packets; no surviving four-station gCAP trial. See the event-specific preprocessing log.'
    requirements.to_csv(D/'candidate_requirements.csv',index=False)
    receipt=dict(accepted=False,low_band=[.2,2],high_band=[1,5],events=len(table),low_band_variance_reduction_range_percent=[float(a.variance_reduction_percent.min()),float(a.variance_reduction_percent.max())],high_band_variance_reduction_range_percent=[float(b.variance_reduction_percent.min()),float(b.variance_reduction_percent.max())],orientation_rotation_range_deg=[float(table.double_couple_rotation_deg.min()),float(table.double_couple_rotation_deg.max())],method='Minimum proper rotation of ordered T/B/P double-couple frames over four determinant-positive sign symmetries. This compares two own gCAP trials, not SKHASH versus gCAP, not author mechanisms.',mathematical_checks=dict(auxiliary_nodal_plane_rotation_deg=checks),SKHASH='No surviving solution under unchanged 8-polarity/90-degree azimuth/60-degree plunge gates',limitations='AI rather than human review; approximate phase windows; fixed provisional locations/model; undocumented event filters, density/Q and source duration; external-filter gCAP port. High-band trial did not validate mechanism inference.')
    skhash=json.loads((D/'skhash_summary.json').read_text());receipt['SKHASH']=f"{skhash['computed_solutions']} computed solutions under unchanged 8-polarity/90-degree azimuth/60-degree plunge gates; scientific acceptance remains separate."
    sk=pd.read_csv(D/'solutions.csv');cross=[]
    for band,frame in [('0.2-2 Hz',a),('1-5 Hz',b)]:
        for _,row in sk.iterrows():
            matched=frame[frame.event_id==row.event_id]
            for other in matched.itertuples():
                cross.append(dict(event_id=int(row.event_id),gcap_band=band,kagan_angle_deg=angle([row[k] for k in ['strike','dip','rake']],[getattr(other,k) for k in ['strike','dip','rake']]),accepted=False))
    pd.DataFrame(cross,columns=['event_id','gcap_band','kagan_angle_deg','accepted']).to_csv(D/'skhash_gcap_comparison.csv',index=False)
    receipt['SKHASH_gCAP_comparisons']=len(cross)
    receipt['SKHASH_gCAP_comparison_scope']='Only own independent trial solutions, not published mechanisms. Empty if no shared solver solution; acceptance remains separate.'
    (D/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    files={}
    with zipfile.ZipFile(D/'gcap/run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for folder in ['gcap','gcap_1_5']:
            for path in sorted((WROOT/folder).rglob('*')):
                if path.is_file():name=str(path.relative_to(WROOT));z.write(path,name);files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (D/'gcap/run_records.json').write_text(json.dumps(dict(classification='Own original-observation preprocessing, own theoretical FK predictions and own fitted outputs; no author observations/solutions/examples',files=files),indent=2)+'\n')
if __name__=='__main__':main()
