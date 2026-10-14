"""Two-station observed windows for review of the 36 displayed crossings.

This diagnostic does not label events automatically. The time origin is template
alignment, not a reviewed phase onset. No paper result table is used.
"""
from pathlib import Path
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[1];os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np,pandas as pd
from obspy import read,read_inventory,UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=ROOT/'data/eida_continuation/hybrid'
def main():
    chosen=pd.read_csv(D/'display_candidates.csv');metrics=pd.read_csv(D/'candidate_metrics.csv').set_index('candidate');inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'));arrays={};rows=[];errors=[]
    for r in chosen.itertuples():
        m=metrics.loc[r.candidate];t=UTCDateTime(r.time)
        for sta,field in [('CAAM','caam_file'),('COLB','colb_file')]:
            source=m[field];key=f'c{r.candidate}_{sta}'
            try:
                st=read(str(ROOT/source),starttime=t-25,endtime=t+25).select(component='Z').merge(method=0).split()
                assert len(st)==1 and st[0].stats.starttime<=t-10 and st[0].stats.endtime>=t+16
                st.detrend('demean');st.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                st.filter('bandpass',freqmin=.2,freqmax=6,corners=4);tr=st[0].trim(t-10,t+16)
                arrays[key]=np.vstack([tr.times(reftime=t),tr.data]);rows.append(dict(candidate=int(r.candidate),station=sta,key=key,source=source,sha256=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()))
            except Exception as exc:errors.append(dict(candidate=int(r.candidate),station=sta,error=repr(exc)))
    np.savez_compressed(D/'review_waveforms.npz',**arrays);pd.DataFrame(rows).to_csv(D/'review_windows.csv',index=False)
    dest=ROOT/'tmp/eida_continuation/hybrid_review';dest.mkdir(exist_ok=True)
    for template,g in chosen.groupby('template'):
        g=g.sort_values('cc',ascending=False)
        for page in range((len(g)+3)//4):
            part=g.iloc[page*4:(page+1)*4];fig,axes=plt.subplots(len(part),2,figsize=(12,7),squeeze=False,layout='constrained')
            for (_,r),aa in zip(part.iterrows(),axes):
                m=metrics.loc[r.candidate]
                for ax,sta in zip(aa,['CAAM','COLB']):
                    key=f'c{int(r.candidate)}_{sta}'
                    if key not in arrays:ax.text(.2,.5,'No complete window');continue
                    t,y=arrays[key];ax.plot(t,y*1e6,c='black',lw=.55);ax.axvspan(0,8,color='.9');ax.axvline(0,c='red',lw=.6)
                    ax.set(xlabel='Seconds from template alignment',ylabel='Velocity (µm/s)',title=f'{int(r.candidate)} {sta} {str(r.time)[:19]} · cc={m[sta.lower()+"_score"]:.2f}');ax.set_xlim(-10,16)
                aa[0].text(.02,.96,f'CAAM FI {r.FI:.2f}; SNR {r.power_SNR_dB:.1f} dB',transform=aa[0].transAxes,va='top',fontsize=8)
            fig.suptitle(template+' · Reproduction diagnostic: strongest unconfirmed crossings, 0.2–6 Hz');fig.savefig(dest/f'{template}_{page+1}.png',dpi=120);plt.close(fig)
    (D/'review_window_summary.json').write_text(json.dumps(dict(candidates=len(chosen),station_windows=len(rows),errors=errors,method=__doc__,filter='Response-corrected vertical velocity, causal four-pole 0.2–6 Hz, -10 to +16 s context. FI/SNR retained from saved broadband measurements; gray area is their 8-s signal window.',human_reviews=0,confirmed_hybrids=0),indent=2)+'\n')
    print(len(chosen),'candidates;',len(rows),'station windows;',len(errors),'missing windows')
if __name__=='__main__':main()
