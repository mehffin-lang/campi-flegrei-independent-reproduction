"""Retrieve short network tie records for this project's new pre-2025 candidates.

These event-selected clips support arrival review/calibration only. They are not
continuous detection exposure and cannot establish completeness. Candidate
times are project GaMMA outputs, never a published or routine event catalog.
"""
import argparse,json,shutil
import pandas as pd
from obspy import UTCDateTime as U
import extend_velocity_training as e

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['plan','query','retrieve']);ap.add_argument('--catalog',default='catalog_dec12');ap.add_argument('--tag',default='ties_dec12');a=ap.parse_args()
    parent=e.D;cat=parent/a.catalog;out=parent/a.tag;inp=e.I/a.tag;out.mkdir(exist_ok=True);inp.mkdir(exist_ok=True)
    if a.stage=='plan':
        ev=pd.read_csv(cat/'initial_events.csv');q=pd.read_csv(cat/'selection/input_quality.csv')
        # Follow-up priority is not admission to training; final screen unchanged.
        candidates=ev[ev.event_index.isin(q[q.causal&q.P.ge(3)&q.S.ge(2)].event_index)].sort_values('time')
        assert (candidates.time<'2025-01-01').all();windows=[]
        for r in candidates.itertuples():
            t=float(U(r.time))
            if windows and t<windows[-1]['end']-10:windows[-1]['candidate_ids'].append(int(r.event_index));continue
            if len(windows)==4:break
            windows.append(dict(start=t-15,end=t+45,candidate_ids=[int(r.event_index)]))
        existing=pd.read_csv(parent/'pre2025_stored_intervals.csv');jobs=[]
        for w in windows:
            for sta in ['CAAM','CBAC','CFMN','COLB','CPOZ','CSOB','CSTH']:
                missing=[]
                for comp in 'ENZ':
                    g=existing[existing.channel.eq(f'IV.{sta}..HH{comp}')];missing.extend(e.av.subtract([(w['start'],w['end'])],zip(g.start,g.end)))
                if not missing:continue
                ident=f'IV_{sta}_HH_{U(w["start"]).strftime("%Y%m%dT%H%M%S")}_{U(w["end"]).strftime("%Y%m%dT%H%M%S")}'
                jobs.append(dict(id=ident,net='IV',sta=sta,band='HH',start=w['start'],end=w['end'],candidate_ids=w['candidate_ids'],missing_channel_s=sum(b-a for a,b in missing),estimated_bytes=300*3*(w['end']-w['start']+60)))
        e.dump(out/'download_plan.json',dict(requests=jobs,estimated_bytes=sum(j['estimated_bytes'] for j in jobs),rate_bytes_per_channel_second=300,role='Event-selected calibration tie windows, never continuous exposure.',candidate_source=str(cat.relative_to(e.R)),candidate_sha256=e.sha(cat/'initial_events.csv'),selection='Causal own association >=3P and >=2S; at most four chronological windows, merge adjacent detections; final training criteria are unchanged.',reason='Connect newly deployed target stations to stations represented in the pre-2025 calibration set; check whether nearby associations split one waveform packet.'))
        shutil.copy2(parent/'storage_budget.json',out/'storage_budget.json');existing.iloc[:0].to_csv(out/'target_existing_intervals.csv',index=False)
        print('Tie windows',len(windows),'station requests',len(jobs),'estimated bytes',sum(j['estimated_bytes'] for j in jobs),flush=True)
    else:
        e.D=out;e.I=inp
        getattr(e,a.stage)()
if __name__=='__main__':main()
