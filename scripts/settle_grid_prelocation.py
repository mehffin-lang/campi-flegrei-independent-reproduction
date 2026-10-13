"""Test whether longer fixed-model prelocation resolves precision-path drift."""
import json
import pandas as pd
import run_grid_velest as g
c=g.c;ROOT=g.ROOT;OUT=ROOT/'data/grid_calibration/merged4/settled_trial';WORK=ROOT/'tmp/grid_calibration/settled_trial'
def main():
    OUT.mkdir(exist_ok=True);c.OUT=OUT;c.WORK=WORK
    src=ROOT/'tmp/grid_calibration/merged4/caldera_prelocation';ids=pd.read_csv(ROOT/'data/grid_calibration/merged4/selected_initial_events.csv').event_index.tolist()
    record=dict(reason='Original fixed-model prelocation stopped at its iteration limit. Generic VELEST guide recommends starting coupled inversion from well-located events; extend prelocation without changing damping, observations or gates.',runs=[],paths={},accepted=False)
    ends={}
    for bits in [32,64]:
        model=(src/'input.mod').read_text();sta=(src/'input.sta').read_text();text=(src/'input.cnv').read_text();previous=None
        settled=False
        for k in range(1,11):
            w,loc,r=c.run(f'prelocation{bits}_{k}',model,sta,text,ids,bits=bits,fixed=True,iterations=14)
            if previous is not None:
                change=c.compare(previous,loc);r['change']=change
                settled=change['max_horizontal_m']<=100 and change['max_depth_km']<=.1
            record['runs'].append(r);text=(w/'output.cnv').read_text();previous=loc
            if settled:break
        path=dict(prelocation_stable=settled,passes=k)
        if settled:
            try:
                w,loc,r=c.run(f'round1_{bits}',model,sta,text,ids,bits=bits);record['runs'].append(r)
                for name in ['round2','convergence1','convergence2','convergence3']:
                    old=loc
                    w,loc,r=c.run(f'{name}_{bits}',(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),ids,bits=bits,corrections=True)
                    r['change']=c.compare(old,loc);record['runs'].append(r)
                ends[bits]=(w,loc)
            except Exception as exc:path['error']=repr(exc)
        record['paths'][bits]=path
    if len(ends)==2:record['precision_change']=c.compare(ends[32][1],ends[64][1])
    record['interpretation']='This controlled longer-prelocation trial is not silently substituted for the current event catalog. Numerical stability, held-out prediction and phase review remain necessary.'
    (OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
