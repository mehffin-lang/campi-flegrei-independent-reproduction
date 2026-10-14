"""Observed-waveform diagnostics for every negative-mean-FI candidate.

These windows support visual review, not automatic hybrid classifications.
No author event, phase or numerical figure data is read.
"""
from pathlib import Path
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
D=ROOT/os.environ.get('CF_OBSERVATIONS','data/continuation')


def main():
    means=pd.read_csv(D/'catalog_frequency_index_events.csv')
    low=means[means.mean_FI<0]
    measurements=pd.read_csv(D/'catalog_frequency_index.csv')
    quality_path=D/'association_quality.csv'
    if not quality_path.exists():quality_path=D/'calibration/input_quality.csv'
    quality=pd.read_csv(quality_path).rename(columns={'causal':'passes_causality'}).set_index('event_index')
    inventories={n:read_inventory(str(ROOT/f'inputs/continuation/{n}_responses.xml')) for n in ['IV','2I']}
    arrays={};rows=[];failures=[]
    for event in low.itertuples():
        group=measurements[measurements.event_index==event.event_index]
        selected=pd.concat([group.nlargest(2,'power_SNR_dB'),group.nsmallest(1,'FI')]).drop_duplicates('station')
        for r in selected.itertuples():
            try:
                t=UTCDateTime(r.arrival)
                st=read(str(ROOT/r.source),starttime=t-35,endtime=t+31).select(id=r.channel).merge(method=0).split()
                if len(st)!=1 or st[0].stats.starttime>t-20 or st[0].stats.endtime<t+16:
                    raise ValueError('No complete gap-free observed review interval')
                st.detrend('demean');st.remove_response(inventory=inventories[r.station.split('.')[0]],output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                raw=st[0].copy().trim(t-20,t+16)
                filtered=st.copy().filter('bandpass',freqmin=.2,freqmax=6,corners=4)[0].trim(t-20,t+16)
                assert len(raw)==len(filtered)
                key=f'e{event.event_index}_{r.station.replace(".","_")}'
                arrays[key]=np.vstack([raw.times(reftime=t),raw.data,filtered.data])
                other=measurements[(measurements.station==r.station)&(measurements.event_index!=event.event_index)]
                other_times=[float(UTCDateTime(x)-t) for x in other.arrival]
                rows.append(dict(event_index=event.event_index,mean_FI=event.mean_FI,station=r.station,channel=r.channel,
                    source=r.source,source_sha256=hashlib.sha256((ROOT/r.source).read_bytes()).hexdigest(),arrival=r.arrival,
                    alignment=r.alignment,FI=r.FI,power_SNR_dB=r.power_SNR_dB,key=key,
                    passes_causality=bool(quality.loc[event.event_index,'passes_causality']),
                    other_provisional_arrivals_s=[x for x in other_times if -20<=x<=16]))
            except Exception as exc:failures.append(dict(event_index=int(event.event_index),station=r.station,error=repr(exc)))
    np.savez_compressed(D/'catalog_frequency_review.npz',**arrays)
    (D/'catalog_frequency_review_index.json').write_text(json.dumps(rows,indent=2)+'\n')
    # Plot from the saved numerical products, not from a second waveform read.
    saved=np.load(D/'catalog_frequency_review.npz')
    rows=json.loads((D/'catalog_frequency_review_index.json').read_text())
    with PdfPages(ROOT/os.environ.get('CF_FREQUENCY_DIAGNOSTIC','figures/catalog_frequency_review_diagnostic.pdf')) as pdf:
        for event in low.itertuples():
            selected=[r for r in rows if r['event_index']==event.event_index]
            if not selected:continue
            fig,axes=plt.subplots(len(selected),2,figsize=(11,7),sharex=True,squeeze=False)
            for pair,r in zip(axes,selected):
                t,raw,filtered=saved[r['key']]
                for ax,y,label in zip(pair,[raw,filtered],['Response-corrected Z','0.2–6 Hz display']):
                    ax.plot(t,y*1e6,lw=.6,color='black');ax.axvspan(0,8,color='.85',alpha=.5)
                    ax.axvline(0,color='#b2182b',lw=.8)
                    for other in r['other_provisional_arrivals_s']:ax.axvline(other,color='#2166ac',ls=':',lw=.6)
                    ax.set(xlim=(-20,16),ylabel='Velocity (µm/s)',title=f"{r['station']} · {label}")
                pair[0].text(.02,.97,f"FI={r['FI']:.2f}; SNR={r['power_SNR_dB']:.2f} dB\n{r['alignment']}",transform=pair[0].transAxes,va='top',fontsize=8)
            for ax in axes[-1]:ax.set_xlabel('Seconds from own picked/predicted P; gray: FI window')
            fig.suptitle(f'Frequency-index review diagnostic: provisional event {event.event_index}\nMean FI={event.mean_FI:.3f}; causality passes={bool(quality.loc[event.event_index,"passes_causality"])}; blue: other provisional arrivals',fontsize=11)
            fig.tight_layout();pdf.savefig(fig);plt.close(fig)
    summary=dict(negative_mean_FI_candidates=len(low),candidates_with_windows=len({r['event_index'] for r in rows}),
        saved_station_windows=len(rows),failures=failures,confirmed_hybrids=0,
        selection='For each negative-mean-FI provisional event: two highest station SNRs and the lowest station FI, deduplicated. Diagnostic selection, not an accuracy sample.',
        display_method='Z velocity; response removal on up to -35/+31 s context, then -20/+16 s display, with a separate causal four-pole 0.2--6 Hz curve. FI/SNR labels retain the original saved measurements, whose response-removal context was -10/+10 s; no FI is re-estimated from the display.',
        input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'catalog_frequency_index.csv',D/'catalog_frequency_index_events.csv',quality_path]},
        limitations='Predicted/picked alignment is unreviewed. Other provisional arrivals are warnings, not validated coda labels. Plots and negative FI do not establish hybrid events.')
    (D/'catalog_frequency_review.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
