"""Update the publication-panel record from actually executed stage outputs."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/continuation';R=ROOT/'report'
def read(name,default=None):
    p=D/(name+'.json');return json.loads(p.read_text()) if p.exists() else (default or {})
def tex(value):
    return ''.join({'\\':r'\textbackslash{}','{':r'\{','}':r'\}','&':r'\&','%':r'\%','_':r'\_','#':r'\#','<':r'$<$','>':r'$>$'}.get(c,c) for c in str(value))
c=read('context_summary');a=read('acquisition_checkpoint',read('acquisition_summary'));s=read('analysis_summary');m=read('downstream_summary');v=read('velest_summary');h=read('hybrid_summary');loc=read('location_consistency');stats=read('magnitude_statistics')
geo=read('station_geometry_summary')
ran_files=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'inputs/revision/ran_stationxml').glob('*.xml'))]+['inputs/revision/RAN_stations.html']
observations=json.loads((ROOT/'data/observations/summary.json').read_text())
template_lines=[r'\begin{longtable}{lrr}\toprule Template & FI & Samples\\\midrule\endhead']
template_lines += [tex(r['template'])+' & '+f"{r['FI']:.4f}"+' & '+str(r['samples'])+r'\\' for r in observations['templates']]
template_lines.append(r'\bottomrule\end{longtable}')
(R/'template_table.tex').write_text('\n'.join(template_lines)+'\n')
rows=json.loads((ROOT/'docs/panel_record.json').read_text())
routine=[f'inputs/continuation/routine_{y}.html' for y in range(2005,2026)]
processed=pd.read_csv(D/'processed_coverage.csv').file.drop_duplicates().sort_values().tolist()
for r in rows:
    p=r['panel']
    if p in ['1A','1C'] or p.startswith('S5'):
        for key in ['comparison_data_command','comparison_plot_command','comparison_figure']:r.pop(key,None)
        r.update(status='partially reproduced',data_command='.venv/bin/python scripts/continue_context.py',plot_command='.venv/bin/python scripts/plot_continuation.py',input_observation_files=routine,
                 generated_figure='figures/figure_S5_routine.pdf' if p.startswith('S5') else f'figures/figure_{p}_routine.pdf',
                 attempt='Executed directly from expressly permitted external routine-catalog records; not independent detections.',
                 blocker='Current catalog snapshot differs from the historical snapshot: 12,503 located study events versus 12,083. No tuning to published counts. Natural Earth coastline is a display substitute; the original relief/inland-zero contour has not been reconstructed.' if p!='1C' else 'Monthly counts and exact-time cumulative Md>0.2 reconstructed from the current routine snapshot; historical count differences unresolved. March 2025 is a partial month.',
                 saved_data='data/continuation/figure_'+('S5' if p.startswith('S5') else p)+'.csv')
    if p=='1B':
        r.update(status='partially reproduced',data_command='.venv/bin/python scripts/continue_context.py',plot_command='.venv/bin/python scripts/plot_continuation.py',
                 input_observation_files=['inputs/extended/delgaudio2010_table.doc','inputs/continuation/RITE_daily.txt','inputs/continuation/RITE_Timeseries_Format.readme','inputs/continuation/RITE_2000_2025.txt','inputs/continuation/Time_Series_Format.txt'],
                 generated_figure='figures/figure_1B_displacement.pdf',saved_data='data/continuation/rite_gnss.csv; data/continuation/historical_leveling.csv',
                 parameters='128 historical entries: 114 leveling surveys, 13 source-provided estimates and one source-provided graphical reconstruction. Source classes preserved separately. Daily GNSS 2000-05-29 through 2025-03-20; median datum from 23 overlapping leveling epochs, +/-15 days. Month-only dates placed on day 15 for display.',
                 attempt='Original text series and format notes verified; 2020--2025 daily coverage is available. Source-reconstructed history is labeled and not described as raw observations. No JPG or digitization by this implementation.',
                 blocker='Benchmark equivalence and datum-joining convention are assumed because the exact original stitching recipe is not specified. Calendar gaps remain unfilled; no missing recent-data blocker through 2025-03-20.')
    if p=='S1':r.update(generated_figure='figures/continuation_coverage.pdf',input_observation_files=processed,data_command='.venv/bin/python scripts/process_continuous.py all --frozen',plot_command='.venv/bin/python scripts/plot_continuation.py',attempt='Executed actual sample-span union for the frozen processed checkpoint; no requested interval is counted as covered.',saved_data='data/continuation/processed_coverage_union.json',blocker=f"{s['files']} files processed, {s['processed_channel_hours']:.3f} union channel-hours. Full-period queue still pending; actual gaps and unavailable RAN credentials remain. Requests/availability are not coverage.")
    if p=='1C':r['saved_data']='data/continuation/figure_1C.csv; data/continuation/figure_1C_cumulative.csv'
    if p=='S15C':r['saved_data']='data/observations/E3_waveforms.csv; data/observations/E3_CAAM_Z_spectrum.npz; data/observations/E3_CAAM_E_spectrum.npz; data/observations/E3_COLB_Z_spectrum.npz; data/observations/E3_COLB_E_spectrum.npz'
    if p in ['S15A','S15B']:
        label='E1' if p=='S15A' else 'E2'
        r.update(generated_figure=None,saved_data=None,data_command=None,plot_command=None,
                 related_data_command='.venv/bin/python scripts/analyze_observations.py',related_plot_command='.venv/bin/python scripts/plot_observations.py',
                 related_diagnostic=f'figures/hybrid_{label}.pdf (different example, not a panel counterpart)',attempt='Related written-method template processed; it is not the published example and is excluded from this panel comparison.')
    if p=='S2':
        r.update(input_observation_files=['inputs/models/stations.csv','inputs/continuation/coastline.zip','inputs/continuation/IV_responses.xml','inputs/continuation/2I_responses.xml']+ran_files,generated_figure='figures/continuation_stations.pdf',saved_data='data/continuation/figure_S2.csv; data/continuation/station_geometry_qa.csv; data/continuation/station_geometry_epochs.csv',data_command='.venv/bin/python scripts/station_geometry.py',plot_command='.venv/bin/python scripts/plot_continuation.py',attempt=f"All 51 candidate identifiers audited: {geo['verified_identifiers']} official coordinate/epoch matches and {len(geo['unresolved_identifiers'])} unresolved. Coastline vertices were masked before local projection. Numbered labels retain network codes and separate verified/unverified metadata.",blocker='The published 48-instrument membership is not verified. Two released-coordinate pairs coincide; no deployment alias mapping justifies collapsing or removing identifiers.')
    if p.startswith('S6'):
        r['status']='not reproduced'
        r.update(generated_figure='',saved_data='',input_observation_files=[],data_command='Not run: provenance/validation prerequisites unresolved',plot_command='Not generated',attempt='Prior S6 output and all dependent velocity/location files quarantined. An alternative-profile precision experiment is a diagnostic, not a panel result.',parameters='Requires verified fixed 2008 grid, documented regional averages and validated independent VELEST inversions.')
        r['blocker']='Fixed 3D grid provenance remains unverified; previous precision-sensitive regional calibration is rejected. The exploratory 2021-profile experiment is not an accepted regional model. No old or author locations substituted.'
    if p.startswith('S8'):
        r['status']='not reproduced'
        r['blocker']=f"{m.get('amplitude_measurements',0)} channel measurements, {m.get('snr_passing',0)} passing SNR, {m.get('magnitude_edges',0)} relative-amplitude equations, {m.get('calibrated_magnitudes',0)} provisional magnitudes. Final relocated locations/full exposure remain missing; routine Md is an allowed regularizer, not independent validation."
        if m.get('calibrated_magnitudes',0)>0:
            r.update(status='partially reproduced',generated_figure='figures/figure_S8_pilot.pdf',saved_data=f'data/continuation/figure_{p}.csv',
                data_command='.venv/bin/python scripts/downstream_checks.py --dataset continuation && .venv/bin/python scripts/magnitude_statistics.py',plot_command='.venv/bin/python scripts/plot_continuation.py',
                input_observation_files=processed+routine+['inputs/continuation/IV_responses.xml','inputs/continuation/2I_responses.xml'],
                parameters='5 s signal, 2 s preceding noise; SNR >=5 dB; all available recorded stations; own picked or predicted P arrivals; >=2 shared stations; separation < one fifth of station distance; squared zero-lag correlation weights; Md regularization lambda=1 for unique one-to-one matches within 2 s. Initial locations. B uses 0.1 magnitude bins, maximum-curvature Mc, half-bin-corrected likelihood b and formal Shi-Bolt sampling error; no arbitrary minimum sample cutoff.',
                attempt='Executed amplitude-ratio inversion on initial locations; partial pilot comparison/distribution only. No claim of full-period completeness or b-value.')
            if p=='S8B':r['saved_data']+='; data/continuation/magnitude_statistics.json'
    if p.startswith('S12'):
        r['blocker']=f"{loc.get('associated_cpoz_p_picks',0)} independently associated CPOZ P arrivals now exist. Relocated ring-sector selection and manual depth review remain unfinished; internal S-P checks do not establish location accuracy."
    if p.startswith('S14'):
        r['blocker']=f"{h.get('valid_hours',0):.3f} common CAAM/COLB scan hours; {h.get('candidates',0)} unconfirmed threshold crossings. Three-year scan, reviewed clusters, relative magnitudes and timing histories remain unfinished."
    if p in ['2A','2B','3/map','3/northing-depth','3/easting-depth']:
        r['blocker']=f"{s['events']} provisional GaMMA events are not a complete calibrated, TomoDD-relocated catalog. Multiyear acquisition and downstream processing remain incomplete."
    if p in ['4A','4B']:
        r['blocker']='Accepted independent locations/model, reviewed P polarities and S/P ratios, Green functions and event-specific gCAP settings are missing or unfinished. SKHASH/gCAP not run. The written methods and figure caption use different counts; no supplied mechanism table is used to resolve this in the scientific report.'
    r['input_observation_files']=sorted(set(r.get('input_observation_files',[])))
    r['report_figure']='figures/figure_1_combined.pdf' if p in ['1A','1B','1C'] else r.get('generated_figure')
(ROOT/'docs/panel_record.json').write_text(json.dumps(rows,indent=2)+'\n');(ROOT/'docs/panels.json').write_text(json.dumps(rows,indent=2)+'\n')
layout=json.loads((R/'figure_layout.json').read_text())
for item in layout:
    if item['figure']=='1':
        item.update(partial_panels=['1A','1B','1C'],file_labels=['1A--C'],independent_files=['figures/figure_1_combined.pdf'],missing='',caption='Partial contextual reconstruction. A: external routine catalog, 16,046 located events and five Md>=4 stars. B: 114 leveling surveys (circles), 13 source-provided estimates (triangles), one source-provided reconstruction (cross), and daily GNSS through 20 March 2025; extension beyond 2023 shaded. Historical estimates are not raw observations or reconstructions made here. C: all routine monthly counts and cumulative Md>0.2; March includes days 1--20 only. Routine events are not independent detections. Datum joining is an assumption; basemap and live snapshot differ from the publication.')
    elif item['figure']=='S5':
        item.update(partial_panels=item['panels'],file_labels=['S5, all views'],independent_files=['figures/figure_S5_routine.pdf'],missing='',caption='External routine-catalog data, independently selected and plotted: 12,503 located events, 21 January 2022--20 March 2025. This is 420 more than the published historical snapshot. No author-derived catalog is used to adjust that difference; these are not independent detections.')
    elif item['figure']=='S1':item.update(independent_files=['figures/continuation_coverage.pdf'],caption=f"Partial: {s['files']} processed files, {len(s['stations'])} station names and {s['processed_channel_hours']:.3f} channel-hours after union of overlapping intervals. Empty intervals are not connected or counted as coverage.")
    elif item['figure']=='S2':item.update(independent_files=['figures/continuation_stations.pdf'],caption=f"Partial station inventory: 51 released identifiers audited against official study-period response epochs. Filled triangles: {geo['verified_identifiers']} official coordinate matches; open triangles: {len(geo['unresolved_identifiers'])} released coordinates with unresolved epochs or channel codes. Two coincident-coordinate pairs remain distinct identifiers. No verified geographic outlier. Local WGS84 projection and clipped coastline; the original 48-instrument membership is not established.")
    elif item['figure']=='S8' and m.get('calibrated_magnitudes',0)>0:
        item.update(partial_panels=item['panels'],file_labels=['S8A--B'],independent_files=['figures/figure_S8_pilot.pdf'],missing='',caption=f"Partial amplitude-ratio pilot: {m['calibrated_magnitudes']} provisional magnitudes from independent observations, with routine Md as the documented calibration prior. A is not an independent validation of that prior. B is a limited-sample histogram with a conditional likelihood estimate, not the full-period completeness or b-value result. Locations are initial associations, before final relocation.")
    elif item['figure'] in ['S6','S8']:
        item.update(partial_panels=[],file_labels=[],independent_files=[],missing='No accepted current result. For S6, the unverified background grid and dependent previous pilot were quarantined; alternative-profile arithmetic tests are not validated locations. No older output is substituted.',caption='Not reproduced at the current checkpoint.')
    elif item['figure']=='2':item['missing']=f"Panels A and B need multiyear calibrated/relocated events and magnitudes. The current {s['events']} initial associations remain provisional."
    elif item['figure']=='S12':item['missing']=f"Panels A--H need relocated sector selections and manual depth review. {loc.get('associated_cpoz_p_picks',0)} independent CPOZ P arrivals now exist, but the required sector gathers remain unfinished."
    elif item['figure']=='S14':item['missing']=f"The cluster histories require three-year exposure, confirmed events and relative magnitudes. The present {h.get('valid_hours',0):.3f} hour scan produced {h.get('candidates',0)} unconfirmed threshold crossings, not reviewed families."
(R/'figure_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
numbers=dict(CurrentFiles=s['files'],CurrentPicks=s['picks'],CurrentPPicks=s['p_picks'],CurrentSPicks=s['s_picks'],CurrentEvents=s['events'],CurrentAssigned=s['assigned_picks'],CurrentHours=f"{s['processed_channel_hours']:.3f}",CurrentAmplitudes=m.get('amplitude_measurements',0),CurrentSNR=m.get('snr_passing',0),CurrentMagnitudeEdges=m.get('magnitude_edges',0),CurrentMagnitudes=m.get('calibrated_magnitudes',0),CurrentCalibration=v.get('calibration_events',0),CurrentHybridHours=f"{h.get('valid_hours',0):.3f}",CurrentHybridCandidates=h.get('candidates',0),CurrentCPOZ=loc.get('associated_cpoz_p_picks',0),CurrentSPPairs=loc.get('paired_observations',0),CurrentBadSP=loc.get('nonpositive_sp',0))
plot_scope=pd.read_csv(D/'routine_plot_scope.csv').set_index('panel')
numbers.update(CurrentRoutineOffMap=int(plot_scope.loc['1A','outside_view']),CurrentStudyOffMap=int(plot_scope.loc['S5/map','outside_view']),CurrentStudyOffEastDepth=int(plot_scope.loc['S5/easting-depth','outside_view']))
(R/'continuation_numbers.tex').write_text('\n'.join('\\newcommand{\\'+key+'}{'+str(value)+'}' for key,value in numbers.items())+'\n')
gather=read('cpoz_gather_summary');hybrid_metrics=read('hybrid_candidate_metrics');catalog_fi=read('catalog_frequency_index')
experiment_path=ROOT/'data/exploratory/velest_stability/summary.json'
experiment=json.loads(experiment_path.read_text()) if experiment_path.exists() else {}
findings=[f"The CPOZ diagnostic contains {gather.get('gathers',0)} P-aligned observed waveforms. It does not implement the relocated ring-sector test.",
          f"Spectral measurements were calculated for {hybrid_metrics.get('measured',0)} of {hybrid_metrics.get('candidates',0)} template crossings. None is confirmed as a hybrid event; spectral windows use correlation alignment and still require onset/coda review."]
findings.append(f"Catalog frequency-index screening measured {catalog_fi.get('station_measurements',0)} station windows for {catalog_fi.get('measured_events',0)} provisional events. Station FIs are averaged; no low-frequency candidate is classified as a confirmed hybrid without onset and coda review.")
if experiment:
    findings.append(f"The alternative-profile VELEST experiment used {experiment.get('events',0)} provisional events. Both real precisions were attempted with identical serialized inputs.")
    if experiment.get('maximum_velocity_difference_km_s'):
        change=experiment['maximum_velocity_difference_km_s']
        findings.append(f"Maximum 32/64-bit differences were {change['Vp_km_s']:.3f} km/s for Vp and {change['Vs_km_s']:.3f} km/s for Vs, with {experiment['maximum_depth_difference_km']:.3f} km in fitted depth.")
    failures=[str(r['bits']) for r in experiment.get('runs',[]) if not r.get('physical_velocity_check',False)]
    if failures:findings.append('Physical velocity checks did not pass in the '+', '.join(failures)+'-bit attempts. No fitted velocity or location is accepted.')
    else:findings.append('Both runs pass the necessary positive-Vp-greater-than-Vs check. This ordering and numerical agreement do not replace reviewed phases or the documented regional calibration; no experimental fit is accepted for S6 or relocation.')
    for run in experiment.get('runs',[]):
        if 'rms_s' in run:findings.append(f"The {run['bits']}-bit experiment has event-RMS aggregate {run['rms_s']:.3f} s.")
experiment_models=[ROOT/f'data/exploratory/velest_stability/model_{bits}.csv' for bits in [32,64]]
if all(p.exists() for p in experiment_models):
    models=[pd.read_csv(p) for p in experiment_models]
    lines=[r'\begin{longtable}{rrrrr}\toprule Layer top (km b.s.l.) & $V_p$, 32 bit & $V_s$, 32 bit & $V_p$, 64 bit & $V_s$, 64 bit\\\midrule\endhead']
    for model_left,model_right in zip(models[0].itertuples(),models[1].itertuples()):
        assert model_left.layer_top_km==model_right.layer_top_km
        lines.append(' & '.join(f'{x:.2f}' for x in [model_left.layer_top_km,model_left.Vp_km_s,model_left.Vs_km_s,model_right.Vp_km_s,model_right.Vs_km_s])+r'\\')
    lines.append(r'\bottomrule\end{longtable}')
    (R/'experimental_velocity_table.tex').write_text('\n'.join(lines)+'\n')
else:(R/'experimental_velocity_table.tex').write_text('No paired experimental models were saved.\n')
(R/'revision_findings.tex').write_text('\n\n'.join(tex(t) for t in findings)+'\n')
counts={status:sum(r['status']==status for r in rows) for status in ['independently reproduced','partially reproduced','not reproduced']}
(D/'panel_status.json').write_text(json.dumps(dict(counts=counts,partial=[r['panel'] for r in rows if r['status']=='partially reproduced'],unreproduced=[r['panel'] for r in rows if r['status']=='not reproduced']),indent=2)+'\n')
(R/'continuation_panel_summary.tex').write_text('Partial counterparts: '+tex(', '.join(r['panel'] for r in rows if r['status']=='partially reproduced'))+'. All remaining panels are not reproduced.\n')
chains=[]
for r in rows:
    if r['status']!='partially reproduced':continue
    classification=('External routine-catalog context; not independent detections' if r['panel'] in ['1A','1C'] or r['panel'].startswith('S5') else
                    'Original GNSS/leveling observations plus explicitly labeled historical source estimates/reconstruction' if r['panel']=='1B' else
                    'Own processing of observations/metadata; trained weights and external Md calibration are identified in the method record')
    chains += [r'\paragraph{'+tex(r['panel'])+r' --- partial data-to-plot chain.} '+tex(classification)+'.']
    inputs=r['input_observation_files']
    if len(inputs)<=6:chains.append('Inputs: '+', '.join(r'\path{'+p+'}' for p in inputs)+'.')
    else:chains.append(str(len(inputs))+r' exact input files are listed under this panel in \path{docs/panel_record.json}; waveform hashes and intervals are in \path{docs/continuation_processed_inputs.json}, with source receipts in the input manifests.')
    chains.append('Data command: '+r'\par\noindent '+r'\par\noindent '.join(r'\path{'+cmd+'}' for cmd in r['data_command'].split(' && '))+r'\par')
    chains.append('Saved numerical output: '+', '.join(r'\path{'+p.strip()+'}' for p in r['saved_data'].split(';'))+'.')
    chains.append(r'Plot command: \path{'+r['plot_command']+'}'+r'\par Output: \path{'+r['generated_figure']+'}.')
    if r['report_figure']!=r['generated_figure']:chains.append(r'The same plotting command composes the report figure: \path{'+r['report_figure']+'}.')
(R/'partial_panel_chains.tex').write_text('\n\n'.join(chains)+'\n')
t=[r'\begin{longtable}{>{\raggedright\arraybackslash}p{.12\linewidth}>{\raggedright\arraybackslash}p{.25\linewidth}>{\raggedright\arraybackslash}p{.52\linewidth}}',r'\toprule Panel/view & Quantity & Status, specification and limitation\\\midrule\endhead']
for r in rows:t.append(' & '.join([tex(r['panel']).replace('/',r'/\allowbreak{}'),tex(r['quantity']),tex(r['status']+'. '+r['documentation']+'. '+r['parameters']+'. '+r['blocker'])])+r'\\[3pt]')
t += [r'\bottomrule\end{longtable}'];(R/'panels_table.tex').write_text('\n'.join(t)+'\n')
event_days=pd.to_datetime(pd.read_csv(D/'initial_events.csv').time,utc=True,format='ISO8601').dt.strftime('%Y-%m-%d').value_counts().sort_index().rename_axis('UTC_day').reset_index(name='provisional_events')
event_days.to_csv(D/'event_day_counts.csv',index=False)
late_events=int(event_days.loc[event_days.UTC_day.ge('2025-03-19'),'provisional_events'].sum())
facts=[('GNSS observations in plotted interval',c['gnss_rows']),('GNSS extension in 2025 (days)',c['gnss2025_extension_rows']),('GNSS overlap RMS after offset (m)',f"{c['gnss2025_overlap_demeaned_rms_m']:.6f}"),('All historical routine records',c['routine_events']),('Located historical routine records',c['routine_located']),('Located routine study events',c['routine_study_located']),('Difference from published study count',c['located_count_difference_from_publication']),('Processed waveform files',s['files']),('Processed union channel-hours',f"{s['processed_channel_hours']:.3f}"),('Merged picks',s['picks']),('Provisional GaMMA events',s['events']),('Candidates on 19--20 March 2025',late_events),('Successful segmented waveform requests',a['files']),('Pending waveform requests',a['jobs_by_status'].get('pending',0))]
(R/'continuation_results.tex').write_text('\n'.join([r'\begin{longtable}{p{.70\linewidth}r}\toprule Quantity & Value\\\midrule\endhead']+[tex(k)+' & '+tex(value)+r'\\' for k,value in facts]+[r'\bottomrule\end{longtable}'])+f"\nThe last two study days account for {late_events} of {s['events']} provisional events ({100*late_events/s['events']:.1f} percent). This temporal concentration prevents inferring a multiyear seismicity history from this checkpoint.\n")
velest_text=(f"The independent VELEST pilot completed {len(v.get('runs',[]))} runs and retained {v.get('quality_passing',0)} events after the final filters. The small calibration subset and absent independent phase review do not establish a reliable regional velocity model." if v.get('completed') else r'No accepted whole-catalog VELEST solve exists. The current blocker is recorded in \path{data/continuation/velest_summary.json}; prior dependent products are quarantined. The separate alternative-profile precision experiment is recorded in \path{data/exploratory/velest_stability/summary.json}. No earlier locations are substituted.')
if v.get('model_checks'):
    check=v['model_checks']
    velest_text+=f" The fitted layer $V_p/V_s$ ratios range from {check['minimum_VpVs']:.3f} to {check['maximum_VpVs']:.3f}. The two regional starting choices yield RMS differences of {check['between_starting_models_rms_Vp_km_s']:.3f} km/s in $V_p$ and {check['between_starting_models_rms_Vs_km_s']:.3f} km/s in $V_s$. These sensitivities limit geological interpretation."
if v.get('precision_check'):
    changes=v['precision_check']['maximum_calibration_velocity_changes_km_s']
    max_p=max(c['Vp_km_s'] for c in changes.values());max_s=max(c['Vs_km_s'] for c in changes.values())
    velest_text+=f" Repeating calibration with 64-bit rather than 32-bit arithmetic changes some fitted layers by up to {max_p:.2f} km/s in $V_p$ and {max_s:.2f} km/s in $V_s$. This substantial arithmetic sensitivity prevents accepting the pilot fit as a robust regional calibration."
(R/'continuation_velest.tex').write_text(velest_text+'\n')
if stats.get('b') is not None:
    sigma=stats.get('b_sigma')
    error=f" \\pm {sigma:.2f}" if sigma is not None else ''
    text=f"The conditional magnitude-frequency fit gives $M_c={stats['Mc']:.1f}$ and $b={stats['b']:.2f}{error}$ from only {stats['events_ge_Mc']} selected magnitudes at or above the pilot completeness level. The quoted Shi--Bolt standard error excludes coverage, selection and magnitude-calibration biases. This calculation does not establish population completeness or a regional b-value."
else:text='No magnitude-frequency fit can be calculated from the current saved magnitudes.'
(R/'continuation_magnitude_statistics.tex').write_text(text+'\n')
if v.get('completed') and (D/'independent_velest_model.csv').exists():
    model=pd.read_csv(D/'independent_velest_model.csv')
    lines=[r'\begin{longtable}{rrrr}\toprule Layer top (km b.s.l.) & $V_p$ (km/s) & $V_s$ (km/s) & $V_p/V_s$\\\midrule\endhead']
    for r in model.itertuples(index=False):lines.append(' & '.join(f'{x:.3f}' for x in r)+r'\\')
    lines.append(r'\bottomrule\end{longtable}')
    (R/'pilot_velocity_table.tex').write_text('\n'.join(lines)+'\n')
else:(R/'pilot_velocity_table.tex').write_text('No successful pilot velocity fit is available.\n')
stages=json.loads((ROOT/'docs/stages.json').read_text())
updates={
    0:f"Partial: {a['files']} segmented waveform requests downloaded; {a['jobs_by_status'].get('pending',0)} pending. {s['files']} total processed files, {s['processed_channel_hours']:.3f} channel-hours, {len(s['stations'])} stations. RAN credentials missing.",
    1:f"Executed: {s['picks']} merged picks; exclusions/probability bounds checked. Full-period inference unfinished.",
    3:f"Executed: {s['events']} provisional GaMMA events, {s['assigned_picks']} assigned picks. Explicit Tramelli 2021 alternative; exact 2018 numerical profile still missing.",
    4:'Blocked: unverified 2008 background grid and previous dependent pilot quarantined. The separate 2021-profile arithmetic experiment is exploratory; no accepted calibrated locations or fitted model.',
    5:'Generic TomoDD source retrieved, classified and compiled. Scientific differential-time pairing and both relocation rounds remain unfinished, not executed.',
    7:f"Executed: {m.get('amplitude_measurements',0)} amplitudes, {m.get('snr_passing',0)} SNR passes, {m.get('magnitude_edges',0)} amplitude-ratio equations, {m.get('calibrated_magnitudes',0)} provisional magnitudes. Initial locations; final relocated-catalog calibration unfinished.",
    8:f"Pilot histogram and maximum-curvature calculation executed on {stats.get('magnitudes',0)} values; conditional b={stats.get('b')} from {stats.get('events_ge_Mc',0)} values at/above pilot Mc. Full-period completeness/b not established; selection and systematic limitations remain.",
    9:'Not reproduced: independently reviewed polarities/S-P amplitudes, accepted locations/model, FK Green functions and event-specific settings remain missing or unfinished. No author mechanism result table is used by this run.',
    10:f"Internal S-P checks: {loc.get('paired_observations',0)} pairs, {loc.get('nonpositive_sp',0)} nonpositive. {loc.get('associated_cpoz_p_picks',0)} CPOZ P arrivals. Relocated sector gathers and manual deep-event review unfinished.",
    11:f"Executed {h.get('valid_hours',0):.3f} common CAAM/COLB scan hours; {h.get('candidates',0)} unconfirmed crossings. Three-year review, clustering and catalog-wide FI incomplete.",
    12:f"Executed: {c['leveling_rows']} source historical entries with estimates/reconstruction distinguished, {c['gnss_rows']} daily GNSS through 2025-03-20, {c['routine_located']} historical and {c['routine_study_located']} study-period located routine events. External contextual/calibration roles only; historical count difference unresolved."
}
for i,status in updates.items():stages[i]['status']=status
(ROOT/'docs/stages.json').write_text(json.dumps(stages,indent=2)+'\n')
# Superseded displays are removed only after their current counterparts exist.
# Their source scripts/data and earlier versions remain in the repository/history.
replacements={'historical_leveling_partial':'figure_1B_displacement','historical_catalog_context':'figure_1_combined',
    'routine_catalog_context':'figure_S5_routine','coverage_partial':'continuation_coverage','stations_partial':'continuation_stations'}
removed=[]
for old,new in replacements.items():
    assert (ROOT/'figures'/f'{new}.pdf').exists()
    for ext in ['pdf','png']:
        path=ROOT/'figures'/f'{old}.{ext}'
        if path.exists():path.unlink();removed.append(str(path.relative_to(ROOT)))
(ROOT/'docs/replaced_context_figures.json').write_text(json.dumps(dict(obsolete_stems=replacements,removed_this_build=removed,
    preserved='Source scripts, saved baseline data, useful diagnostics, original uploads and Git history'),indent=2)+'\n')
print(counts)
