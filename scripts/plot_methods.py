"""Only our saved method-check CSVs are plotted; no authors' assets are read."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def data(name): return np.genfromtxt(str(ROOT/'data'/name),delimiter=',',names=True)
s=data('scaling.csv');f=data('frequency_index.csv');r=data('regularization.csv')
fig,axes=plt.subplots(2,2,figsize=(9,6.8))
a,b,c,d=axes.flat
for ax in axes.flat: ax.grid(alpha=.25)
a.semilogx(s['amplitude_ratio'],s['delta_m'],'o',label='C++');a.semilogx(s['amplitude_ratio'],s['expected_delta_m'],'--',label='Analytic fixture')
a.set(title='M1a: Relative magnitude (S2, S5)',xlabel='Amplitude ratio',ylabel='Magnitude difference');a.legend(fontsize=8)
b.semilogx(s['amplitude_ratio'],s['snr_db'],'o');b.semilogx(s['amplitude_ratio'],s['expected_snr_db'],'--');b.axhline(5,color='gray',ls=':')
b.set(title='M1b: Signal-to-noise ratio (S3)',xlabel='Signal / noise amplitude',ylabel='SNR (dB)')
c.semilogx(f['amplitude_ratio'],f['fi'],'o');c.semilogx(f['amplitude_ratio'],f['expected_fi'],'--')
c.set(title='M1c: Frequency index (S4)',xlabel='10 Hz / 3 Hz amplitude',ylabel='FI')
d.loglog(r['lambda'],r['rmse_magnitude'],'o-')
d.set(title='M1d: Assumed prior sensitivity',xlabel='Regularization weight (assumed)',ylabel='Magnitude RMSE')
fig.suptitle('Method consistency only — no manuscript panel reproduced',fontsize=12)
fig.tight_layout(rect=[0,0,1,.94])
fig.savefig(str(ROOT/'figures/method_checks.pdf'),metadata={'CreationDate':None})
fig.savefig(str(ROOT/'figures/method_checks.png'),dpi=150)
