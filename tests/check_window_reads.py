"""Software check on real inputs: cached slicing versus bounded miniSEED reads.

This produces assertion records only, never empirical measurements or figures.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np
import pandas as pd
from obspy import read,UTCDateTime
ROOT=Path(__file__).resolve().parents[1]
picks=pd.read_csv(ROOT/'data/continuation/picks.csv')
picks=picks[picks.source.str.contains('inputs/continuation/waveforms/')]
checks=[]
for source in picks.source.value_counts().index[:3]:
    candidates=picks[picks.source.eq(source)].time
    times=[UTCDateTime(t) for t in candidates.iloc[::max(len(candidates)//20,1)].iloc[:20]]
    begin=time.monotonic();direct=[read(str(ROOT/source),starttime=t-30,endtime=t+30) for t in times];direct_s=time.monotonic()-begin
    begin=time.monotonic();full=read(str(ROOT/source));load_s=time.monotonic()-begin
    begin=time.monotonic();cached=[full.slice(t-30,t+30).copy() for t in times];slice_s=time.monotonic()-begin
    for left,right in zip(direct,cached):
        left.merge(method=0);right.merge(method=0);left=left.split().sort();right=right.split().sort()
        assert len(left)==len(right)
        for a,b in zip(left,right):
            assert a.id==b.id and a.stats.starttime==b.stats.starttime and a.stats.endtime==b.stats.endtime and np.array_equal(a.data,b.data)
    checks.append(dict(source=source,sha256=hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),window_centers=list(map(str,times)),
                       exact_samples_and_times=True,direct_read_s=direct_s,full_read_s=load_s,cached_slice_s=slice_s))
result=dict(passed=True,windows=sum(len(x['window_centers']) for x in checks),checks=checks,
            command='.venv/bin/python tests/check_window_reads.py',scope='Software equivalence check on selected observed windows, not a scientific finding or comprehensive proof for all possible miniSEED files.')
(ROOT/'tests/results/window_reads.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS:',result['windows'],'observed windows have identical samples and timing with both read paths.')
