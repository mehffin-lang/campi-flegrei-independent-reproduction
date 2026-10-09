"""Plot saved C++ output only. No publication images or observational inputs."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'tmp'/'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def read(name):
    return np.genfromtxt(ROOT/'data'/name,delimiter=',',names=True)
p=read('picks.csv'); c=read('convergence.csv'); r=read('residuals.csv'); s=read('sensitivity.csv')
fig,axes=plt.subplots(2,2,figsize=(9,7))
a,b,d,e=axes.flat
a.scatter(p['x_m']/1000,p['y_m']/1000,marker='^',label='Synthetic stations')
a.scatter(c['x_m'][-1]/1000,c['y_m'][-1]/1000,marker='*',s=110,label='Estimated epicenter')
a.set(xlabel='x (km)',ylabel='y (km)',title='V1a: Synthetic geometry',aspect='equal'); a.legend(fontsize=8)
b.loglog(c['grid_m'],c['location_error_m'],'o-'); b.invert_xaxis()
b.set(xlabel='Grid spacing (m)',ylabel='Location error (m)',title='V1b: Refinement consistency')
d.plot(r['station'],r['residual_s']*1e6,'o-')
d.set(xlabel='Synthetic station index',ylabel='Arrival residual (microseconds)',title='V1c: Exact-data fit')
e.plot(s['velocity_ratio'],s['location_error_m'],'o-')
e.set(xlabel='Assumed / generating velocity',ylabel='Location error (m)',title='V1d: Velocity sensitivity')
for ax in axes.flat: ax.grid(alpha=.25)
fig.suptitle('Independent validation only — no Tan et al. panel reproduced',fontsize=12)
fig.tight_layout(rect=[0,0,1,.95])
fig.savefig(ROOT/'figures'/'validation.pdf',metadata={'CreationDate':None})
fig.savefig(ROOT/'figures'/'validation.png',dpi=160)

# Build report tables directly from saved numerical output.
import csv
with (ROOT/'data'/'checks.csv').open() as f:
    checks=list(csv.DictReader(f))
lines=[r'\begin{tabular}{lrrl}',r'\toprule Check & Error & Tolerance & Pass \\',r'\midrule']
for row in checks:
    label=row['check'].replace('_',r'\_')
    lines.append(label+' & '+format(float(row['value']),'.3g')+' & '+format(float(row['tolerance']),'.3g')+' & '+('yes' if row['pass']=='1' else 'NO')+r' \\')
lines += [r'\bottomrule',r'\end{tabular}']
(ROOT/'report'/'validation_table.tex').write_text('\n'.join(lines)+'\n')
lines=[r'\begin{tabular}{rrrr}',r'\toprule Velocity ratio & Position error (m) & Depth (m) & RMS (s) \\',r'\midrule']
for row in s:
    lines.append(' & '.join(format(float(row[n]),'.5g') for n in s.dtype.names)+r' \\')
lines += [r'\bottomrule',r'\end{tabular}']
(ROOT/'report'/'sensitivity_table.tex').write_text('\n'.join(lines)+'\n')
