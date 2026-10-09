"""Plot only saved results of our observational processing."""
from pathlib import Path
import os,csv,json
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path('data/observations');F=Path('figures');F.mkdir(exist_ok=True)
def rows(file):return list(csv.DictReader((D/file).open()))
def save(fig,name):
 fig.savefig(F/(name+'.pdf'),bbox_inches='tight');fig.savefig(F/(name+'.png'),dpi=140,bbox_inches='tight');plt.close(fig)
s=rows('stations.csv');fig,ax=plt.subplots(figsize=(8,6))
ax.scatter([float(x['longitude']) for x in s],[float(x['latitude']) for x in s],marker='^',c='black')
offsets={'CAAM':(-65,-45),'COLB':(40,-35),'CSOB':(-75,35),'CSTH':(45,40)}
for x in s:
 if x['station'] in offsets:
  point=(float(x['longitude']),float(x['latitude']))
  ax.scatter(*point,color='tab:blue',s=25,zorder=4)
  ax.annotate(x['station'],point,fontsize=8,xytext=offsets[x['station']],textcoords='offset points',arrowprops=dict(arrowstyle='-',color='tab:blue',lw=.6),bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
ax.plot([],[],marker='^',linestyle='',color='black',label='All permitted station coordinates')
ax.plot([],[],marker='o',linestyle='',color='tab:blue',label='Waveform stations (labeled)');ax.legend(fontsize=8,loc='lower right')
ax.set(xlabel='Longitude (degrees E)',ylabel='Latitude (degrees N)',title='S2 partial: permitted station metadata (51-station inventory)');ax.set_aspect(1/np.cos(np.deg2rad(40.82)))
save(fig,'stations_partial')
for label in ['E1','E2','E3']:
 rr=rows(label+'_waveforms.csv');fig,axes=plt.subplots(4,2,figsize=(10,9),sharex=True)
 for i,(station,comp) in enumerate([(s,c) for s in ['CAAM','COLB'] for c in ['Z','E']]):
  r=[x for x in rr if x['station']==station and x['component']==comp]
  axes[i,0].plot([float(x['time_s']) for x in r],[float(x['normalized']) for x in r],lw=.6)
  axes[i,0].set_ylabel(station+' HH'+comp+'\nnormalized velocity')
  a=np.load(D/(label+'_'+station+'_'+comp+'_spectrum.npz'))
  use=a['frequency']<=20
  axes[i,1].pcolormesh(a['time'],a['frequency'][use],10*np.log10(np.maximum(a['power'][use],1e-20)),shading='auto',cmap='magma',vmin=-80,vmax=0)
  axes[i,1].set_ylabel('Frequency (Hz)')
 for ax in axes[-1]:ax.set_xlabel('Seconds from written template time')
 fig.suptitle(label+(': S15C partial' if label=='E3' else ': related template, not the published S15 example')+'\nSpectral color: dB relative to normalized-unit²/Hz, −80 to 0');fig.tight_layout(rect=(0,0,1,.94));save(fig,'hybrid_'+label)
r=rows('hourly_counts.csv');stations=sorted(set(x['source'].split('_')[-2] for x in r))
fig,ax=plt.subplots(figsize=(9,4))
for station in stations:
 rr=[x for x in r if '_'+station+'_' in x['source']]
 ax.plot([int(x['source'].split('_')[-1].split('.')[0]) for x in rr],[int(x['picks']) for x in rr],'.-',label=station)
ax.set(xlabel='UTC hour on 2024-01-01',ylabel='P and S picks (not earthquakes)',title='Independent PhaseNet inference; calendar-selected validation day');ax.legend();fig.tight_layout();save(fig,'independent_picks')

# Actual downloaded coverage, not deployment epochs.
from datetime import datetime
import matplotlib.dates as mdates
cov=rows('coverage.csv');fig,ax=plt.subplots(figsize=(10,4))
names=sorted(set(x['channel'].split('.')[1] for x in cov))
for x in cov:
 station=x['channel'].split('.')[1]
 start=datetime.fromisoformat(x['start'].replace('Z','+00:00'));end=datetime.fromisoformat(x['end'].replace('Z','+00:00'))
 ax.plot([start,end],[names.index(station)]*2,linewidth=5,solid_capstyle='butt',color='navy')
ax.set_yticks(range(len(names)),names);ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'));ax.set(title='S1 partial: retrieved waveform intervals only',xlabel='UTC date (narrow intervals may be smaller than a pixel)');fig.tight_layout();save(fig,'coverage_partial')
