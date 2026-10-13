"""Save original-observation windows for a limited hybrid-candidate review.

Selection by independent correlation and SNR is recorded. Six examples do not
replace review of all candidates, or confirm cluster membership automatically.
"""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parents[1];os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
D=ROOT/'data/continuation'


def main():
    metrics=pd.read_csv(D/'hybrid_candidate_metrics.csv')
    selected=pd.concat([metrics.nlargest(4,'correlation'),metrics.nlargest(2,'power_SNR_dB')]).drop_duplicates('candidate')
    rows=[];arrays={};errors=[]
    for r in selected.itertuples():
        t=UTCDateTime(r.time)
        for station,source in [('CAAM',r.caam_file),('COLB',r.colb_file)]:
            try:
                st=read(str(ROOT/source),starttime=t-20,endtime=t+24).merge(method=0).split()
                st.detrend('demean');st.remove_response(inventory=read_inventory(str(ROOT/f'inputs/extended/responses/IV_{station}.xml')),output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                for component in ['Z','E','N']:
                    traces=st.select(component=component).copy()
                    if len(traces)!=1:raise ValueError('Missing gap-free component')
                    raw=traces[0].copy().trim(t-4,t+12-.01)
                    traces.filter('bandpass',freqmin=.2,freqmax=6,corners=4)
                    trace=traces[0].trim(t-4,t+12-.01)
                    if len(trace)!=1600 or len(raw)!=1600:raise ValueError('Incomplete waveform')
                    key=f'c{r.candidate}_{station}_{component}'
                    arrays[key]=np.vstack([trace.times(reftime=t),trace.data,raw.data])
                    rows.append(dict(candidate=r.candidate,time=r.time,station=station,component=component,key=key,source=source,correlation=r.correlation,FI=r.FI,power_SNR_dB=r.power_SNR_dB))
            except Exception as exc:errors.append(dict(candidate=int(r.candidate),station=station,error=repr(exc)))
    np.savez_compressed(D/'hybrid_review_windows.npz',**arrays)
    pd.DataFrame(rows).to_csv(D/'hybrid_review_windows.csv',index=False)
    selected.to_csv(D/'hybrid_review_selection.csv',index=False)
    saved=np.load(D/'hybrid_review_windows.npz');index=pd.read_csv(D/'hybrid_review_windows.csv')
    with PdfPages(ROOT/'figures/hybrid_review_diagnostic.pdf') as pdf:
        for candidate,g in index.groupby('candidate'):
            fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True)
            for ax,component in zip(axes,['Z','E','N']):
                for r in g[g.component==component].itertuples():
                    t,filtered,raw=saved[r.key]
                    ax.plot(t,filtered*1e6,label=r.station,lw=.8)
                ax.axvspan(0,8,color='.85',alpha=.5);ax.set_ylabel(component+' velocity (µm/s)');ax.legend(fontsize=8)
            r=g.iloc[0];axes[-1].set_xlabel('Seconds from correlation alignment; 0.2–6 Hz display')
            fig.suptitle(f'Hybrid review diagnostic: candidate {candidate}, {r.time}\nCC={r.correlation:.3f}; CAAM FI={r.FI:.2f}; SNR={r.power_SNR_dB:.2f} dB; not confirmed',fontsize=11)
            fig.tight_layout();pdf.savefig(fig);plt.close(fig)
    summary=dict(selected_candidates=len(selected),saved_component_windows=len(rows),failures=errors,
        selection='Highest four independent mean correlations plus highest two CAAM power SNRs, unique candidates; diagnostic selection, not a random sample.',
        automatic_confirmations=0,manual_labels_generated=False,limitations='A spectral score or correlation crossing is not an event classification. Full onset/coda review and three-year exposure remain incomplete.')
    (D/'hybrid_review_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)


if __name__=='__main__':main()
