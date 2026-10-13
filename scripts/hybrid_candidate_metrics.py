"""Spectral measurements of all own template crossings, not confirmed events.

Eight-second windows follow correlation alignment. This is not manually picked
onset alignment; coda and noise discrimination remain required. No authors'
event list or frequency-index values are read or used as targets.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/continuation'

def main():
    candidates=pd.read_csv(D/'hybrid_candidates.csv');rows=[];errors=[]
    inventories={s:read_inventory(str(ROOT/'inputs/extended/responses'/f'IV_{s}.xml')) for s in ['CAAM','COLB']}
    for file,group in candidates.groupby('caam_file'):
        stream=read(str(ROOT/file)).merge(method=0).split()
        for index,r in group.iterrows():
            t=UTCDateTime(r.time)
            try:
                st=stream.slice(t-12,t+12).copy().select(component='Z')
                if len(st)!=1 or st[0].stats.starttime>t-10 or st[0].stats.endtime<t+8:raise ValueError('Incomplete gap-free CAAM Z window')
                st.detrend('demean');st.remove_response(inventory=inventories['CAAM'],output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                tr=st[0];fs=tr.stats.sampling_rate;n=round(8*fs)
                signal=tr.copy().trim(t,t+8-1/fs).data.astype(float)
                noise=tr.copy().trim(t-8,t-1/fs).data.astype(float)
                assert len(signal)==n and len(noise)==n
                signal-=signal.mean();noise-=noise.mean()
                f=np.fft.rfftfreq(n,1/fs);power=abs(np.fft.rfft(signal))**2
                lo=float(power[(f>=2)&(f<=5)].sum());hi=float(power[(f>=8)&(f<=15)].sum())
                fi=np.log10(hi/lo) if min(lo,hi)>0 else np.nan
                snr=10*np.log10(np.mean(signal**2)/np.mean(noise**2)) if np.mean(noise**2)>0 else np.nan
                rows.append(dict(candidate=index,time=r.time,template=r.template,correlation=r.score,
                                 caam_score=r.caam_score,colb_score=r.colb_score,
                                 FI=float(fi),power_SNR_dB=float(snr),caam_file=file,colb_file=r.colb_file,
                                 alignment='template correlation peak; onset unreviewed',status='unconfirmed threshold crossing'))
            except Exception as e:errors.append(dict(candidate=int(index),file=file,error=repr(e)))
    pd.DataFrame(rows).to_csv(D/'hybrid_candidate_metrics.csv',index=False)
    summary=dict(candidates=len(candidates),measured=len(rows),failures=errors,confirmed_hybrids=0,
                 negative_FI_candidates=sum(r['FI']<0 for r in rows),
                 method='CAAM Z, response-corrected velocity; 8 s at template alignment, FFT band power 8--15 Hz / 2--5 Hz; 8 s preceding noise. No taper or coda rejection, no manual onset review.',
                 limitations='Negative FI and correlation crossings do not establish hybrid events. No confirmed clusters or cluster-relative magnitudes are produced.')
    (D/'hybrid_candidate_metrics.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
