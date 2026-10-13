"""Inspect local candidate records lacking an independent PhaseNet P pick."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy import read,read_inventory,UTCDateTime
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_followup'
def main():
    f=pd.read_csv(D/'measurements.csv');events=pd.read_csv(ROOT/'data/coverage_extension/calibration/merged4/uncertainty/relocated_events.csv').set_index('event_index')
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'))+read_inventory(str(ROOT/'inputs/continuation/2I_responses.xml'))
    arrays={};rows=[]
    for eid,g in f[f.p_time.isna()].groupby('event_id'):
        t=UTCDateTime(events.loc[eid].time);fig,axes=plt.subplots(len(g),1,figsize=(11,1.05*len(g)),squeeze=False,layout='constrained')
        for r,ax in zip(g.itertuples(),axes[:,0]):
            row=dict(event_id=int(eid),station=r.station,network=r.network,source=r.source,key=r.key,origin_time=str(t))
            try:
                st=read(str(ROOT/r.source),starttime=t-10,endtime=t+15).merge(method=0).split().select(network=r.network,station=r.station,component='Z')
                assert len(st)==1
                tr=st[0];meta=inv.select(network=r.network,station=r.station,channel=tr.stats.channel,time=t)[0][0][0]
                assert abs(meta.dip+90)<1
                tr.detrend('demean').taper(.03);tr.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                tr.filter('bandpass',freqmin=1,freqmax=15,corners=4,zerophase=True)
                tt=tr.times()+float(tr.stats.starttime-t);y=tr.data;noise=np.sqrt(np.mean(y[(tt>=-8)&(tt<=-2)]**2));signal=max(abs(y[(tt>=0)&(tt<=12)]));row.update(peak_noise_ratio=signal/noise,response_verified=True)
                arrays[r.key]=np.vstack([tt,y]);ax.plot(tt,y/max(signal,noise,1e-30),lw=.6,c='black');ax.set(xlim=(-2,12),ylim=(-1.2,1.2),yticks=[],ylabel=r.network+'.'+r.station);ax.text(.99,.80,f'peak/noise={signal/noise:.1f}',transform=ax.transAxes,ha='right',fontsize=8);ax.axvline(0,c='red',lw=.5)
            except Exception as exc:row['error']=repr(exc);ax.text(.1,.5,str(exc))
            rows.append(row)
        axes[-1,0].set_xlabel('Seconds from own provisional origin; 1–15 Hz Z velocity');fig.suptitle(f'Event {eid}: stations without independent P; review diagnostic')
        fig.savefig(D/f'review/unpicked_{eid}.png',dpi=120);plt.close(fig)
    pd.DataFrame(rows).to_csv(D/'unpicked_inspection.csv',index=False);np.savez_compressed(D/'unpicked_waveforms.npz',**arrays)
if __name__=='__main__':main()
