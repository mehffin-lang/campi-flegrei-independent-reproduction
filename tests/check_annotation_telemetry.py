"""Real-data equivalence check; no synthetic samples or reference phase labels."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import process_continuous as p
from obspy import read
p.initialize_worker()
file='inputs/extended/waveforms/IV_CMIS_2024-01-01T12:00:00_2024-01-01T12:30:00.mseed'
stream=read(str(ROOT/file));stream.merge(method=0);stream=stream.split()
stream.detrend('demean');stream.filter('highpass',freq=1,corners=4,zerophase=False)
first=p.NET.classify(stream,P_threshold=.3,S_threshold=.3,batch_size=128)
args=dict(p.NET.default_args,P_threshold=.3,S_threshold=.3,batch_size=128)
annotations=p.NET.annotate(p.NET.classify_stream_pre(stream,args),**args)
second=p.NET.classify_aggregate(annotations,args)
def values(result):return [(v.trace_id,v.phase,str(v.peak_time),float(v.peak_value)) for v in result.picks]
assert values(first)==values(second)
out=dict(passed=True,input=file,input_sha256=hashlib.sha256((ROOT/file).read_bytes()).hexdigest(),picks=len(first.picks),
    check='Exact identity of classify and explicit annotate/aggregate on one real 30-minute recording. A code-path equivalence test, not an accuracy estimate.')
(ROOT/'tests/results/annotation_telemetry.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
