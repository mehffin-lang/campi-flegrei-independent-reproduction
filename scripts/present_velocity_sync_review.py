"""Summarize frozen fits; no observation changes, fitting or model selection."""
import os
os.environ['VELOCITY_REVIEW_VERSION']='sync_training_review_20261015'
import json
import numpy as np
import pandas as pd
from extend_velocity_training import R,D,sha,dump

def main():
    F=D/'fits';s=json.loads((F/'validation_summary.json').read_text());plan=json.loads((F/'plan.json').read_text())
    assert plan['gates']==json.loads((R/'data/velocity_holdout_review/experiment_plan.json').read_text())['gates']
    for manifest in [D/'prior_hashes.json',F/'training_frozen.json']:
        for path,h in json.loads(manifest.read_text()).items():assert sha(R/path)==h,path
    lock=json.loads((D/'holdout_lock.json').read_text());assert sha(R/lock['file'])==lock['sha256']
    rows=[];sens=[];rays=[];delays=[];phase=[];depth=[]
    aliases=pd.read_csv(R/'data/velocity_holdout_review/station_aliases.csv').set_index('alias').id
    for name,r in s['runs'].items():
        assert r['finished'],name
        tr=pd.read_csv(F/(name+'_training_residuals.csv'))
        rows.append(dict(trial=name,family=r['family'],variant=r['variant'],events=r['training_events'],arrivals=len(tr),train_initial_rms_s=r['runs'][0]['residual_rms_s'],train_fitted_rms_s=r['runs'][-1]['residual_rms_s'],holdout_initial_rms_s=r['holdout']['initialization']['residual_rms_s'],holdout_fitted_rms_s=r['holdout']['fitted']['residual_rms_s'],physical=r['positive_bulk_modulus'] and r['monotonic'],iteration_gate=r['last_change_gate'],holdout_improves=r['holdout_improves'],holdout_location_converged=r['holdout_location_converged'],accepted=r.get('accepted',False)))
        loc=pd.read_csv(F/(name+'_joint5_locations.csv'))
        for event in loc[loc.event_index.eq(100000)].itertuples():depth.append(dict(trial=name,event_index=event.event_index,depth_km=event.depth_km))
        if r['variant']!='base':continue
        tr['station']=tr.alias.map(aliases)
        for (sta,ph),g in tr.groupby(['station','phase']):phase.append(dict(trial=name,station=sta,phase=ph,arrivals=len(g),mean_s=g.residual_s.mean(),rms_s=np.sqrt(np.mean(g.residual_s**2))))
        ray=pd.read_csv(F/(name+'_joint5_rays.csv'))
        for (ph,top),g in ray.groupby(['phase','layer_top_km']):
            rays.append(dict(trial=name,phase=ph,layer_top_km=top,arrivals=len(g),path_arrivals=int(g.ray_length_km.gt(0).sum()),path_km=g.ray_length_km.sum(),strict_deep_arrivals=int(g.deepest_point_km.gt(3).sum()),strict_deep_source_events=g[g.source_depth_km.gt(3)].event_index.nunique(),dec12_strict_deep_arrivals=int((g.event_index.eq(100000)&g.deepest_point_km.gt(3)).sum())))
        for l in (F/(name+'_fitted.sta')).read_text().splitlines()[1:]:
            if l[:4].strip():delays.append(dict(trial=name,station=aliases[l[:4]],P_s=float(l[34:39]),S_s=float(l[41:46])))
    for fam,checks in s['comparisons'].items():
        for name,q in checks.items():sens.append(dict(family=fam,trial=name,**q['locations'],velocity_km_s=q['velocity_km_s'],station_s=q['station_s']))
    df=pd.DataFrame(rows);sg=pd.DataFrame(sens);rf=pd.DataFrame(rays)
    for name,frame in [('experiment_results',df),('sensitivity_results',sg),('ray_coverage',rf),('station_corrections',pd.DataFrame(delays)),('station_phase_residuals',pd.DataFrame(phase)),('dec12_depth_sensitivity',pd.DataFrame(depth))]:frame.to_csv(D/(name+'.csv'),index=False)
    base=df[df.variant.eq('base')].set_index('family');gates=[]
    for fam,r in base.iterrows():
        q=sg[sg.family.eq(fam)];native=s['runs'][fam+'_base'];extra=native['extra_iteration_changes']
        gates.append(dict(family=fam,max_horizontal_m=q.max_horizontal_m.max(),max_depth_km=q.max_depth_km.max(),max_velocity_km_s=q.velocity_km_s.max(),max_station_s=q.station_s.max(),extra_training_horizontal_m=extra['locations']['max_horizontal_m'],extra_training_depth_km=extra['locations']['max_depth_km'],holdout_location_converged=bool(r.holdout_location_converged),accepted=bool(r.accepted)))
    pd.DataFrame(gates).to_csv(D/'acceptance_checks.csv',index=False)
    cov=json.loads((D/'coverage_summary.json').read_text());pick=json.loads((D/'catalog_dec13/summary.json').read_text());changes=json.loads((D/'training_changes.json').read_text())
    verification=dict(accepted=bool(s['accepted']),training_fits=18,training_events=int(base.iloc[0].events),training_arrivals=int(base.iloc[0].arrivals),continuous_files=cov['downloaded_files'],continuous_bytes=cov['downloaded_bytes'],core_channel_hours=pick['input_channel_hours'],picks=pick['picks'],P=pick['P'],S=pick['S'],new_events=pick['events'],prior_files_unchanged=len(json.loads((D/'prior_hashes.json').read_text())),training_frozen_before_validation=True,holdout_sha256=lock['sha256'],holdout_unchanged=True,criteria_unchanged=True,reviewed_uncertain_phases=6,reviewed_uncertain_event=1532,remaining_gaps=['CSOC P','CSOC S','CUMA P','CUMA S'],metadata=json.loads((D/'metadata_qa.json').read_text()),scope='Training-only quality review; no new calibrated model or scientific-panel replacement.')
    dump(D/'verification.json',verification)
    labels={'four_regularized':'Four layers, fitted delays','three_regularized':'Three layers, fitted delays','three_zero_delays':'Three layers, zero delays'}
    table=[]
    for fam,r in base.iterrows():table.append(f'{labels[fam]} & {r.train_initial_rms_s:.4f} $\\to$ {r.train_fitted_rms_s:.4f} & {r.holdout_initial_rms_s:.4f} $\\to$ {r.holdout_fitted_rms_s:.4f} & '+('Pass' if r.accepted else 'Fail')+r' \\')
    maxima=pd.DataFrame(gates).set_index('family');zero=maxima.loc['three_zero_delays'];deep=rf[(rf.trial=='three_zero_delays_base')&(rf.layer_top_km==3)]
    raytext=', '.join(f'{r.strict_deep_arrivals}/{r.arrivals} {r.phase}' for r in deep.itertuples())
    report=r'''\section{Training-arrival review and synchronized figures}
The report and separate comparison use the same 20 generated figure files and
63 panel records: 53 partial and ten unreproduced. The document builder now
records each panel's status, numerical-file hashes, shared figure hash, and PDF
file timestamps in \path{report/document_build.json}. All 19 comparison pages
were visually inspected. Published images remain confined to that comparison;
missing results retain explicit explanations. This synchronization does not
validate the plotted scientific results or promote the failed velocity profiles.

\paragraph{Targeted observations and review.}
Existing target-station files were checked before querying EIDA for
13 December 2024, 00:00--02:00 UTC. All six station requests succeeded, adding
36 core channel-hours and 20,906,496 bytes against a 20,519,430-byte estimate.
The 40 GiB free-space reserve plus 8 GiB processing allowance was preserved.
The broad queue remained stopped. Header epochs, responses, coordinates and
sampling rates agree with existing StationXML; absolute clock accuracy is untested.
The permitted trained PhaseNet weights yield 163 P and 922 S picks, but no
GaMMA association. CUMA has no picks in this window. No new arrival therefore
enters calibration. CGAU P/S, CLAC S, CREM P/S and CRUS P/S still have one
training observation each, from the preceding December 12 event. CSOC P/S
and CUMA P/S remain absent. Available public intervals beyond this bounded
window have not been exhausted or declared inaccessible.

Six inherited training arrivals remain ambiguous in enlarged raw and filtered
windows: CFMN P for event 159, CMSN S for 265, CFMN S for 264, and CSFT P,
CPOZ S and CFMN S for 1055. They are preserved as uncertain and excluded from
the new fit; no times were forced. Network review of event 1532 places several
assigned P markers in an earlier decaying packet, without establishing a distinct
new event. That association is also excluded as uncertain, not declared false.
After the unchanged event screen, 51 events and 816 arrivals remain; event 159
fails after its ambiguous P is removed. The selection sensitivity retains
62 events and 997 arrivals. These are Codex visual reviews, not independent
human seismologist validation. Other inherited arrivals were not all reviewed.

\paragraph{Numerical diagnosis and refit.}
Saved 32/64-bit prelocation runs have identical observation, model, station and
control files. Their first iteration-zero RMS values differ by about
$2\times10^{-6}$ s. The three-layer prelocation then differs by 0.11 km for
event 932 near the 3 km interface; the four-layer path reaches a 0.18 km
difference after its first joint block and 0.65 km later. This is arithmetic
sensitivity amplified along nonlinear paths, rather than a detected input mismatch.
The exact ray-branch cause has not been isolated for these updated cohorts.
An additional native logging defect leaves the aggregate P/S counters
uninitialized. Those variables are used only for printing; input tokens and
per-ray records supply the verified counts. No solver equation or binary was
changed to hide this defect.

All 18 training fits were frozen before evaluating the unchanged 62-event,
1,065-arrival 2025 set. The same three parameterizations and six sensitivity
choices were retained. No 2025 data were repicked, reassociated, reweighted or
used to fit velocities/delays or select a model. The existing evaluation adjusts
held-out origins and locations with velocities and delays fixed; it tests
conditional arrival prediction, not independent known-hypocenter accuracy.
\begin{center}\small\begin{tabular}{lccc}\toprule
Parameterization & Training RMS (s) & 2025 RMS (s) & All gates\\\midrule
'''+ '\n'.join(table)+r'''
\bottomrule\end{tabular}\end{center}
'''
    assert not s['accepted'],'Review accepted outcome before drafting claims'
    report+=r'''No candidate passes every unchanged criterion. The maximum depth changes across
the registered sensitivities are '''+', '.join(f'{maxima.loc[f,"max_depth_km"]:.2f}' for f in base.index)+r''' km in table order.
The zero-delay case changes by '''+f'{zero.max_horizontal_m:.0f} m horizontally and {zero.max_velocity_km_s:.2f} km/s in velocity'+r'''.
Additional training iterations in that case still move locations by '''+f'{zero.extra_training_horizontal_m:.0f} m horizontally and {zero.extra_training_depth_km:.2f} km in depth'+r'''.
Fixed-model held-out locations also fail the unchanged convergence check.
The limits remain 100 m horizontally, 0.1 km in depth, 0.05 km/s in velocity
and 0.02 s in station delay, alongside physical velocities, convergence and
improved holdout RMS. No failed result is promoted into the catalog or figures.

\paragraph{Depth support and what remains needed.}
In the zero-delay base fit, '''+raytext+r''' rays extend strictly below 3 km.
These are model-dependent paths with 0.01 km vertex rounding, not measured depths
or independent proof of deep resolution. The December 12 event spans '''+f'{min(x["depth_km"] for x in depth):.2f}--{max(x["depth_km"] for x in depth):.2f} km'+r''' across the fits.
Independent layerwise travel-time sums agree with serialized residuals to
0.0050--0.0083 s RMS, subject to rounded native coordinates, velocities and times.
This is an arithmetic consistency check, not confirmation of phase identity.
The present observations do not establish a stable profile. Clear pre-2025
CSOC/CUMA arrivals recorded jointly with the established network are still
needed, as are repeat events at the seven singly represented station/phase
combinations. Training associations in coda and events sensitive to layer
interfaces require further scientific review. More independently constrained
deep source--receiver paths are needed to test resolution below 3 km; no exact
number of additional events sufficient for acceptance has been established.
Logs, decisions, fits, residuals and ray tables are in
\path{data/velocity_holdout_review/sync_training_review_20261015/}; commands are in
\path{docs/SYNC_VELOCITY_REVIEW.md}. Earlier runs remain separate checkpoints.
'''
    (R/'report/velocity_sync_review.tex').write_text(report)
    print(base.to_string());print(pd.DataFrame(gates).to_string(index=False));print(json.dumps(verification,indent=2))

if __name__=='__main__':main()
