"""Retry only the SVD component interrupted by generic zero-CC logging.

The different component rejected as airquakes is preserved without rerunning.
All other completed conditional estimates remain unchanged.
"""
from pathlib import Path
import hashlib,json,zipfile
import pandas as pd
import relocation_followup as rf
ROOT=rf.ROOT;D=ROOT/'data/eida_continuation';B=D/'calibration/merged4';U=B/'uncertainty';W=ROOT/'tmp/eida_continuation/uncertainty'
def main():
    s=json.loads((U/'summary.json').read_text());old=s.copy();selected=[(i,r) for i,r in enumerate(s['svd_runs']) if "array 'sta_lab'" in r.get('error','')]
    events=pd.read_csv(U/'relocated_events.csv').set_index('event_index');aliases=pd.read_csv(B/'station_aliases.csv').set_index('alias');ct=pd.read_csv(B/'tomodd/phase_pair_times.csv');cc=pd.read_csv(B/'tomodd/accepted_differential_times.csv')
    rf.OUT=B;rf.DEST=U;rf.RUN_ROOT=ROOT/'tmp/eida_continuation/hypodd_logging_repair';rf.MODEL_PATH=U/'model.csv'
    if selected:
        assert len(selected)==1,selected
        i,r=selected[0];name=r['name'];source=W/name
        with zipfile.ZipFile(D/'hypodd_logging_failure.zip','w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('summary_before_repair.json',json.dumps(old,indent=2))
            for p in source.iterdir():
                if p.is_file():z.write(p,str(p.relative_to(ROOT)))
        ids=[int(x.split()[-1])-1 for x in (source/'event.dat').read_text().splitlines()]
        out,run=rf.execute(name,events.loc[ids],aliases,ct,cc,svd=True)
        checks={f:(source/f).read_bytes()==(rf.RUN_ROOT/name/f).read_bytes() for f in ['event.dat','station.dat','dt.ct','dt.cc','hypoDD.inp']};assert all(checks.values()),checks
        run.update(region=r['region'],component=r['component'],input_byte_equality=checks,previous_error='Preserved in hypodd_logging_failure.zip; logging station index zero with no CC data.')
        s['svd_runs'][i]=run
        combined=pd.read_csv(U/'regional_svd.csv')
        if out is not None:
            out=out.reset_index();out['region']=r['region'];out['component']=r['component'];out['finite_positive_errors']=(out[['error_x_m','error_y_m','error_z_m']]>0).all(axis=1)
            assert not set(out.event_index)&set(combined.event_index)
            combined=pd.concat([combined,out],ignore_index=True);combined.to_csv(U/'regional_svd.csv',index=False)
        s['svd_events']=len(combined);s['logging_repair']='data/eida_continuation/hypodd_logging_repair.json';(U/'summary.json').write_text(json.dumps(s,indent=2)+'\n')
    else:
        run=next(q for q in s['svd_runs'] if 'previous_error' in q);checks=run['input_byte_equality'];combined=pd.read_csv(U/'regional_svd.csv');out=pd.read_csv(U/(run['name']+'.csv')) if run.get('output_events') else None
    # A small previously successful component checks that the diagnostic fix
    # changes no locations or error estimates for an otherwise executable run.
    base=min((q for q in s['svd_runs'] if q.get('output_events',0)>0 and 'previous_error' not in q),key=lambda q:q['output_events']);oldfile=(U/(base['name']+'.csv')).read_bytes();src=W/base['name'];ids=[int(x.split()[-1])-1 for x in (src/'event.dat').read_text().splitlines()]
    checked,checkrun=rf.execute('logging_check',events.loc[ids],aliases,ct,cc,svd=True)
    identical=(U/'logging_check.csv').read_bytes()==oldfile;assert identical,'HypoDD logging fix changed an executable component'
    result=dict(repaired_run=run,added_estimates=0 if out is None else len(out),total_estimates=len(combined),same_input_files=checks,successful_component_comparison=dict(reference=base['name'],byte_identical=identical,run=checkrun),accepted_scientific_locations=False)
    (D/'hypodd_logging_repair.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
