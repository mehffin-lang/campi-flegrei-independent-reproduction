"""Compare saved precision paths; no new inversion or reference result is used."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
from pyproj import Geod
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';B=D/'calibration/merged4'
def main():
    rows=[];sources={};quality=pd.read_csv(D/'calibration/input_quality.csv').set_index('event_index')
    for stage in ['prelocation','round1','round2','convergence1','convergence2','convergence3']:
        paths=[B/f'Pozzuoli_Solfatara_{stage}_locations.csv',B/f'precision32_{stage}_locations.csv'];a,c=[pd.read_csv(p).set_index('event_index') for p in paths]
        depth=abs(a.depth_km-c.depth_km);horizontal=Geod(ellps='WGS84').inv(a.longitude.to_numpy(),a.latitude.to_numpy(),c.longitude.to_numpy(),c.latitude.to_numpy())[2];eid=int(depth.idxmax())
        rows.append(dict(stage=stage,events=len(a),max_depth_km=float(depth.max()),median_depth_km=float(depth.median()),p95_depth_km=float(depth.quantile(.95)),depth_difference_over_100m=int(depth.gt(.1).sum()),max_horizontal_m=float(horizontal.max()),median_horizontal_m=float(np.median(horizontal)),horizontal_over_100m=int((horizontal>100).sum()),worst_depth_event=eid,initial_P=int(quality.loc[eid,'P']),initial_S=int(quality.loc[eid,'S']),initial_gap_deg=float(quality.loc[eid,'gap_deg'])))
        sources.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    pd.DataFrame(rows).to_csv(D/'precision_diagnosis.csv',index=False)
    s=json.loads((B/'heldout/summary.json').read_text());notes=dict(sources=sources,initial_inputs_identical=all(x['identical'] for x in s['precision_initial_setup'].values()),interpretation='Identical observations, initial conditions and controls. Differences already occur in fixed-model prelocation, before model/station fitting, and amplify through later global update paths. Common-intermediate-start differences are smaller but nonzero. Both precision builds share the checked optimization. This excludes a simple input/setup mismatch and the tested zero-term optimization as explanations. The exact ill-conditioned mode or ray-path switch was not isolated; no assertion that the discrepancy is harmless rounding.',common_start=s['common_intermediate_start'],accepted=False)
    (D/'precision_diagnosis.json').write_text(json.dumps(notes,indent=2)+'\n');print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
