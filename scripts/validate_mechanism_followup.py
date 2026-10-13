"""Review input integrity and frequency-band sensitivity of own source fits."""
from pathlib import Path
import json,hashlib,zipfile
import numpy as np,pandas as pd
from obspy.imaging.beachball import aux_plane
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_followup'
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
        rows.append(dict(event_id=r.event_id,low_band_VR_percent=r.variance_reduction_percent_low,high_band_VR_percent=r.variance_reduction_percent_high,double_couple_rotation_deg=angle(low,high),accepted=False,reason='Low waveform variance reduction and sensitivity to frequency band; own location/model unvalidated'))
    table=pd.DataFrame(rows);table.to_csv(D/'gcap_band_sensitivity.csv',index=False)
    requirements=pd.read_csv(D/'candidate_requirements.csv')
    for i,r in requirements.iterrows():
        g=table[table.event_id==r.event_id]
        msg='Seven other candidates have fewer than eight reliable polarities.'
        if r.event_id==649:requirements.loc[i,'unmet_requirement']='SKHASH measured gap 96.57 deg exceeds unchanged max_agap=90 deg.'
        if len(g):requirements.loc[i,'unmet_requirement']+=f' gCAP ran: VR {g.low_band_VR_percent.iloc[0]:.1f}% / {g.high_band_VR_percent.iloc[0]:.1f}%; orientation changes {g.double_couple_rotation_deg.iloc[0]:.1f} deg across bands. Reliable location/model and validated windows remain necessary.'
        else:requirements.loc[i,'unmet_requirement']+=' Only one reviewed three-component packet; no four-station gCAP trial.'
    requirements.to_csv(D/'candidate_requirements.csv',index=False)
    receipt=dict(accepted=False,low_band=[.2,2],high_band=[1,5],events=len(table),low_band_variance_reduction_range_percent=[float(a.variance_reduction_percent.min()),float(a.variance_reduction_percent.max())],high_band_variance_reduction_range_percent=[float(b.variance_reduction_percent.min()),float(b.variance_reduction_percent.max())],orientation_rotation_range_deg=[float(table.double_couple_rotation_deg.min()),float(table.double_couple_rotation_deg.max())],method='Minimum proper rotation of ordered T/B/P double-couple frames over four determinant-positive sign symmetries. This compares two own gCAP trials, not SKHASH versus gCAP, not author mechanisms.',mathematical_checks=dict(auxiliary_nodal_plane_rotation_deg=checks),SKHASH='No surviving solution under unchanged 8-polarity/90-degree azimuth/60-degree plunge gates',limitations='AI rather than human review; approximate phase windows; fixed provisional locations/model; undocumented event filters, density/Q and source duration; external-filter gCAP port. High-band trial did not validate mechanism inference.')
    (D/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    files={}
    with zipfile.ZipFile(D/'gcap/run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for folder in ['gcap','gcap_1_5']:
            for path in sorted((ROOT/'tmp/mechanism_followup'/folder).rglob('*')):
                if path.is_file():name=str(path.relative_to(ROOT/'tmp/mechanism_followup'));z.write(path,name);files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (D/'gcap/run_records.json').write_text(json.dumps(dict(classification='Own original-observation preprocessing, own theoretical FK predictions and own fitted outputs; no author observations/solutions/examples',files=files),indent=2)+'\n')
if __name__=='__main__':main()
