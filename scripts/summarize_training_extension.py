"""Present frozen targeted-training fits; never change observations or models."""
import json,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from extend_velocity_training import R,D,sha,dump

def main():
    F=D/'fits';s=json.loads((F/'validation_summary.json').read_text());assert len(s['comparisons'])==3
    plan=json.loads((F/'plan.json').read_text());rows=[];sens=[];rays=[];newdepth=[];station=[]
    aliases=pd.read_csv(R/'data/velocity_holdout_review/station_aliases.csv').set_index('alias').id
    for name,r in s['runs'].items():
        tr=pd.read_csv(F/(name+'_training_residuals.csv'))
        rows.append(dict(trial=name,family=r['family'],variant=r['variant'],training_events=r['training_events'],training_arrivals=len(tr),train_initial_rms_s=r['runs'][0]['residual_rms_s'],train_fitted_rms_s=r['runs'][-1]['residual_rms_s'],holdout_initial_rms_s=r['holdout']['initialization']['residual_rms_s'],holdout_fitted_rms_s=r['holdout']['fitted']['residual_rms_s'],physical=r['positive_bulk_modulus'] and r['monotonic'],iteration_gate=r['last_change_gate'],holdout_improves=r['holdout_improves'],holdout_location_converged=r['holdout_location_converged'],accepted=r.get('accepted',False)))
        loc=pd.read_csv(F/(name+'_joint5_locations.csv'));q=loc[loc.event_index>=100000]
        for e in q.itertuples():newdepth.append(dict(trial=name,event_index=e.event_index,depth_km=e.depth_km,rms_s=e.rms_s,latitude=e.latitude,longitude=e.longitude))
        if r['variant']!='base':continue
        tr['station']=tr.alias.map(aliases)
        for (st,ph),g in tr.groupby(['station','phase']):station.append(dict(trial=name,station=st,phase=ph,arrivals=len(g),events=g.event_index.nunique(),mean_residual_s=float(g.residual_s.mean()),rms_s=float(np.sqrt(np.mean(g.residual_s**2)))))
        ray=pd.read_csv(F/(name+'_joint5_rays.csv'))
        for (phase,top),g in ray.groupby(['phase','layer_top_km']):
            rays.append(dict(trial=name,phase=phase,layer_top_km=top,arrivals=len(g),nonzero_layer_path=int(g.ray_length_km.gt(0).sum()),path_length_km=g.ray_length_km.sum(),strictly_below_3km=int(g.deepest_point_km.gt(3).sum()),events_strictly_below_3km=g[g.source_depth_km.gt(3)].event_index.nunique(),new_event_nonzero_paths=int((g.event_index.ge(100000)&g.ray_length_km.gt(0)).sum()),new_event_strictly_below3=int((g.event_index.ge(100000)&g.deepest_point_km.gt(3)).sum())))
    for family,comparisons in s['comparisons'].items():
        for name,q in comparisons.items():sens.append(dict(family=family,trial=name,**q['locations'],velocity_km_s=q['velocity_km_s'],station_s=q['station_s']))
    frame=pd.DataFrame(rows);frame.to_csv(D/'experiment_results.csv',index=False);pd.DataFrame(sens).to_csv(D/'sensitivity_results.csv',index=False);pd.DataFrame(rays).to_csv(D/'ray_coverage_after.csv',index=False);pd.DataFrame(newdepth).to_csv(D/'new_event_depth_sensitivity.csv',index=False);pd.DataFrame(station).to_csv(D/'training_station_phase_residuals.csv',index=False)
    before=json.loads((D/'prior_results_sha256.json').read_text());assert all(sha(R/p)==h for p,h in before.items())
    frozen=json.loads((F/'training_frozen.json').read_text());assert all(sha(R/p)==h for p,h in frozen.items())
    lock=json.loads((D/'holdout_lock.json').read_text());assert sha(R/lock['file'])==lock['sha256']
    oldgate=json.loads((R/'data/velocity_holdout_review/experiment_plan.json').read_text())['gates'];assert plan['gates']==oldgate
    for cap in [5,8]:assert (pd.read_csv(F/f'training_cap{cap}.csv').time<'2025-01-01').all()
    coverage=json.loads((D/'coverage_summary.json').read_text());catalogs=[json.loads((D/tag/'summary.json').read_text()) for tag in ['catalog_dec12','catalog_dec19']]
    base=frame[frame.variant.eq('base')].set_index('family');sg=pd.DataFrame(sens)
    checks=dict(accepted=bool(s['accepted']),all_18_training_fits_finished=all(r['finished'] for r in s['runs'].values()),training_frozen_before_validation=True,training_hashes_unchanged=True,prior_results_unchanged=len(before),holdout_hash_unchanged=True,holdout_sha256=lock['sha256'],acceptance_thresholds_unchanged=True,added_training_events=plan['added_events'],added_arrivals=20,primary_training_events=53,primary_training_arrivals=847,continuous_files=coverage['downloaded_files'],continuous_bytes=coverage['downloaded_bytes'],continuous_core_channel_hours=sum(c.get('coverage_channel_hours',c.get('input_channel_hours',0)) for c in catalogs),new_continuous_picks=sum(c['picks'] for c in catalogs),new_continuous_P=sum(c['P'] for c in catalogs),new_continuous_S=sum(c['S'] for c in catalogs),raw_target_associations=sum(c['events'] for c in catalogs),supplemental_tie_files=7,supplemental_tie_bytes=615936,remaining_unrepresented=['2I.CSOC.P','2I.CSOC.S','IV.CUMA.P','IV.CUMA.S'],depth_range_new_event_km=[min(d['depth_km'] for d in newdepth),max(d['depth_km'] for d in newdepth)],scope='Targeted pre-2025 calibration experiment. Existing catalog and empirical publication panels are not replaced by these unvalidated models. Event-selected tie clips are excluded from continuous exposure.')
    dump(D/'verification.json',checks)
    # Diagnostic, not a publication panel. Saved arrays/tables supply every value.
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
    labels=['4 layers\ndamped delays','3 layers\ndamped delays','3 layers\nzero delays'];x=np.arange(3)
    axs[0].bar(x-.18,base.holdout_initial_rms_s,width=.36,color='.75',label='Initial profile');axs[0].bar(x+.18,base.holdout_fitted_rms_s,width=.36,color='#0072b2',label='Training fit')
    axs[0].set(xticks=x,xticklabels=labels,ylabel='2025 arrival RMS (s)',ylim=(0,max(base.holdout_initial_rms_s.max(),base.holdout_fitted_rms_s.max())*1.2));axs[0].legend(fontsize=8)
    q=sg.groupby('family').max(numeric_only=True).loc[base.index]
    axs[1].bar(x,q.max_depth_km,color='#d55e00');axs[1].axhline(.1,color='black',ls='--',label='Unchanged 0.1 km gate');axs[1].set(xticks=x,xticklabels=labels,ylabel='Maximum depth sensitivity (km)');axs[1].legend(fontsize=8)
    fig.suptitle('Reproduction diagnostic: reviewed training addition; all profiles remain provisional' if not checks['accepted'] else 'Reproduction diagnostic: reviewed training addition')
    fig.savefig(D/'validation_diagnostic.pdf');fig.savefig(D/'validation_diagnostic.png',dpi=150);plt.close(fig)
    table=[]
    for family,r in base.iterrows():
        label={'four_regularized':'Four layers, damped delays','three_regularized':'Three layers, damped delays','three_zero_delays':'Three layers, zero delays'}[family]
        table.append(f'{label} & {r.train_initial_rms_s:.4f} $\\to$ {r.train_fitted_rms_s:.4f} & {r.holdout_initial_rms_s:.4f} $\\to$ {r.holdout_fitted_rms_s:.4f} & '+('Pass' if r.accepted else 'Fail')+r' \\')
    strict=pd.DataFrame(rays);strict=strict[strict.layer_top_km.eq(3)]
    raylines=[]
    for family,g in strict.groupby('trial',sort=False):
        raylines.append(f'{family}: '+', '.join(f'{r.phase} {r.strictly_below_3km}/{r.arrivals}' for r in g.itertuples()))
    report=r'''\section{Targeted pre-2025 training extension}
The earlier models remain unvalidated. This separate experiment targeted CGAU P/S,
CLAC S, CREM P/S, CSOC P/S, CRUS P/S and CUMA P/S without using 2025 observations
for waveform review, association, fitting or model selection. All prior velocity
trial files remain unchanged. The previously examined 62-event, 1,065-arrival
2025 set was hash-locked and evaluated only after all 18 training fits were frozen.
It remains a reused validation set, not a newly collected blind test.

\paragraph{Coverage and arrival review.}
The missing training support principally reflects different station epochs:
the previous qualifying training events end in May 2024, whereas EIDA advertises
these stations from July--November 2024. The six target stations were retrieved
for 12 and 19 December 2024, 00:00--06:00 UTC, after availability checks.
All 12 requests succeeded: 123,535,872 bytes and 216 core channel-hours.
The measured-size estimate was 123,116,584 bytes. The existing 40 GiB free-space
reserve plus 8 GiB processing allowance remained intact; the broad queue was stopped.
An additional seven event-selected station clips (615,936 bytes) provide network
ties, not continuous detection or completeness exposure.
No requested-but-absent duration is counted as coverage.

The continuous batches yield '''+f"{checks['new_continuous_P']:,} P and {checks['new_continuous_S']:,} S picks"+r'''. Their three initial associations are provisional.
Review of raw and filtered traces identifies a December 12 packet that was split
by later coda picks. A clear raw CGAU P onset was measured at 04:34:26.21 UTC
(reading uncertainty approximately 0.03 s); the earlier existing CRUS S pick
at 04:34:27.44 UTC replaces the later 28.31 s coda pick. These are Codex visual
measurements, not human-reviewed ground truth. Ambiguous CUMA and CSOC phases
remain excluded. The reviewed reassociation has 10 P, 10 S and a 156.2-degree
gap, passing the unchanged pre-inversion screen. Its provisional starting depth
changes from 3.28 to 2.84 km after review; neither value establishes true depth.
The December 19 candidate fails P/S causality and the existing event screen.

The training set increases from 52 events/827 arrivals to 53/847; the selection
sensitivity uses 63 events/1,010 arrivals. Seven previously absent target
station/phase pairs gain one observation each. CSOC P/S and CUMA P/S still have
none. A single event does not independently constrain station corrections across
dates and source depths. All inspected new headers match their StationXML epochs,
responses, rates and coordinates; absolute clock accuracy has not been independently verified.
The 827 inherited training arrivals are preserved, not all newly reviewed.
Earlier uncertain picks and coda associations in that set remain a possible
contributor to instability; this extension does not establish their validity.

\paragraph{Frozen-model validation.}
The same three parameterizations and six sensitivity choices were retained:
$\pm5\%$ initial velocities, training selection, tenfold velocity damping,
32/64-bit fitting and additional iterations. P/S weights remain 1/0.5.
Both fitted families and the zero-delay restricted alternative are reported;
none is selected by its 2025 score. Fixed-model evaluation adjusts held-out
origin times and locations, so this is conditional arrival prediction, not
validation against known hypocenters. The acceptance limits remain 100 m
horizontal displacement, 0.1 km depth, 0.05 km/s velocity and 0.02 s station
delay, together with physical velocities, convergence and improved holdout RMS.

\begin{center}\small\begin{tabular}{lccc}\toprule
Parameterization & Training RMS (s) & 2025 RMS (s) & All gates\\\midrule
'''+ '\n'.join(table)+r'''
\bottomrule\end{tabular}\end{center}
None passes every gate. Across the registered sensitivities, maximum depth
changes are 1.18, 1.39 and 1.57 km for the three families in table order.
The zero-delay family's maximum horizontal change is 898 m and velocity
change is 0.27 km/s. Extra training iterations still change locations by
177 m horizontally and 0.15 km in depth. Its 32/64-bit printed results agree,
but that agreement does not resolve starting-profile and event-selection sensitivity.
After the training decisions were frozen, 1,043 of the 1,065 holdout arrivals
have a represented station/phase combination and 22 remain unrepresented.
Both fitted-delay families worsen RMS even on the represented combinations;
the remaining four empty training cells cannot alone explain the failure.
Independent sums of layerwise ray travel times, with station delays, agree with
the serialized residual calculation to 0.0040--0.0057 s RMS, consistent with
rounded native outputs. This checks arithmetic consistency, not phase truth.
\begin{figure}[H]\centering
\includegraphics[width=.96\linewidth]{data/velocity_holdout_review/training_extension_20261015/validation_diagnostic.pdf}
\caption{Reproduction diagnostic, not a manuscript panel. Conditional arrival RMS
and maximum depth changes across the registered starting-profile, selection,
damping and arithmetic tests. Saved fits supply all plotted values.}
\end{figure}

\paragraph{Depth coverage and remaining limitation.}
The preserved three-layer zero-delay fit had 80/366 P and 115/461 S paths
in the layer beginning at 3 km. That count includes interface paths: only
48 P and 76 S rays, from nine source events, extended strictly below 3 km.
The numerical ray vertices have 0.01 km precision; these are model-dependent
paths, not measured depths. The new event's fitted depth ranges across trials from
'''+f"{checks['depth_range_new_event_km'][0]:.2f} to {checks['depth_range_new_event_km'][1]:.2f} km"+r'''.
The addition therefore does not by itself establish improved deep resolution.
In the new zero-delay base fit, 52/376 P and 83/471 S paths extend strictly
below 3 km, but none of those strict deep paths belongs to the added event.
The count change reflects changes to the estimated geometry of older events.
Detailed layer lengths, depth coverage and per-station residuals are saved beside
the fits. More clear pre-2025 events recorded jointly at the target and established
stations, especially with stable depth constraints, are needed. The CSOC and CUMA
records in these two batches do not supply reliable training arrivals. Additional
public pre-2025 intervals remain available but were not downloaded in this bounded
experiment; this is insufficient reviewed coverage, not a claim of inaccessible data.

\paragraph{Reproducibility and status.}
The versioned record is \path{data/velocity_holdout_review/training_extension_20261015/}.
It contains request receipts, coverage and checksums, reviewed arrivals, numerical
fits, residuals, sensitivity results and ray paths. Commands and input placement are
in \path{docs/TARGETED_VELOCITY_TRAINING.md}. The previous empirical panels and
comparison images retain their original checkpoints; no failed profile is promoted
to a calibrated catalog or relocated result.
'''
    (R/'report/velocity_training_extension.tex').write_text(report)
    print(frame.to_string(index=False));print(json.dumps(checks,indent=2));print('\n'.join(raylines))

if __name__=='__main__':main()
