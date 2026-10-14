"""Compare generic fixed-model location modes on 20 existing own events.

VELEST guide pp. 3, 13 and appendix recommend single-event mode for locating a
catalog with fixed velocities and station corrections. This is a method check,
not additional observations or accepted event locations.
"""
from pathlib import Path
import json,re,time
import pandas as pd
import calibration_chain as c
ROOT=c.ROOT
def main():
    c.OUT=ROOT/'data/eida_continuation/single_mode_check';c.WORK=ROOT/'tmp/eida_continuation/single_mode_check';c.OUT.mkdir(exist_ok=True);c.WORK.mkdir(exist_ok=True)
    source=ROOT/'tmp/local_extension/merged4/whole_catalog_pass1'
    ids=pd.read_csv(ROOT/'data/local_extension/calibration/merged4/whole_catalog_pass1_locations.csv').event_index.tolist()[:20]
    blocks=re.split(r'\n\s*\n',(source/'input.cnv').read_text().strip())[:20];cnv='\n\n'.join(blocks)+'\n\n';model=(source/'input.mod').read_text();sta=(source/'input.sta').read_text();base=c.v.controls;record=dict(method=__doc__,events=20,runs=[])
    outputs={}
    for single in [False,True]:
        def controls(*args,**kwargs):
            lines=base(*args,**kwargs).splitlines()
            if single:lines[3]='1 0'
            return '\n'.join(lines)+'\n'
        c.v.controls=controls;start=time.monotonic();name='single' if single else 'simultaneous'
        try:
            w,loc,r=c.run(name,model,sta,cnv,ids,corrections=True,fixed=True);r['wall_seconds']=time.monotonic()-start;record['runs'].append(r);outputs[name]=loc
        except Exception as exc:record['runs'].append(dict(name=name,error=repr(exc),wall_seconds=time.monotonic()-start))
    if len(outputs)==2:record['difference']=c.compare(outputs['single'],outputs['simultaneous'])
    record['input_files']={str(p.relative_to(ROOT)):c.sha(p) for p in [source/'input.cnv',source/'input.mod',source/'input.sta',ROOT/'inputs/extended/velest_guide.pdf']}
    (c.OUT/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
if __name__=='__main__':main()
