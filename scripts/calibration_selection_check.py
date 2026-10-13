"""One declared selection sensitivity test, without published-result targets.

At least four P and two S observations provide information for both velocity
fields; optimizer depth-bound hits are excluded. These are explicit additional
criteria, not attributed to Tan. No result from this test replaces the main fit.
"""
import json
import numpy as np
import pandas as pd
import calibration_chain as c

def main():
    events=pd.read_csv(c.OUT/'calibration_selection.csv');quality=pd.read_csv(c.D/'association_quality.csv').set_index('event_index')
    selected=events[(events.num_p_picks>=4)&(events.num_s_picks>=2)&~events.event_index.map(quality.depth_boundary)]
    selected.to_csv(c.OUT/'stricter_selection.csv',index=False)
    picks=pd.read_csv(c.D/'picks.csv');assign=pd.read_csv(c.D/'associations.csv')
    aliases=pd.read_csv(c.OUT/'station_aliases.csv').set_index('id').alias.to_dict()
    original=c.WORK/'calibration_64_round1';model=(original/'input.mod').read_text();stations=(original/'input.sta').read_text()
    record=dict(events=len(selected),selection='Prior 130-event set plus >=4P, >=2S and no initial depth-bound hit; explicit alternative selection, no author catalog.',runs=[],accepted_scientific_calibration=False)
    for label,train,test in [('all',selected,None),('validation',selected.iloc[[i for i in range(len(selected)) if i%5]],selected.iloc[::5])]:
        ids=train.event_index.tolist();text=c.v.cnv(train,picks,assign,aliases)
        name='strict_'+label+'_round1'
        try:
            w,loc,r=c.run(name,model,stations,text,ids);record['runs'].append(r)
            name='strict_'+label+'_round2'
            w,loc,r=c.run(name,(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),ids,corrections=True);record['runs'].append(r)
        except (AssertionError,RuntimeError) as exc:
            record['runs'].append(dict(name=name,status='rejected',error=str(exc),workdir=str((c.WORK/name).relative_to(c.ROOT))))
            continue
        if test is None:
            previous=loc
            for i in range(1,6):
                old=c.v.model_table(w/'velout.mod')
                name='strict_extra'+str(i)
                try:
                    w,loc,r=c.run(name,(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()),(w/'output.cnv').read_text(),ids,corrections=True)
                except (AssertionError,RuntimeError) as exc:
                    record['runs'].append(dict(name=name,status='rejected',error=str(exc),workdir=str((c.WORK/name).relative_to(c.ROOT))))
                    # Never propagate a rejected velocity model. The held-out
                    # branch below starts again from the published alternative.
                    break
                r['change']=c.compare(previous,loc);r['max_velocity_change_km_s']=float(np.max(abs(old[['Vp_km_s','Vs_km_s']].to_numpy()-c.v.model_table(w/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy())))
                record['runs'].append(r);previous=loc
        else:
            for name,mod,sta in [('starting',model,stations),('fitted',(w/'velout.mod').read_text(),c.normalize_stations((w/'output.sta').read_text()))]:
                _,_,r=c.run('strict_heldout_'+name,mod,sta,c.v.cnv(test,picks,assign,aliases),test.event_index.tolist(),corrections=True,fixed=True,iterations=21);record['runs'].append(r)
    record['interpretation']='Selection sensitivity only. No manual phase review, independent absolute-location truth, verified 2008 grid or representative multiyear coverage; no promotion to accepted calibration.'
    (c.OUT/'selection_sensitivity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':main()
