"""Own processing of raw FDSN observations; permitted model weights only."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['SEISBENCH_CACHE_ROOT']=str(ROOT/'tmp/seisbench');os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import csv,json,hashlib
import numpy as np
from scipy.signal import spectrogram
from obspy import read,read_inventory,UTCDateTime
cfg=json.loads(Path('config/observations.json').read_text())
OUT=Path('data/observations');OUT.mkdir(parents=True,exist_ok=True)
def write(name,rows):
 if not rows: return
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Independently check source identities against retrieval receipts before analysis.
for item in json.loads(Path('docs/observation_inputs.json').read_text()):
 if 'sha256' in item: assert hashlib.sha256(Path(item['file']).read_bytes()).hexdigest()==item['sha256']
coverage=[]
for f in sorted(Path('inputs/waveforms').glob('*.mseed')):
 for tr in read(str(f),headonly=True):
  coverage.append(dict(file=str(f),channel=tr.id,start=str(tr.stats.starttime),end=str(tr.stats.endtime),samples=tr.stats.npts,sample_rate=tr.stats.sampling_rate))
write('coverage.csv',coverage)
# S2 subset: study station names from explicitly permitted metadata, coordinates from official epochs.
study={row[0].split('.')[1] for row in list(csv.reader(open('inputs/models/stations.csv')))[1:]}
stations={}
for row in list(csv.reader(open('inputs/models/stations.csv')))[1:]:
 station=row[0].split('.')[1]
 stations[station]=dict(station=station,latitude=float(row[2]),longitude=float(row[1]),elevation_m=float(row[3]),source='inputs/models/stations.csv')
for line in Path('inputs/metadata/channels.txt').read_text().splitlines():
 if line.startswith('#'): continue
 v=line.split('|')
 if v[1] in study: stations[v[1]]=dict(station=v[1],latitude=float(v[4]),longitude=float(v[5]),elevation_m=float(v[6]),source='inputs/metadata/channels.txt')
write('stations.csv',list(stations.values()))
metadata_names=sorted({line.split('|')[1] for line in Path('inputs/metadata/channels.txt').read_text().splitlines() if not line.startswith('#')})
(OUT/'station_access.json').write_text(json.dumps(dict(metadata_available=metadata_names,waveforms_retrieved=sorted({r['channel'].split('.')[1] for r in coverage}),coverage_file='data/observations/coverage.csv',caution='Metadata availability does not imply waveform availability. Other stations were not tested.'),indent=2)+'\n')
inv=read_inventory('inputs/metadata/response.xml');metrics=[];tests=[]
for label,time in cfg['template_times'].items():
 t=UTCDateTime(time);streams={}
 for station in ['CAAM','COLB']:
  st=read('inputs/waveforms/'+label+'_'+station+'.mseed');assert not st.get_gaps()
  for tr in st:
   assert tr.stats.sampling_rate==100 and np.isfinite(tr.data).all()
  # Sensitivity conversion to physical velocity; full response removal is not specified in S15.
  st.detrend('demean');st.remove_sensitivity(inv);streams[station]=st
 rows=[]
 for component in ['Z','E']:
  ca=streams['CAAM'].select(component=component)[0].copy().trim(t-cfg['display_seconds_before'],t+cfg['display_seconds_after'])
  norm=max(abs(ca.data));assert norm>0
  for station in ['CAAM','COLB']:
   tr=streams[station].select(component=component)[0].copy().trim(t-cfg['display_seconds_before'],t+cfg['display_seconds_after'])
   x=tr.data/norm;tt=tr.times()+float(tr.stats.starttime-t)
   rows.extend(dict(station=station,component=component,time_s=a,velocity_m_s=b,normalized=c) for a,b,c in zip(tt,tr.data,x))
   ff,ts,p=spectrogram(x,fs=100,window='hann',nperseg=cfg['spectrogram_nperseg'],noverlap=cfg['spectrogram_noverlap'],detrend='constant',scaling='density')
   np.savez_compressed(OUT/(label+'_'+station+'_'+component+'_spectrum.npz'),frequency=ff,time=ts+tt[0],power=p)
   if station=='CAAM': tests.append(dict(check=label+component+'_normalization',passed=bool(np.isclose(max(abs(x)),1))))
 write(label+'_waveforms.csv',rows)
 tr=streams['CAAM'].select(component='Z')[0].copy().trim(t,t+8-0.01)
 x=tr.data-np.mean(tr.data);n=len(x);assert n==800
 freqs=np.fft.rfftfreq(n,.01);power=abs(np.fft.rfft(x))**2/n**2;power[1:-1]*=2
 low=power[(freqs>=2)&(freqs<=5)].sum();high=power[(freqs>=8)&(freqs<=15)].sum()
 fi=np.log10(high/low)
 tests.append(dict(check=label+'_parseval',passed=bool(np.isclose(power.sum(),np.mean(x*x),rtol=1e-12,atol=0))))
 metrics.append(dict(template=label,window_start=str(t),samples=n,FI=fi,low_power=low,high_power=high,window_rule='written origin time to +8s; onset alignment uncertain'))
write('template_metrics.csv',metrics)
# Model loading explicitly restricts PyTorch to tensor weights.
import torch,seisbench.models as sbm
meta=json.loads(Path('inputs/models/phasenet_retrained.json').read_text())
torch.set_num_threads(2);torch.manual_seed(0)
model=sbm.PhaseNet(**meta['model_args'])
state=torch.load('inputs/models/phasenet_retrained.pt',map_location='cpu',weights_only=True)
model.load_state_dict(state,strict=True);model.eval();model.default_args.update(meta['default_args']);model.default_args.update(overlap=cfg['picker_overlap_samples'],blinding=cfg['picker_blinding_samples'])
picks=[];hourly=[]
for file in sorted(Path('inputs/waveforms').glob('day_*.mseed')):
 st=read(str(file));hour=int(file.stem.split('_')[-1]);start=UTCDateTime(cfg['independent_calendar_day'])+hour*3600;st.trim(start,start+3600-.01);gaps=st.get_gaps()
 # Do not fabricate missing observations by interpolating gaps.
 st=st.split();st.detrend('demean');st.filter('highpass',freq=cfg['picker_highpass_hz'],corners=cfg['picker_filter_corners'],zerophase=cfg['picker_zerophase'])
 result=model.classify(st,P_threshold=cfg['picker_threshold'],S_threshold=cfg['picker_threshold'],batch_size=64)
 count=0
 for p in result.picks:
  row=dict(source=str(file),trace_id=p.trace_id,phase=p.phase,time=str(p.peak_time),probability=float(p.peak_value))
  assert cfg['picker_threshold']<=row['probability']<=1
  picks.append(row);count+=1
 hourly.append(dict(source=str(file),picks=count,gaps=len(gaps)))
 print(file,count,flush=True)
# Adjacent chunks share endpoints; retain unique peak/phase/station tuples.
unique={(p['trace_id'],p['phase'],p['time']):p for p in picks};picks=sorted(unique.values(),key=lambda p:p['time'])
write('picks.csv',picks);write('hourly_counts.csv',hourly)
tests.append(dict(check='all_pick_probabilities_in_bounds',passed=all(cfg['picker_threshold']<=p['probability']<=1 for p in picks)))
assert all(t['passed'] for t in tests)
# Independent template matching on the same calendar day, prior to manual review.
# Candidate scores are not a reviewed event catalog or the paper's 70-event list.
from scipy.signal import fftconvolve,find_peaks

def normalized_correlation(x,y):
 y=y-y.mean();n=len(y);norm=np.linalg.norm(y)
 sums=np.r_[0.,np.cumsum(x)];sq=np.r_[0.,np.cumsum(x*x)]
 var=(sq[n:]-sq[:-n])-(sums[n:]-sums[:-n])**2/n
 denom=np.sqrt(np.maximum(var,0))*norm
 numerator=fftconvolve(x,y[::-1],mode='valid')
 return np.divide(numerator,denom,out=np.zeros_like(numerator),where=denom>0)

templates={}
for label,time in cfg['template_times'].items():
 templates[label]={}
 for station in ['CAAM','COLB']:
  st=read('inputs/waveforms/'+label+'_'+station+'.mseed').select(component='Z')
  st.detrend('demean');st.filter('bandpass',freqmin=.2,freqmax=6,corners=4,zerophase=False)
  t=UTCDateTime(time);y=st[0].copy().trim(t,t+7.99).data.astype(float)
  assert len(y)==800
  selfscore=float(normalized_correlation(y,y)[0]);assert abs(selfscore-1)<1e-10
  assert abs(float(normalized_correlation(3*y,y)[0])-1)<1e-10
  templates[label][station]=y
  injected=np.zeros(3000);injected[1200:2000]=y
  scores=normalized_correlation(injected,y)
  assert np.argmax(scores)==1200 and abs(scores[1200]-1)<1e-10
candidates=[];scan_intervals=[]
for hour in range(24):
 traces={};requested_start=UTCDateTime(cfg['independent_calendar_day'])+hour*3600
 for station in ['CAAM','COLB']:
  file=Path('inputs/waveforms/day_'+station+'_'+str(hour).zfill(2)+'.mseed')
  if not file.exists():continue
  st=read(str(file)).select(component='Z');st.trim(requested_start,requested_start+3599.99)
  if len(st)!=1 or st.get_gaps():continue
  st.detrend('demean');st.filter('bandpass',freqmin=.2,freqmax=6,corners=4,zerophase=False)
  traces[station]=st[0]
 if len(traces)!=2:continue
 start=max(tr.stats.starttime for tr in traces.values());end=min(tr.stats.endtime for tr in traces.values())
 arrays={sta:tr.copy().trim(start,end).data.astype(float) for sta,tr in traces.items()}
 assert len({len(x) for x in arrays.values()})==1
 count=len(arrays['CAAM']);assert count>2800
 scan_intervals.append(dict(hour=hour,start=str(start),end=str(end),samples=count,valid_window_starts=count-800+1-2000))
 for label in templates:
  score=sum(normalized_correlation(arrays[sta],templates[label][sta]) for sta in arrays)/2
  assert np.isfinite(score).all() and np.max(abs(score))<=1+1e-6
  scan_intervals[-1]['maximum_correlation_'+label]=float(np.max(score[1000:-1000]))
  # Exclude 10-second chunk edges; end exclusion includes the 8-second template duration.
  score[:1000]=0;score[-1000:]=0
  peaks,_=find_peaks(score,height=.25,distance=800)
  candidates.extend(dict(template=label,time=str(start+int(i)/100),mean_correlation=float(score[i]),reviewed=False) for i in peaks)
write('template_scan_coverage.csv',scan_intervals)
assert len(scan_intervals)==24, 'Expected one actual common interval per hour; inspect coverage'
tests.append(dict(check='template_scan_covers_all_24_hourly_intervals',passed=True))
with (OUT/'template_candidates.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['template','time','mean_correlation','reviewed']);w.writeheader();w.writerows(candidates)
tests.append(dict(check='template_self_correlation',passed=True))
tests.append(dict(check='template_injection_timing',passed=True))
summary=dict(template_scan_hours=len(scan_intervals),template_valid_start_seconds=sum(x['valid_window_starts'] for x in scan_intervals)/100,template_candidates=len(candidates),stations=len(stations),waveform_records=len(coverage),files=len(set(r['file'] for r in coverage)),picks=len(picks),phase_counts={p:sum(x['phase']==p for x in picks) for p in ['P','S']},tests=tests,templates=metrics,model_inference='SeisBench PhaseNet with authorized retrained weights; own preprocessing',association_performed=False,metadata_coordinate_policy='official INGV where available, permitted station CSV otherwise',picker_window_samples=model.in_samples)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
