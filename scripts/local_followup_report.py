"""Integrate executed local processing and mechanism trials into the documents.

Reads saved numerical products; never estimates results or runs a solver.
Earlier cohorts remain available with their own event identifiers.
"""
from pathlib import Path
import hashlib,json,re,zipfile
import pandas as pd
import grid_report as gr

ROOT=gr.ROOT;R=ROOT/'report';D=ROOT/'data/local_extension';B=D/'calibration/merged4';M=ROOT/'data/mechanism_followup'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def paragraph(text,start,replacement):
    # Source paragraphs occupy one line; never consume following figure inputs.
    return re.sub(re.escape(start)+r'[^\n]*',lambda _:replacement,text,count=1)

def main():
    a=read(D/'analysis_summary.json');u=read(B/'uncertainty/summary.json');s=read(B/'summary.json');v=read(B/'validation.json')
    m=read(B/'magnitude/downstream_summary.json') if (B/'magnitude/downstream_summary.json').exists() else read(B/'magnitude/summary.json')
    ms=read(B/'magnitude/magnitude_statistics.json');ps=read(B/'panels/summary.json');lc=read(B/'location_checks/summary.json')
    f=read(M/'skhash_summary.json');mv=read(M/'validation.json');c=pd.read_csv(M/'candidate_requirements.csv')
    e=pd.read_csv(B/'panels/relocated.csv');count=len(e);depth=(e.depth_km.min(),e.depth_km.max())
    assert len(c)==8 and f['computed_solutions']==0 and mv['events']==7
    execution=read(D/'execution.json');assert len(execution['runs'])==9 and all(r['returncode']==0 for r in execution['runs'])
    layout=read(R/'figure_layout.json');rows=read(ROOT/'docs/panel_record.json');byid={r['panel']:r for r in rows}
    saved={
      '2':['panels/weekly_counts.csv','panels/relocated.csv'], '3':['panels/relocated.csv'],
      'S6':['panels/velest.csv'], 'S7':['uncertainty/regional_svd.csv','panels/relocated.csv'],
      'S8':['magnitude/figure_S8A.csv','magnitude/figure_S8B.csv'],
      'S10':['panels/relocated.csv'], 'S11':['panels/swarm-2.csv'],
      'S12':['panels/sectors.csv','panels/cpoz_index.csv','panels/cpoz_gathers.npz'],
      'S13':['panels/relocated.csv']}
    captions={
      '2':'Weekly counts and depths from the latest 123-event relocated trial. Weeks without observations are not connected as measured zero rates. Routine counts are separately labeled context; geographic masks are explicit alternatives.',
      '3':f'{count} independently relocated trial events, {depth[0]:.3f}--{depth[1]:.3f} km below sea level. Own provisional magnitudes set point areas where available; crosses indicate missing magnitudes. Five depths above 5 km retain magenta over-range colors. This subset does not establish a ring fault or its depth limits.',
      'S6':f'{s["paper_filter_passing"]} independently fitted VELEST events pass numerical pick/RMS/gap filters. Full precision paths differ by 0.89 km in depth; regional starts differ by 1.04 km. Physical ordering and small final changes do not establish a stable physical solution.',
      'S7':f'{u["svd_events"]} conditional HypoDD SVD estimates from every supported connected component in four alternative geographic quadrants. The largest reported vertical 2-sigma error is 1.337 km. These errors exclude model, phase-identification and coverage bias. Zero correlation counts are omitted only from logarithmic count axes.',
      'S8':f'{ms["magnitudes"]} own provisional magnitudes; {ms["matched_Md"]} duration-magnitude matches in A. {m["amplitude_measurements"]} channel measurements, {m["snr_passing"]} above 5 dB, {m["magnitude_edges"]} amplitude equations. Conditional Mc=0.0 and b={ms["b"]:.3f} +/- {ms["b_sigma"]:.3f}, N={ms["events_ge_Mc"]}. Routine Md supplies calibration, not validation; discontinuous acquisition prevents population-completeness inference.',
      'S10':'Own relocated calendar-year subsets: 55 in 2022, one each in 2023 and 2024, 66 in 2025. These counts reflect sparse acquisition and filtering, not annual seismicity rates.',
      'S11':'Written calendar windows, inclusive end days. Only swarm 2 contains one retained independent event; the other windows have no qualifying result. Empty selections are not evidence that earthquakes did not occur.',
      'S12':f'{ps["cpoz_traces"]} original CPOZ component traces from {ps["cpoz_events"]} events, aligned on own P picks and filtered above 4 Hz. Geographic sector masks are explicit alternatives. Individual amplitudes are normalized; missing traces are not interpolated. Manual onset/depth validation remains incomplete.',
      'S13':'Latest own provisional relocated coordinates in whole-caldera and central views. An independent coarse coastline replaces the unimplemented satellite layer. No published pixels enter the maps.'}
    common=' Sparse observations, unreviewed phases and unresolved calibration sensitivity; partial numerical counterpart, not accepted structural reproduction.'
    for item in layout:
        group=item['figure']
        if group in saved:
            item['independent_files']=[f'figures/figure_{group}_local_followup.pdf']
            item['file_labels']=[group+'; latest provisional numerical counterpart']
            item['caption']=captions[group]+common;item['comparison_caption']=captions[group]
            for panel in item['panels']:
                row=byid[panel];row['data_command']='.venv/bin/python scripts/calibrate_local_followup.py'
                row['plot_command']='.venv/bin/python scripts/plot_local_followup.py'
                names=saved[group]
                if group=='S11':names=['panels/'+panel.split('/')[-1]+'.csv']
                row['saved_data']='; '.join(str((B/n).relative_to(ROOT)) for n in names)
                row['input_observation_files']=['data/local_extension/all_observation_inputs.json','data/local_extension/input_jobs.json','data/local_extension/short_window_inputs.json','inputs/continuation/IV_responses.xml','inputs/continuation/2I_responses.xml']
                row['input_role']='Original waveform observations and verified metadata; event-selected short windows separately labeled; own phases, associations, velocities and locations; authorized starting grid. Routine Md only for magnitude calibration.'
                row['generated_figure']=item['independent_files'][0] if panel in item['partial_panels'] else ''
                row['report_figure']=item['independent_files'][0]
                row['style_record']='data/mechanism_followup/plot_inventory.json'
                row['attempt']=captions[group]
                row['agreement']='Not established; numerical generation and scientific acceptance are separate.'
                row['independent_generation']=panel in item['partial_panels']
                if panel in item['partial_panels']:row['blocker']=common.strip()+' '+({'S13':'Satellite layer missing.','S7':'Original regional masks unspecified.','S8':'Selected-subset statistics only.','S12':'Original regional masks and manual onset validation unavailable.'}.get(group,''))
        elif group=='4':
            item.update(partial_panels=item['panels'][:],independent_files=['figures/figure_4_followup.pdf'],file_labels=['4A--B; unvalidated waveform-inversion trials'],missing='',caption='Seven own gCAP/FK double-couple trial fits, not accepted focal mechanisms. Gray beachballs distinguish them from the published red/blue quality classes. Variance reduction is 3.9--14.8% at 0.2--2 Hz and 2.3--7.1% at 1--5 Hz; orientations change 34--98 degrees. SKHASH returns no solution. A uses the whole-caldera display; B is a central zoom, with depth colors instead of unavailable terrain elevation. Uniform beachball size is a display choice. Background locations and event IDs belong to the frozen 1,023-association cohort, never joined to the new cohort by integer ID.',comparison_caption='Seven independently computed but unaccepted trial fits. Poor waveform fit and 34--98 degree frequency-band sensitivity prevent mechanism interpretation. Gray denotes unvalidated; zero SKHASH solutions. B uses depth rather than unavailable elevation. Frozen candidate cohort.')
            for panel in item['panels']:
                byid[panel].update(status='partially reproduced',independent_generation=True,agreement='Not established; no accepted mechanism.',data_command='.venv/bin/python scripts/mechanism_measurements.py && .venv/bin/python scripts/run_reviewed_skhash.py && .venv/bin/python scripts/run_gcap_followup.py && .venv/bin/python scripts/run_gcap_followup.py --high-band && .venv/bin/python scripts/validate_mechanism_followup.py',plot_command='.venv/bin/python scripts/plot_local_followup.py',saved_data='data/mechanism_followup/gcap/solutions.csv; data/mechanism_followup/gcap_1_5/solutions.csv; data/mechanism_followup/candidate_requirements.csv',generated_figure='figures/figure_4_followup.pdf',report_figure='figures/figure_4_followup.pdf',input_observation_files=['data/mechanism_followup/measurements.csv','data/mechanism_followup/input_provenance.json','config/mechanism_visual_decisions.json','config/mechanism_review_arrivals.csv'],input_role='Original observed waveform windows and responses; AI visual review, no human review; generic method software and own provisional model. FK waveforms are theoretical predictions, never substituted for observations.',parameters='Eight own candidates, 29 accepted AI first motions, 41 AI-reviewed S/P windows; unchanged SKHASH 8-polarity/90-degree/60-degree gates. Seven gCAP/FK fits at fixed own locations, 10-degree grid, two frequency bands; disclosed external-filter port. No Tan solution or pick.',blocker='No accepted mechanism: seven events have fewer than eight reliable first motions; event 649 has 96.57-degree SKHASH gap. gCAP fits are poor and frequency-sensitive; provisional locations/model and approximate windows remain. Event 698 has one reviewed three-component packet.',attempt=item['caption'],style_record='data/mechanism_followup/plot_inventory.json')
        elif group=='S1':
            item.update(independent_files=['figures/coverage_local_followup.pdf'],file_labels=['S1; actual returned intervals'],caption='1,024 waveform files, 30 station names, 8,952.452 union channel-hours. Four station names occur only in short single-channel windows. Orange identifies event-selected observations; neither these windows nor requested-but-unreturned intervals establish continuous coverage. Official response epochs cover 8,952.386 hours; four short intervals lack responses.')
            byid['S1'].update(saved_data='data/local_extension/processed_coverage.csv; data/local_extension/processed_coverage_union.json; data/local_extension/short_window_inputs.json',data_command='.venv/bin/python scripts/process_local_followup.py --frozen --workers 4',plot_command='.venv/bin/python scripts/plot_local_followup.py',generated_figure=item['independent_files'][0],report_figure=item['independent_files'][0],input_observation_files=['data/local_extension/input_jobs.json'],attempt=item['caption'],blocker='Sparse returned intervals, not full study-period/network coverage; four additional names only have event-selected single-channel windows.')
        elif group=='S9':
            for panel in item['panels']:
                byid[panel].update(saved_data='data/local_extension/calibration/merged4/panels/best_located.csv',data_command='.venv/bin/python scripts/calibrate_local_followup.py',attempt='The >100 correlated-phase selection returned zero qualifying events in the latest own 123-event trial.',independent_generation=False)
        if group in set(saved)|{'4','S1','S9'}:
            for panel in item['panels']:
                row=byid[panel]
                if 'additional_independent_results' in row:row['historical_independent_results']=row.pop('additional_independent_results')
                for name in ['input_files','inputs','output_files','output','related_saved_data','related_data_command']:
                    if name in row:
                        row.setdefault('historical_evidence',{}).setdefault(name,row[name])
                        row.pop(name)
                row['input_files']=[n.strip() for n in row['saved_data'].split(';')]
                row['output_files']=item['independent_files'] if panel in item['partial_panels'] else []
                row['independent_data_generation']=row.get('independent_generation',panel in item['partial_panels'])
                row['agreement_with_publication']='Not quantitatively established; subset/method differences and scientific validation limits remain.'
                row['parameters']=item['caption']
                row['provenance']='Current continuation inputs and own processing; see data/local_extension/all_observation_inputs.json and data/mechanism_followup/input_provenance.json. Earlier numerical sources are historical_evidence, not plotted in the current document.'
    for name in ['panel_record.json','panels.json']:write(ROOT/'docs'/name,rows)
    write(R/'figure_layout.json',layout)
    partial=[r['panel'] for r in rows if r['status']=='partially reproduced'];missing=[r['panel'] for r in rows if r['status']=='not reproduced']
    assert len(rows)==63 and len(partial)==50 and len(missing)==13
    (R/'continuation_panel_summary.tex').write_text(f'{len(partial)} panel/views have partial numerical counterparts and {len(missing)} remain unreproduced. Independent data generation and agreement with the publication are recorded separately.\n')
    table=[r'\begin{longtable}{>{\raggedright\arraybackslash}p{.13\linewidth}>{\raggedright\arraybackslash}p{.28\linewidth}>{\raggedright\arraybackslash}p{.49\linewidth}}',r'\toprule Panel/view & Quantity & Status and remaining limitation\\\midrule\endhead']
    for r in rows:table.append(' & '.join([gr.tex(r['panel']).replace('/',r'/\allowbreak{}'),gr.tex(r['quantity']),gr.tex(r['status']+'. '+r['blocker'])])+r'\\[3pt]')
    table.append(r'\bottomrule\end{longtable}');(R/'panels_table.tex').write_text('\n'.join(table)+'\n')
    chain=[]
    for item in layout:
        if not item['independent_files']:continue
        row=byid[item['partial_panels'][0]]
        chain.append(r'\paragraph{Figure '+item['figure']+r'.} '+gr.tex(', '.join(item['partial_panels']))+r'. Data: \path{'+row['data_command']+r'}. Plot: \path{'+row['plot_command']+r'}.')
        paths=sorted({p.strip() for panel in item['partial_panels'] for p in byid[panel].get('saved_data','').split(';') if p.strip()})
        chain.extend(r'\par\path{'+p+'}' for p in paths)
        chain.append(r'\par Output: \path{'+item['independent_files'][0]+r'}. Upstream input manifests and limitations are in \path{docs/panel_record.json}.')
    (R/'partial_panel_chains.tex').write_text('\n'.join(chain)+'\n')
    narrative=f'The latest independent checkpoint contains {a["picks"]:,} picks and {a["events"]:,} provisional associations from {a["files"]:,} files and {a["processed_channel_hours"]:,.3f} union channel-hours. Of 921 causally usable events, 38 meet the numerical calibration selection; 219 locations survive VELEST filters and 123 survive both TomoDD rounds and the final gap filter. These are independently calculated trials, not accepted physical locations. Calibration retains 0.89 km precision-path and 1.04 km regional-start depth sensitivity. The added observations produced one new association, rejected by residual filtering, and no additional retained relocated event.'
    (R/'grid_narrative.tex').write_text(gr.tex(narrative)+'\n')
    path=R/'report.tex';text=path.read_text().replace('1,023 provisional GaMMA associations from 134,483 picks','1,024 provisional GaMMA associations from 136,376 picks');path.write_text(text)
    path=R/'main_paper.tex';text=path.read_text()
    text=paragraph(text,'Where two counterparts are shown,','Figures 2--3 and the associated supplementary analyses use the latest 1,024-association cohort. Figure 4 retains the frozen 1,023-association candidate identifiers so that waveform review remains traceable. Overlapping cohorts are not additive event counts; no result is joined across them by integer identifier.')
    text=paragraph(text,'Figure 3 shows',f'Figure 3 shows {count} independently relocated trial events. Five lie deeper than 5 km and retain an over-range color. Their sparse distribution does not recover the ring fault or its depth limits. Calibration-path differences reach 0.89 km in depth; conditional SVD vertical errors reach 1.337 km and exclude model bias. Figure 4 now shows seven unaccepted waveform-inversion trials. Variance reduction is only 3.9--14.8\\% in the lower band; changing frequency band rotates the solutions by 34--98 degrees. The polarity inversion returns no mechanism. These results do not establish faulting style.')
    if r'\input{report/figure_sections/F3.tex}' not in text:
        title=r'\section*{Implications for the physical process driving the unrest}'
        text=text.replace(title,r'\input{report/figure_sections/F3.tex}'+'\n'+r'\input{report/figure_sections/F4.tex}'+'\n\n'+title)
    path.write_text(text)
    path=R/'reproduced_supplement.tex';text=path.read_text()
    text=text.replace('132,733 merged picks (19,530 P and 113,203 S)','136,376 merged picks (20,022 P and 116,354 S)').replace('7,351 picks into 1,015','7,416 picks into 1,024').replace('65 provisional magnitudes','67 provisional magnitudes').replace('118 P-aligned','122 P-aligned')
    text=paragraph(text,r'\paragraph{Focal mechanism estimation.}',r'\paragraph{Focal mechanism estimation.} AI visual inspection of 180 station-event records produced 29 usable first motions and 41 usable S/P measurements across eight own candidates; no human manual review is claimed. SKHASH returns no solutions under unchanged quality gates. Generic FK and a disclosed gCAP port return seven provisional double-couple fits in each of two frequency bands. Their poor waveform fits and large orientation changes prevent acceptance. Figure 4 shows these numerical trials with an explicit unvalidated label; the post-supplement record lists every candidate and rejection.')
    path.write_text(text)
    # Earlier numerical sections remain for audit, clearly labeled as earlier cohorts.
    for name,title in [('coverage_extension.tex','Historical 1,023-association checkpoint'),('grid_calibration.tex','Historical 1,015-association grid trial'),('provisional_validation.tex','Historical validation of the 1,015-association trial')]:
        path=R/name;text=path.read_text();text=re.sub(r'\\section\{[^}]+\}',lambda _:r'\section{'+title+'}',text,count=1)
        text=text.replace('The latest separately frozen extension','This earlier separately frozen extension')
        marker=r'\noindent\textit{Historical checkpoint: current processing and mechanism results are reported in the local-file continuation above. Event identifiers and counts in this section refer to the earlier cohort.}\par'
        if marker not in text:text=text.replace('\n','\n'+marker+'\n',1)
        path.write_text(text)
    path=R/'reproduction_documentation.tex';text=path.read_text()
    if r'\input{report/local_followup.tex}' not in text:text=text.replace(r'\section{Scientific specification',r'\input{report/local_followup.tex}'+'\n\n'+r'\section{Scientific specification',1)
    text=text.replace('The examples are access/format checks, not detections or continuous exposure.','The original access checks have now entered the explicitly labeled local-window picking pass. They are event-selected observations, not continuous exposure.')
    text=text.replace('Their waveform/spectral analysis is separate; their picks never seed the independently detected catalog.','These event-selected original windows now also enter the separately labeled local picking pass; their selection cannot establish unbiased continuous discovery. No author-derived pick or event solution is used.')
    text=text.replace('The current collector queries','The collector queries')
    text=paragraph(text,'The accepted regional calibrated and TomoDD-relocated catalog,','Accepted calibrated locations, reliable multiyear magnitudes/completeness, human-reviewed polarities and S/P ratios, accepted SKHASH/gCAP mechanisms, exact original regional masks, manual deep-event validation and three-year hybrid clustering remain incomplete. This continuation generated FK Green functions and provisional gCAP fits; these stages are no longer described as unrun. The per-candidate table and frequency-band validation explain why no mechanism is accepted. Training labels/splits and some inversion settings remain incompletely specified. Author-derived results are not substituted for these missing or unaccepted analyses.')
    path.write_text(text)
    lines=[r'\begin{center}\small\begin{tabular}{rrrrrr}\toprule Event & P signs & S/P & VR low (\%) & VR high (\%) & Rotation ($^\circ$)\\\midrule']
    bands=pd.read_csv(M/'gcap_band_sensitivity.csv').set_index('event_id')
    for row in c.itertuples():
        if row.event_id in bands.index:
            b=bands.loc[row.event_id];vals=[f'{b.low_band_VR_percent:.1f}',f'{b.high_band_VR_percent:.1f}',f'{b.double_couple_rotation_deg:.1f}']
        else:vals=['---']*3
        lines.append(' & '.join(map(str,[row.event_id,row.accepted_ai_polarities,row.accepted_ai_sp]+vals))+r'\\')
    lines.append(r'\bottomrule\end{tabular}\end{center}')
    report=rf'''\section{{Local-file continuation and mechanism measurements}}
This continuation supersedes the current scientific figures for 2--4, S1, S6--S8 and S10--S13. Previous data and plots remain in their labeled cohort directories. No earlier event identifier is silently reused in the new cohort. All new empirical points come from observed waveforms and this implementation's saved calculations; theoretical FK Green functions are predictions, not observations. Published images occur only in the separate comparison PDF.

\paragraph{{Inputs and actual processing.}}
Fourteen previously omitted files were processed: six original CAAM/COLB template windows, seven short local-archive records, and the original CSOB benchmark window. These event-selected observations do not measure continuous discovery exposure. Twenty previously unattempted public requests were issued: 19 returned readable files and one CPIS interval returned HTTP 204; zero failed and no previously attempted interval was retried. All 33 files entered PhaseNet. Compatible older per-file inference and day-association results were reused only after observation, model and settings checks. Raw observation hashes, short-window classifications and processing receipts are in \path{{data/local_extension}}.

The new checkpoint has {a['files']:,} files, 30 station names, 87 channels and {a['processed_channel_hours']:,.3f} union channel-hours, an increase of 245.482 hours. Four added names occur only in short single-channel records. Response epochs cover 8,952.386 hours; four short intervals totaling 0.0667 hours lack valid responses. Ten picks at CROS, V0102 and V0105 lack verified association metadata and remain in \path{{picks_without_metadata.csv}}. The independent selection contains {a['picks']:,} picks, {a['assigned_picks']:,} associated picks and {a['events']:,} provisional events. Requests with no returned observations are not exposure. The frozen queue has 842 downloads, 36 empty responses, 11 failures and 73,917 pending requests. Full study-period coverage remains unfinished. The alternative Tramelli (2021) association profile is retained and explicitly prevents an exact starting-model claim.

\paragraph{{Calibration and relocation outcomes.}}
All nine requested calibration/downstream stages exited successfully; scientific acceptance is false. The new 921-event causal input supplies 38 numerical calibration candidates, 219 VELEST filter passes and 123 final relocated gap passes. Two fixed-grid TomoDD rounds, 80 conditional SVD estimates, 67 provisional amplitude magnitudes and 122 CPOZ component gathers were recomputed for this cohort. On 398 shared waveform differential observations, residual RMS decreases from 0.04125 to 0.03940 s; on 4,367 shared picked differences, from 0.10738 to 0.10130 s. The maximum between-round shift is 386 m horizontally and 0.372 km vertically. Thirty-four retained events have no cross-correlation link and none has more than 100. S9 therefore still has no qualifying result.

Full 32/64-bit calibration paths differ by 558 m horizontally, 0.89 km in depth, 0.32 km/s in velocity and 0.25 s in station delay. Identical converged starts give identical printed coordinates and velocities; this does not remove accumulated nonlinear sensitivity. Regional-start depth differences reach 1.04 km. Earlier instrumentation and failed held-out validation are retained as historical evidence, not asserted to have been rerun for this extension. The new association at 29 January 2022 06:26:03.080 UTC has one P and five S picks. Its reported VELEST RMS increases 0.44, 0.45, 0.46 s in the first three passes; residual rejection leaves too few picks, so it does not survive. The final 123 origins match the prior cohort, with coordinate differences at most 0.001 km vertically. More input did not yield another accepted or retained event.

The relocated-subset magnitude inversion uses {m['amplitude_measurements']:,} measured channels, {m['snr_passing']:,} SNR passes and {m['magnitude_edges']} relative-amplitude equations. Routine duration magnitude is a documented external calibration prior. Conditional $M_c=0.0$ and $b={ms['b']:.3f}\pm{ms['b_sigma']:.3f}$ describe 41 selected magnitudes, not population completeness. There are {lc['pairs']} positive observed S--P pairs, with 0.1777 s RMS against the approximate own model; 42 deep events are flagged for review. These checks do not validate absolute depths.

\paragraph{{Polarity and amplitude review.}}
The frozen eight-event candidate set preserves the requested event 649 identifier. All 180 available station-event records were inspected visually by the AI; none was reviewed by a human seismologist. Responses verify the upward vertical orientation. First motions were read from counts and response-corrected velocity without an additional bandpass. Accepted and rejected judgments, trace references and reasons are saved in \path{{data/mechanism_followup/review_decisions.csv}}. Some initially assigned signs describe later lobes rather than first motions and were corrected. The 13 additional stations for 649 were inspected: CGAU, CLAC, CSOC, CBAG, CCAP, CFMN, CMSN, CMTS, COLB, CPIS, CQUE, CRUS and CUMA. The new AI-reviewed CFMN P arrival is 20 March 2025 06:32:18.910 UTC, with approximately 0.03 s reading uncertainty; it is not an author pick.

S/P is the ratio of peak three-component velocity norms in independently aligned P and S windows, filtered 1--15 Hz. P uses P to min(P+0.30,S-0.10) s, S uses S to S+0.50 s; noise uses P-3 to P-1 s. Both peak/noise-RMS ratios must exceed three. Of 61 automated measurement passes, 41 retain visually usable phase packets; 29 first motions survive AI review. These explicit exploratory windows are not asserted to recover Tan's unpublished per-event choices. Seven events have fewer than eight reliable polarities. Event 649 has eight, but SKHASH's computed azimuthal gap is 96.57 degrees, above the unchanged 90-degree limit. The successful software run returns zero solutions, not a negative finding about faulting style.

\paragraph{{FK and gCAP trials.}}
Official generic FK 3.3 and Zhu's generic gCAP source were inspected and compiled; archive examples, example results and plotting scripts were excluded. Source URLs, archive hashes and extracted member lists are in \path{{data/mechanism_followup/method_resources.json}}. The gCAP distribution requires unavailable Numerical Recipes and SAC filtering functions. A separately named port replaces its three-dimensional curvature eigensolver with a Jacobi calculation and filters complete observations/Green functions externally before fitting. The fixed-matrix eigensolver check differs from NumPy by at most $6.7\times10^{{-8}}$; this is a software test, not an empirical result. External filtering differs from stock segment filtering and limits exact reproduction.

Seven candidates supply at least four reviewed three-component stations; 698 supplies only one. FK generates nine double-couple components per station using the independently fitted four-layer provisional model. Depth is below sea level, with the model surface at $-0.5$ km; source depth is shifted by +0.5 km. Individual receiver topography is not corrected. Density uses the documented FK fallback $\rho=0.77+0.32V_p$ in g/cm$^3$; $Q_S=500$, $Q_P=1000$ are defaults, not measured properties. Verified components rotate to up, outward radial and counterclockwise transverse in cm/s. Horizontal-energy consistency passes.

Both frequency trials use fixed own locations/depths, a 10-degree double-couple grid, 0.1 magnitude increments and a 0.2 s source duration. Pnl windows are P-0.3 to P+1.2 s; surface-wave windows S-0.3 to S+4.7 s, with maximum shifts 0.5 and 1 s, Pnl weight two and distance exponents one and one-half. These are disclosed assumptions. The two bands are 0.2--2 and 1--5 Hz. All seven fits return finite numerical outputs, but variance reduction remains poor and orientations are strongly frequency-dependent. No solution is accepted; no SKHASH--gCAP comparison can be computed without a SKHASH solution. The rotation below compares two own gCAP trials only.

{chr(10).join(lines)}
Event-specific requirements, logs, controls, observed SAC inputs, theoretical Green functions and fitted traces are retained under \path{{data/mechanism_followup}}. For 649, another reliable first motion in the uncovered sector or justified review of current ambiguous onsets is required even to pass the SKHASH gap gate. Additional stations are not automatically usable polarities. For every other candidate the insufficient polarity count is recorded explicitly. Accepted waveform mechanisms further require defensible source locations/model, reviewed windows and stable fits; an optimizer returning angles does not establish these conditions.

\begin{{figure}}[H]\centering
\includegraphics[width=.97\linewidth]{{figures/mechanism_fit_diagnostic.pdf}}
\caption{{Reproduction diagnostic, not a publication figure: event 649 observations and FK/gCAP predictions at four stations. Each pair shares the observed-peak amplitude normalization; the prediction is not normalized separately. Pnl and transverse-S discrepancies explain why the trial beachball is unaccepted.}}
\end{{figure}}

\paragraph{{Rebuild, provenance and replacements.}}
Run \path{{.venv/bin/python scripts/rebuild_local_followup.py}} to validate saved manifests, redraw these panels, integrate their records and compile both documents. The option \path{{--analysis}} reruns the frozen inference/association, calibration/downstream stages and mechanism calculations from retained observations; it does not download a new waveform batch or replace AI review with an automatic claim of human review. Successful commands from this continuation are recorded in \path{{data/local_extension/execution.json}} and mechanism execution logs; old inference caches were hash-checked, not recomputed from scratch. The original waveform inputs remain local with source receipts and hashes. The source and result files superseded in the current documents are listed in \path{{docs/local_followup.md}}; historical numerical cohorts remain unchanged.
'''
    (R/'local_followup.tex').write_text(report)
    result=dict(processing=a,calibration_events=38,velest_filter_passes=219,relocated_events=count,svd_events=u['svd_events'],magnitudes=ms['magnitudes'],mechanism_candidates=8,ai_polarities=29,ai_sp_ratios=41,human_reviews=0,gcap_trials_per_band=7,accepted_mechanisms=0,scientific_acceptance=False,partial_panels=partial,unreproduced_panels=missing)
    write(D/'report_summary.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='processing'},indent=2))

if __name__=='__main__':main()
