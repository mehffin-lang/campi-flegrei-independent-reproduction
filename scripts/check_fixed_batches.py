"""Check fixed-model batching against a simultaneous solve of real observations.

Only event hypocenters/origin times are adjustable. No velocity or station
correction is fitted here. This is a numerical consistency check, not new data
or evidence of accurate hypocenters.
"""
import concurrent.futures,json,os,re,time
os.environ.update(CF_GRID_BASE='data/eida_continuation/calibration',CF_GRID_WORK='tmp/eida_continuation',CF_OBSERVATIONS='data/eida_continuation')
import numpy as np,pandas as pd
import run_grid_velest as g

def main():
    root=g.ROOT;source=g.WORKROOT/'merged4/Pozzuoli_Solfatara_prelocation'
    out=g.BASE/'fixed_batch_check';out.mkdir(exist_ok=True)
    work=g.WORKROOT/'fixed_batch_check';work.mkdir(exist_ok=True);g.c.OUT=out;g.c.WORK=work
    ids=pd.read_csv(g.BASE/'merged4/selected_initial_events.csv').event_index.tolist()
    model=(source/'input.mod').read_text();sta=(source/'input.sta').read_text()
    blocks=re.split(r'\n\s*\n',(source/'input.cnv').read_text().strip());assert len(blocks)==len(ids)
    def run(i):
        w,loc,r=g.c.run(f'batch_{i:04d}',model,sta,'\n\n'.join(blocks[i:i+64])+'\n\n',ids[i:i+64],fixed=True,iterations=14)
        return loc,np.loadtxt(w/'residuals.txt',ndmin=2)[:,1],r
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,range(0,len(ids),64)))
    locations=pd.concat([x[0] for x in results],ignore_index=True);residuals=np.concatenate([x[1] for x in results])
    reference=g.BASE/'merged4/Pozzuoli_Solfatara_prelocation_locations.csv'
    while not reference.exists():time.sleep(10)
    full=pd.read_csv(reference);full_res=np.loadtxt(source/'residuals.txt',ndmin=2)[:,1]
    comparison=g.c.compare(full,locations)
    record=dict(method=__doc__,events=len(ids),batch_size=64,runs=[x[2] for x in results],comparison=comparison,
        maximum_printed_residual_difference_s=float(abs(full_res-residuals).max()),
        exactly_equal_printed_locations=bool(full.equals(locations)),
        exactly_equal_printed_residuals=bool(np.array_equal(full_res,residuals)),
        input_hashes={str((source/p).relative_to(root)):g.c.sha(source/p) for p in ['input.mod','input.sta','input.cnv','velest.cmn']})
    locations.to_csv(out/'batched_locations.csv',index=False);np.savetxt(out/'batched_residuals.txt',residuals)
    (out/'summary.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
if __name__=='__main__':main()
