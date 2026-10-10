"""Save candidate waveforms/FI for review; a threshold crossing is not a hybrid."""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np,pandas as pd
from obspy import read,read_inventory,UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=pd.read_csv('data/extended/hybrid_candidates.csv');metrics=[];wave=[]
for i,r in rows.iterrows():
    t=UTCDateTime(r.time)
    for station,file in [('CAAM',r.caam_file),('COLB',r.colb_file)]:
        st=read(file,starttime=t-20,endtime=t+20);st.detrend('demean')
        inv=read_inventory('inputs/extended/responses/IV_'+station+'.xml')
        st.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
        z=st.select(component='Z')[0];show=z.copy().trim(t-2,t+12)
        for ts,v in zip(show.times()+float(show.stats.starttime-t),show.data):wave.append(dict(candidate=i,station=station,time_s=ts,velocity_m_s=v))
        if station=='CAAM':
            x=z.copy().trim(t,t+7.99).data;x=x-x.mean();assert len(x)==800
            f=np.fft.rfftfreq(800,.01);p=abs(np.fft.rfft(x))**2
            fi=float(np.log10(p[(f>=8)&(f<=15)].sum()/p[(f>=2)&(f<=5)].sum()))
            metrics.append(dict(candidate=i,time=r.time,template=r.template,score=r.score,FI=fi,status='Unconfirmed; candidate needs event and coda discrimination'))
pd.DataFrame(metrics).to_csv('data/extended/hybrid_review_metrics.csv',index=False)
pd.DataFrame(wave).to_csv('data/extended/hybrid_review_waveforms.csv',index=False)
if len(rows):
    data=pd.read_csv('data/extended/hybrid_review_waveforms.csv');fig,axs=plt.subplots(len(rows),1,figsize=(9,2*len(rows)),squeeze=False)
    for i,ax in enumerate(axs[:,0]):
        for station,g in data[data.candidate==i].groupby('station'):
            ax.plot(g.time_s,g.velocity_m_s*1e6,label=station,lw=.6)
        ax.set(title=f"Candidate {i}: {metrics[i]['time']} — FI {metrics[i]['FI']:.2f}",ylabel='Velocity (µm/s)');ax.legend(fontsize=7)
    axs[-1,0].set_xlabel('Time from template alignment (s)');fig.suptitle('Independently detected, unconfirmed candidates — not reproduced hybrid clusters')
    fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig('figures/hybrid_candidate_review.'+ext,dpi=150)
    plt.close(fig)
