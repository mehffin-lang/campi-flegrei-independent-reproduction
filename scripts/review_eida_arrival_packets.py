"""Display the saved packets affected by the new downstream AI arrival picks."""
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_eida'
f=pd.read_csv(D/'measurements.csv');a=np.load(D/'review_waveforms.npz')
g=f[f.pick_basis.fillna('').str.startswith('AI') & f.event_id.ne(649)]
for page in range((len(g)+3)//4):
    fig,axes=plt.subplots(4,2,figsize=(12,9),layout='constrained')
    for row,(left,right) in zip(g.iloc[page*4:(page+1)*4].itertuples(),axes):
        for suffix,c in [('_raw','gray'),('_z','black')]:
            t,y=a[row.key+suffix];scale=max(abs(y[(t>=-.15)&(t<=.2)]).max(),1e-30);left.plot(t,y/scale,color=c,lw=.7)
        left.axvline(0,color='red',lw=.6);left.set(xlim=(-.3,.4),ylim=(-1.5,1.5),title=f'{row.event_id} {row.station} {row.p_time}',xlabel='Seconds from approximate AI P')
        if row.key+'_three' in a:
            q=a[row.key+'_three'];scale=max(abs(q[1:]).max(),1e-30)
            for i,c in enumerate(['black','blue','green']):right.plot(q[0],q[i+1]/scale+i,c=c,lw=.6)
            right.axvline(0,color='red',lw=.6);right.axvline(row.s_minus_p_s,color='orange',lw=.6);right.set(xlim=(-1,row.s_minus_p_s+1),xlabel='Seconds from P; orange = own S')
        else:right.text(.1,.5,row.sp_reason);right.axis('off')
    fig.suptitle('Original observational packets; AI review only, not a paper figure')
    fig.savefig(D/f'review/new_arrival_packets_{page+1}.png',dpi=140);plt.close(fig)
