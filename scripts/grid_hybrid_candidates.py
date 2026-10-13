"""Save provisional template-family waveforms and horizontal amplitude ratios.

No candidate is declared a hybrid. These are explicitly partial S14 analyses,
not a substitute for the manual confirmation and cluster assignment in Tan.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/grid_calibration/merged4/hybrid'
def main():
    old=pd.read_csv(ROOT/'data/continuation/hybrid_candidates.csv');new=pd.read_csv(OUT/'hybrid_candidates.csv')
    identical=old.equals(new)
    if identical:
        # Equivalent candidate rows identify the same original windows.
        metrics=pd.read_csv(ROOT/'data/continuation/hybrid_candidate_metrics.csv')
    else:
        import hybrid_candidate_metrics as h
        h.D=OUT;h.main();metrics=pd.read_csv(OUT/'hybrid_candidate_metrics.csv')
    metrics.to_csv(OUT/'candidate_metrics.csv',index=False)
    chosen=metrics.sort_values(['template','correlation'],ascending=[True,False]).groupby('template').head(12)
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'));rows=[];arrays={};errors=[]
    for file,g in chosen.groupby('caam_file'):
        raw=read(str(ROOT/file)).merge(method=0).split()
        for r in g.itertuples():
            try:
                t=UTCDateTime(r.time);st=raw.slice(t-12,t+12).copy();st.detrend('demean');st.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
                peaks=[]
                for c in ['N','E']:
                    comp=st.select(component=c)
                    if len(comp)!=1:raise ValueError('Missing gap-free horizontal component')
                    tr=comp[0].copy().trim(t,t+8-1/comp[0].stats.sampling_rate)
                    if len(tr)!=round(8*tr.stats.sampling_rate):raise ValueError('Incomplete horizontal amplitude window')
                    peaks.append(float(np.max(abs(tr.data))))
                zz=st.select(component='Z').copy()
                if len(zz)!=1:raise ValueError('Missing gap-free vertical component')
                tr=zz[0];tr.filter('bandpass',freqmin=1,freqmax=10,corners=4,zerophase=False);tr.trim(t,t+8-1/tr.stats.sampling_rate)
                if len(tr)!=round(8*tr.stats.sampling_rate):raise ValueError('Incomplete vertical window')
                key='c'+str(r.candidate);arrays[key]=np.vstack([tr.times(),tr.data/np.max(abs(tr.data))]);rows.append(dict(candidate=r.candidate,time=r.time,template=r.template,cc=r.correlation,FI=r.FI,power_SNR_dB=r.power_SNR_dB,peak_horizontal_velocity_m_s=max(peaks),source=file,array_key=key))
            except Exception as exc:errors.append(dict(candidate=r.candidate,error=repr(exc)))
    table=pd.DataFrame(rows)
    # Ratio only within the displayed, unreviewed template family. It is not an
    # accepted relative magnitude: common source/path assumptions are untested.
    table['log10_horizontal_ratio']=np.log10(table.peak_horizontal_velocity_m_s/table.groupby('template').peak_horizontal_velocity_m_s.transform('max'))
    table.to_csv(OUT/'display_candidates.csv',index=False);np.savez_compressed(OUT/'display_waveforms.npz',**arrays)
    summary=dict(all_crossings=len(new),displayed=len(table),errors=errors,confirmed_hybrids=0,confirmed_clusters=0,
        selection='Twelve highest independent two-station correlation scores per template; a display selection only, not confirmation. Each template family includes noise/coda candidates until reviewed.',
        amplitude='Largest absolute sample of CAAM N or E response-corrected velocity in eight seconds; log10 ratio to largest displayed candidate in each template family. No relative magnitude claim because common path and event membership are unvalidated.',
        waveform='CAAM Z, causal four-pole 1–10 Hz, individually normalized for display; eight-second template-aligned window, onset unreviewed.',
        reused_metrics='Previous original-window FI measurements reused only after full row equality.' if identical else 'Crossing list differs; all original-window FI measurements recomputed with hybrid_candidate_metrics.py.',
        limitation='No independent unclustered family or manual hybrid confirmation. Not the published 70-event result or its full-period timing history.')
    (OUT/'display_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
