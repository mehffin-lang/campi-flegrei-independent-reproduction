"""Preserve run records and describe executed, unaccepted calibration trials."""
from pathlib import Path
import hashlib,json,zipfile
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/calibration_followup';R=ROOT/'report'
def read(name):return json.loads((D/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    summary=read('summary.json');validation=read('validation.json');reloc=read('relocation/summary.json')
    expanded=read('expanded/analysis_summary.json');coverage=read('expanded/coverage_audit.json');delta=read('acquisition_delta.json');acq=read('acquisition_checkpoint.json')
    expanded_events=pd.read_csv(D/'expanded/initial_events.csv')
    expanded_events.groupby(expanded_events.time.str[:4]).size().rename('events').to_csv(D/'expanded/event_year_counts.csv')
    retrievals={}
    for name in ['docs/rebuild_inputs.json','docs/continuation_rebuild_inputs.json','data/calibration_followup/additional_inputs.json']:
        for item in json.loads((ROOT/name).read_text()):retrievals[item['file']]=item
    processed=[]
    for name in sorted(pd.read_csv(D/'expanded/processed_coverage.csv').file.unique()):
        item=retrievals[name];assert sha(ROOT/name)==item['sha256'],name
        processed.append(dict(file=name,url=item['url'],bytes=(ROOT/name).stat().st_size,sha256=item['sha256'],classification='Original waveform observations'))
    (D/'expanded/processed_input_receipts.json').write_text(json.dumps(processed,indent=2)+'\n')
    strict=read('selection_sensitivity.json');convergence=read('convergence_path.json')
    rows=[]
    for base in [ROOT/'tmp/calibration_followup/velest']+[ROOT/'tmp/calibration_followup'/r['name'] for r in reloc['runs']]:
        rows.extend(p for p in base.rglob('*') if p.is_file())
    # These are this implementation's controls, observations and outputs;
    # generic licensed method source/binaries are not redistributed here.
    with zipfile.ZipFile(D/'run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(rows):
            name=str(p.relative_to(ROOT/'tmp/calibration_followup'));info=zipfile.ZipInfo(name,(2026,10,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
    (D/'run_records.json').write_text(json.dumps(dict(file='data/calibration_followup/run_records.zip',sha256=sha(D/'run_records.zip'),
        role='Own serialized observations, controls, fitted outputs and logs; includes rejected runs, not accepted scientific results',
        members=[dict(file=str(p.relative_to(ROOT/'tmp/calibration_followup')),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(rows)]),indent=2)+'\n')
    numbers={'FollowupFiles':expanded['files'],'FollowupEvents':expanded['events'],'FollowupPicks':expanded['picks'],'FollowupHours':f"{expanded['processed_channel_hours']:.3f}"}
    (R/'followup_numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in numbers.items())+'\n')
    rp=reloc['measurement'];last=convergence[-1];h=summary['heldout']
    calibration=pd.read_csv(D/'calibration_selection.csv')
    counts=calibration.groupby(calibration.time.str[:4]).size()
    year_text=', '.join(str(int(counts.get(str(y),0))) for y in range(2022,2026))
    sonly=int(calibration.num_p_picks.eq(0).sum())
    rr={r['name']:r for r in reloc['runs']}
    region_counts=', '.join(str(rr['svd_'+region]['output_events']) for region in ['NW','SW','SE'])
    region_errors=', '.join(f"{rr['svd_'+region]['max_error_z_m']:.1f}" for region in ['NW','SW','SE'])
    text=rf'''\subsection*{{Calibration and relocation follow-up, 13 October 2026}}
The frozen calibration cohort contains 1,003 provisional associations. Its event identifiers and earlier magnitude, template and frequency-index products are preserved. An additional {delta['successful_requests']} successful six-hour waveform requests supplied {delta['bytes']:,} bytes and {delta['channel_hours']:.3f} channel-hours; {delta['new_no_data']} requests returned HTTP 204. The segmented queue now has {acq['files']} successful requests, {acq['jobs_by_status']['no_data']} no-data responses and {acq['jobs_by_status']['pending']:,} unattempted requests. Pending intervals remain unfinished acquisition, not evidence of remote inaccessibility.

The separate expanded checkpoint processed {expanded['files']} files from {len(expanded['stations'])} station names, with {expanded['processed_channel_hours']:.3f} union channel-hours. It produced {expanded['picks']:,} merged picks ({expanded['p_picks']:,} P and {expanded['s_picks']:,} S), and {expanded['events']:,} provisional associations containing {expanded['assigned_picks']:,} assigned picks. These identifiers are not interchanged with the earlier calibration cohort. Complete epoch intersections identify {coverage['missing_response_channel_hours']:.3f} channel-hours without a usable saved response. This checks metadata availability, not response accuracy or complete three-component detection exposure. Station coverage, every unobserved interval and request status are saved under \path{{data/calibration_followup/expanded}}. No expanded event is yet promoted to an accepted location or substituted into earlier magnitude plots.

\paragraph{{Executed VELEST chain.}}
The written methods identify 373 high-quality calibration events but give no numerical rule that uniquely selects them. The declared causality, more-than-six-pick and gap-below-$180^\circ$ screen selects {summary['calibration_events']} events: {year_text} in 2022--2025. {sonly} have only S picks. This is an unreviewed and temporally unrepresentative alternative selection. The starting layers are Tramelli et al. (2021), Table 1, with the top extended to $-0.5$ km for station elevations. They are not the missing Battaglia regional averages. The reference P delay at {summary['reference_station']} is fixed; initial delays are zero. Two calibration rounds estimate locations/velocities and then also station delays, using seven iterations per round and the preceding explicit damping and S/P weights.

Both arithmetic precisions completed both rounds. The fitted velocity tables agree at their printed precision; maximum location differences are {summary['precision_locations']['max_horizontal_m']:.3f} m horizontally and {1000*summary['precision_locations']['max_depth_km']:.1f} m vertically. Five fixed-model, fixed-correction catalog passes were executed on {summary['whole_catalog_input_events']} causally consistent candidates, including the stated 0.4 s and 0.3 s residual rejection. The final six-pick, 0.25 s and $300^\circ$ filters retain {summary['paper_filter_passing']} exploratory locations. Fixed models/corrections were checked after every pass; absolute own-pick times were preserved to {rp['max_cnv_rounding_s']:.6f} s through serialized origin-time changes.

\paragraph{{Validation rejects acceptance.}}
Another five seven-iteration passes do not converge. The last moves an event by {last['change']['max_horizontal_m']/1000:.3f} km horizontally and {last['change']['max_depth_km']:.2f} km vertically; a fitted depth reaches {last['depth_max_km']:.2f} km. These are unstable trial estimates, not newly established deep earthquakes. With every fifth chronological event held out, unweighted phase RMS worsens from {h['starting']['residual_rms_s']:.3f} to {h['fitted']['residual_rms_s']:.3f} s, although aggregate reported event RMS changes from {h['starting']['event_rms_s']:.3f} to {h['fitted']['event_rms_s']:.3f} s. Recalculation shows that VELEST reports a sample standard deviation of normalized weighted residuals rather than unweighted phase RMS. Maximum discrepancy from the printed values is {validation['maximum_rms_serialization_difference_s']:.6f} s, consistent with output rounding. Thus the mixed validation is not resolved by relabeling both metrics RMS.

One declared sensitivity trial requires at least four P and two S picks and excludes initial depth-bound hits. It leaves {strict['events']} events. Further iterations produce $V_p\leq V_s$; its held-out training branch also fails that physical check. Neither fit is propagated. Reviewed phase identities and well-constrained events are needed before another regional fit can be accepted. The stationary-coordinate approximation differs from sampled channel epochs by up to {validation['max_static_coordinate_offset_m']:.3f} m, already relevant to a claimed ten-meter precision. These checks establish reasons for rejection, not an accepted calibrated catalog.

\begin{{figure}}[H]\centering
\includegraphics[width=.96\linewidth]{{figures/calibration_convergence_diagnostic.pdf}}
\caption{{Reproduction diagnostic, not a publication figure. Saved convergence trials show kilometer-scale location changes despite similar residual statistics. The model and locations are rejected for scientific interpretation.}}
\end{{figure}}

\paragraph{{Observed delays and exploratory HypoDD.}}
The {reloc['events']}-event filtered trial supplies {rp['neighbor_pairs']} nearest-neighbor pairs and {rp['catalog_pair_phases']} catalog differential phases. Original response-corrected waveform measurements supply {rp['measured_channels']:,} channel comparisons, {rp['accepted_channels']} passing channels and {rp['accepted_phase_delays']} coherency-weighted station/phase delays; {rp['window_failures']} window failures are retained. The preceding two-second window, 1--15 Hz band and correlation/coherence thresholds are explicit assumptions, not recovered author configuration. Rejected picks or published event solutions are not used to fill gaps.

Generic HypoDD 2.1 was obtained from Waldhauser's official repository at revision \path{{fb40407}} (full commit in the source receipt). Bounds checks exposed an incorrect output-vector dummy extent in \path{{matmult2.f}}; it was changed from the column count to the row count, with unchanged multiplication equations. An isolated synthetic matrix assertion checks that fix and never enters empirical data. Source hashes, dimensions, compiler flags and the exact change are recorded in \path{{hypodd21_sources.json}} and \path{{hypodd_build.json}} under the follow-up data directory.

Two alternative-profile HypoDD LSQR rounds returned {rr['hypodd_round1']['output_events']} and {rr['hypodd_round2']['output_events']} locations. These are not TomoDD rounds. Six shared phases link clusters; two four-iteration blocks shift weight from catalog to waveform delays, with LSQR damping 50, and a $300^\circ$ gap ceiling. Magnitudes and initial errors set to zero are unused format fields, not measured quantities. LSQR error columns are not interpreted as uncertainties. Quadrants about $14.14^\circ$E, $40.82^\circ$N provide explicit alternative SVD subsets; they do not recreate the paper's four numerical selections. Smaller underconstrained components failed, so only the largest connected component in each quadrant was attempted. NW, SW and SE return {region_counts} estimates; NE diverges and supplies no valid output. The largest conditional 95\% depth errors are {region_errors} m, respectively. These conditional errors and unstable locations cannot establish the publication's spatial precision. No S7 panel is promoted.

\begin{{figure}}[H]\centering
\includegraphics[width=.96\linewidth]{{figures/relocation_uncertainty_diagnostic.pdf}}
\caption{{Reproduction diagnostic, not Figure S7. Conditional SVD errors for three exploratory connected components; the fourth diverged. Zero waveform-difference counts are retained on a symmetric-log abscissa. Error bars cannot validate unreviewed events or the background model.}}
\end{{figure}}

\paragraph{{Provenance and remaining prerequisites.}}
The authorized De Siena et al. (2017) article cites the original Battaglia model and links PANGAEA 875535. Its inspected metadata list derived locations, attenuation products, geochemistry and map material; no numerical original $V_p/V_s$ grid is identified. Those derived products were not downloaded as analysis inputs. The model remains quarantined. Source receipts, URL and hash are recorded; no correspondence was initiated. Exact Cal\`o--Tramelli layer depths and velocities also remain missing, but did not prevent these explicitly alternative trials. TomoDD using the stated fixed 3D background, accepted-location magnitudes, the four specified S7 subsets and their dependent structural panels remain uncompleted. Reviewed phases, stable calibration, verified numerical grid/coordinates/depth convention and regional-averaging masks remain prerequisites. Coverage remains sparse and RAN waveforms credential-gated. Additional observations alone do not resolve the failed calibration.

The complete own-run controls, input serialization, logs and outputs, including failures, are preserved in \path{{data/calibration_followup/run_records.zip}} with member hashes. Code and commands are in \path{{docs/CALIBRATION_FOLLOWUP.md}}. The incremental rebuild executes these trials and reports scientific failures separately from successful software execution; it does not claim a full-period reproduction. Earlier magnitude, focal-mechanism and hybrid statuses are unchanged.
'''
    (R/'calibration_followup.tex').write_text(text)
    print('Saved follow-up report section and own-run archive.')

if __name__=='__main__':main()
