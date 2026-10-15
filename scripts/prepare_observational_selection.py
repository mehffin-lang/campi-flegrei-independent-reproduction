"""Apply the unchanged independent causality/geometry screen, without a grid."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from obspy import UTCDateTime
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--observations',default='data/availability_extension/catalog');a=ap.parse_args();D=ROOT/a.observations;out=D/'selection';out.mkdir(exist_ok=True)
    ev=pd.read_csv(D/'initial_events.csv');p=pd.read_csv(D/'picks.csv');a=pd.read_csv(D/'associations.csv');sta=pd.read_csv(D/'stations.csv').set_index('id');rows=[]
    groups={i:g.pick_index.to_numpy(int) for i,g in a.groupby('event_index')}
    for e in ev.to_dict('records'):
        g=p.iloc[groups[e['event_index']]];t=np.array([UTCDateTime(x)-UTCDateTime(e['time']) for x in g.time]);xy=sta.loc[g.trace_id,['x(km)','y(km)']].drop_duplicates().to_numpy();az=np.sort(np.mod(np.degrees(np.arctan2(xy[:,0]-e['x(km)'],xy[:,1]-e['y(km)'])),360));gap=float(np.diff(np.r_[az,az[0]+360]).max())
        bad=0
        for _,h in g.groupby('trace_id'):
            pp=h[h.phase=='P'];ss=h[h.phase=='S']
            if len(pp)==len(ss)==1:bad+=int(UTCDateTime(ss.time.iloc[0])<=UTCDateTime(pp.time.iloc[0]))
        P=int((g.phase=='P').sum());S=int((g.phase=='S').sum());causal=bool((t>0).all() and (t<999).all() and bad==0)
        rows.append(dict(event_index=e['event_index'],P=P,S=S,picks=len(g),gap_deg=gap,causal=causal,invalid_sp=bad,calibration=causal and P>=4 and S>=2 and len(g)>10 and gap<180 and .001<e['z(km)']<7.999))
    q=pd.DataFrame(rows);q.to_csv(out/'input_quality.csv',index=False);ev[ev.event_index.isin(q[q.calibration].event_index)].to_csv(out/'selected_initial_events.csv',index=False)
    (out/'summary.json').write_text(json.dumps(dict(events=len(ev),causal=int(q.causal.sum()),calibration=int(q.calibration.sum()),selection='Same pre-inversion screen as prior checkpoint; necessary checks, not manual phase review.',inputs={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [D/'initial_events.csv',D/'picks.csv',D/'associations.csv',D/'stations.csv']}),indent=2)+'\n')
if __name__=='__main__':main()
