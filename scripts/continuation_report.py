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
                 blocker='Current catalog snapshot differs from the historical snapshot: 12,503 located study events versus 12,083. No tuning to published counts. Natural Earth coastline substitutes for the unavailable original relief/inland-zero contour.' if p!='1C' else 'Monthly counts and exact-time cumulative Md>0.2 reconstructed from the current routine snapshot; historical count differences unresolved. March 2025 is a partial month.',
                 saved_data='data/continuation/figure_'+('S5' if p.startswith('S5') else p)+'.csv')
    if p=='1B':
        r.update(status='partially reproduced',data_command='.venv/bin/python scripts/continue_context.py',plot_command='.venv/bin/python scripts/plot_continuation.py',
                 input_observation_files=['inputs/extended/delgaudio2010_table.doc','inputs/continuation/RITE_daily.txt','inputs/continuation/RITE_Timeseries_Format.readme','inputs/continuation/RITE_2000_2025.txt','inputs/continuation/Time_Series_Format.txt'],
                 generated_figure='figures/figure_1B_displacement.pdf',saved_data='data/continuation/rite_gnss.csv; data/continuation/historical_leveling.csv',
                 parameters='128 leveling observations, 1905--2009; daily GNSS 2000-05-29 through 2025-03-20. Median offset from 23 overlapping leveling epochs, +/-15 days. Extension beyond original 2023 endpoint is labeled.',
                 attempt='Text observations and format notes verified; daily observations now cover 2020--2025. No JPG used.',
                 blocker='Benchmark equivalence and datum-joining convention are assumed because the exact original stitching recipe is not specified. Calendar gaps remain unfilled; no missing recent-data blocker through 2025-03-20.')
    if p=='S1':r.update(generated_figure='figures/continuation_coverage.pdf',input_observation_files=processed,data_command='.venv/bin/python scripts/process_continuous.py all --frozen',plot_command='.venv/bin/python scripts/plot_continuation.py',attempt='Executed actual sample-span union for the frozen processed checkpoint; no requested interval is counted as covered.',saved_data='data/continuation/processed_coverage_union.json',blocker=f"{s['files']} files processed, {s['processed_channel_hours']:.3f} union channel-hours. Full-period queue still pending; actual gaps and unavailable RAN credentials remain. Requests/availability are not coverage.")
    if p=='S2':
        r.update(input_observation_files=['inputs/models/stations.csv','inputs/continuation/coastline.zip'],supporting_metadata_files=['inputs/continuation/IV_responses.xml','inputs/continuation/2I_responses.xml'],generated_figure='figures/continuation_stations.pdf',saved_data='data/continuation/figure_S2.csv',data_command='.venv/bin/python scripts/plot_continuation.py',plot_command='.venv/bin/python scripts/plot_continuation.py',attempt='Plotted all 51 released station identifiers. Response epochs for actual processed observations are verified separately; exact membership of the published 48 instruments is unresolved.')
    if p.startswith('S6'):
        r['status']='not reproduced'
        r['blocker']='Independent VELEST pilot: '+('calibration and whole-catalog passes executed, but limited/noncontinuous sample and unreviewed input phases prevent an exact result.' if v.get('completed') else 'No successful whole-catalog solve. The exact numerical failure is recorded in data/continuation/velest_summary.json; no older locations are substituted.')
        if v.get('completed') and v.get('quality_passing',0):
            r.update(status='partially reproduced',generated_figure='figures/figure_S6_pilot.pdf',saved_data='data/continuation/figure_S6.csv; data/continuation/velest_filtered.csv',
                data_command='.venv/bin/python scripts/run_velest.py',plot_command='.venv/bin/python scripts/plot_continuation.py',
                input_observation_files=processed+['inputs/extended/background_3d_vmod'],
                parameters=f"Pilot calibration uses {v.get('calibration_events',0)} independent candidates, not the published 373. Two regional starts and two calibration rounds each; five fixed-model catalog passes; rejection at 0.4 then 0.3 s; final >=6 picks, RMS <=0.25 s, gap <=300 degrees. Positive-time filtering and geometric selection are explicit assumptions; dampings and boxes are in the implementation record.",
                attempt=f"Executed independent regional calibration and five catalog passes; {v['quality_passing']} events pass the final filters. No author-fitted solution used.")
    if p.startswith('S8'):
        r['status']='not reproduced'
        r['blocker']=f"{m.get('amplitude_measurements',0)} channel measurements, {m.get('snr_passing',0)} passing SNR, {m.get('magnitude_edges',0)} relative-amplitude equations, {m.get('calibrated_magnitudes',0)} provisional magnitudes. Final relocated locations/full exposure remain missing; routine Md is an allowed regularizer, not independent validation."
        if m.get('calibrated_magnitudes',0)>0:
            r.update(status='partially reproduced',generated_figure='figures/figure_S8_pilot.pdf',saved_data=f'data/continuation/figure_{p}.csv',
                data_command='.venv/bin/python scripts/downstream_checks.py --dataset continuation && .venv/bin/python scripts/magnitude_statistics.py',plot_command='.venv/bin/python scripts/plot_continuation.py',
                input_observation_files=processed+routine+['inputs/continuation/IV_responses.xml','inputs/continuation/2I_responses.xml'],
                parameters='5 s signal, 2 s preceding noise; SNR >=5 dB; stations with associated phases only; >=2 shared stations; separation < one fifth of station distance; squared zero-lag correlation weights; Md regularization lambda=1 for unique one-to-one matches within 2 s. Initial locations. B uses 0.1 magnitude bins and a >=20-above-Mc minimum for reporting a pilot b estimate.',
                attempt='Executed amplitude-ratio inversion on initial locations; partial pilot comparison/distribution only. No claim of full-period completeness or b-value.')
    if p.startswith('S12'):
        r['blocker']=f"{loc.get('associated_cpoz_p_picks',0)} independently associated CPOZ P arrivals now exist. Relocated ring-sector selection and manual depth review remain unfinished; internal S-P checks do not establish location accuracy."
    if p.startswith('S14'):
        r['blocker']=f"{h.get('valid_hours',0):.3f} common CAAM/COLB scan hours; {h.get('candidates',0)} unconfirmed threshold crossings. Three-year scan, reviewed clusters, relative magnitudes and timing histories remain unfinished."
    if p in ['2A','2B','3/map','3/northing-depth','3/easting-depth']:
        r['blocker']=f"{s['events']} provisional GaMMA events are not a complete calibrated, TomoDD-relocated catalog. Multiyear acquisition and downstream processing remain incomplete."
    r['input_observation_files']=sorted(set(r.get('input_observation_files',[])))
(ROOT/'docs/panel_record.json').write_text(json.dumps(rows,indent=2)+'\n');(ROOT/'docs/panels.json').write_text(json.dumps(rows,indent=2)+'\n')
layout=json.loads((R/'figure_layout.json').read_text())
for item in layout:
    if item['figure']=='1':
        item.update(partial_panels=['1A','1B','1C'],file_labels=['1A--C'],independent_files=['figures/figure_1_combined.pdf'],missing='',caption='Partial reconstruction from permitted original displacement observations and external routine-catalog records. A: 16,046 located routine events and five Md>=4 stars. B: historical leveling datum; daily GNSS through 20 March 2025, with the extension beyond 2023 shaded. C: all monthly counts and exact-time cumulative Md>0.2; March includes days 1--20 only. This is not the independently detected catalog. The basemap and live catalog snapshot differ from the publication.')
    elif item['figure']=='S5':
        item.update(partial_panels=item['panels'],file_labels=['S5, all views'],independent_files=['figures/figure_S5_routine.pdf'],missing='',caption='External routine-catalog data, independently selected and plotted: 12,503 located events, 21 January 2022--20 March 2025. This is 420 more than the published historical snapshot. No author-derived catalog is used to adjust that difference; these are not independent detections.')
    elif item['figure']=='S1':item.update(independent_files=['figures/continuation_coverage.pdf'],caption=f"Partial: {s['files']} processed files, {len(s['stations'])} station names and {s['processed_channel_hours']:.3f} channel-hours after union of overlapping intervals. Empty intervals are not connected or counted as coverage.")
    elif item['figure']=='S2':item.update(independent_files=['figures/continuation_stations.pdf'])
    elif item['figure']=='S6' and v.get('completed') and v.get('quality_passing',0):
        item.update(partial_panels=item['panels'],file_labels=['S6, all views'],independent_files=['figures/figure_S6_pilot.pdf'],missing='',caption=f"Partial independent VELEST pilot: {v['quality_passing']} events pass the final six-pick, 0.25 s RMS and 300-degree gap filters. This limited, unreviewed sample is not the published 61,809-event catalog. The initial association model and regional averaging choices differ or are assumed; no TomoDD refinement is implied.")
    elif item['figure']=='S8' and m.get('calibrated_magnitudes',0)>0:
        item.update(partial_panels=item['panels'],file_labels=['S8A--B'],independent_files=['figures/figure_S8_pilot.pdf'],missing='',caption=f"Partial amplitude-ratio pilot: {m['calibrated_magnitudes']} provisional magnitudes from independent observations, with routine Md as the documented calibration prior. A is not an independent validation of that prior. B is a limited-sample histogram, not the full-period completeness or b-value result. Locations are initial associations, before final relocation.")
    elif item['figure'] in ['S6','S8']:
        item.update(partial_panels=[],file_labels=[],independent_files=[],missing='No successful current pilot result. See the recorded stage failure; no older output is substituted.',caption='Not reproduced at the current checkpoint.')
    elif item['figure']=='2':item['missing']=f"Panels A and B need multiyear calibrated/relocated events and magnitudes. The current {s['events']} initial associations remain provisional."
    elif item['figure']=='S12':item['missing']=f"Panels A--H need relocated sector selections and manual depth review. {loc.get('associated_cpoz_p_picks',0)} independent CPOZ P arrivals now exist, but the required sector gathers remain unfinished."
    elif item['figure']=='S14':item['missing']=f"The cluster histories require three-year exposure, confirmed events and relative magnitudes. The present {h.get('valid_hours',0):.3f} hour scan produced {h.get('candidates',0)} unconfirmed threshold crossings, not reviewed families."
(R/'figure_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
numbers=dict(CurrentFiles=s['files'],CurrentPicks=s['picks'],CurrentPPicks=s['p_picks'],CurrentSPicks=s['s_picks'],CurrentEvents=s['events'],CurrentAssigned=s['assigned_picks'],CurrentHours=f"{s['processed_channel_hours']:.3f}",CurrentAmplitudes=m.get('amplitude_measurements',0),CurrentSNR=m.get('snr_passing',0),CurrentMagnitudeEdges=m.get('magnitude_edges',0),CurrentMagnitudes=m.get('calibrated_magnitudes',0),CurrentCalibration=v.get('calibration_events',0),CurrentHybridHours=f"{h.get('valid_hours',0):.3f}",CurrentHybridCandidates=h.get('candidates',0),CurrentCPOZ=loc.get('associated_cpoz_p_picks',0),CurrentSPPairs=loc.get('paired_observations',0),CurrentBadSP=loc.get('nonpositive_sp',0))
(R/'continuation_numbers.tex').write_text('\n'.join('\\newcommand{\\'+key+'}{'+str(value)+'}' for key,value in numbers.items())+'\n')
counts={status:sum(r['status']==status for r in rows) for status in ['independently reproduced','partially reproduced','not reproduced']}
(D/'panel_status.json').write_text(json.dumps(dict(counts=counts,partial=[r['panel'] for r in rows if r['status']=='partially reproduced'],unreproduced=[r['panel'] for r in rows if r['status']=='not reproduced']),indent=2)+'\n')
(R/'continuation_panel_summary.tex').write_text('Partial counterparts: '+tex(', '.join(r['panel'] for r in rows if r['status']=='partially reproduced'))+'. All remaining panels are not reproduced.\n')
t=[r'\begin{longtable}{>{\raggedright\arraybackslash}p{.12\linewidth}>{\raggedright\arraybackslash}p{.25\linewidth}>{\raggedright\arraybackslash}p{.52\linewidth}}',r'\toprule Panel/view & Quantity & Status, specification and limitation\\\midrule\endhead']
for r in rows:t.append(' & '.join([tex(r['panel']).replace('/',r'/\allowbreak{}'),tex(r['quantity']),tex(r['status']+'. '+r['documentation']+'. '+r['parameters']+'. '+r['blocker'])])+r'\\[3pt]')
t += [r'\bottomrule\end{longtable}'];(R/'panels_table.tex').write_text('\n'.join(t)+'\n')
facts=[('GNSS observations in plotted interval',c['gnss_rows']),('GNSS extension in 2025 (days)',c['gnss2025_extension_rows']),('GNSS overlap RMS after offset (m)',f"{c['gnss2025_overlap_demeaned_rms_m']:.6f}"),('All historical routine records',c['routine_events']),('Located historical routine records',c['routine_located']),('Located routine study events',c['routine_study_located']),('Difference from published study count',c['located_count_difference_from_publication']),('Processed waveform files',s['files']),('Processed union channel-hours',f"{s['processed_channel_hours']:.3f}"),('Merged picks',s['picks']),('Provisional GaMMA events',s['events']),('Downloaded six-hour chunks',a['files']),('Pending six-hour requests',a['jobs_by_status'].get('pending',0))]
(R/'continuation_results.tex').write_text('\n'.join([r'\begin{longtable}{p{.70\linewidth}r}\toprule Quantity & Observed result\\\midrule\endhead']+[tex(k)+' & '+tex(value)+r'\\' for k,value in facts]+[r'\bottomrule\end{longtable}'])+'\n')
velest_text=(f"The independent VELEST pilot completed {len(v.get('runs',[]))} runs and retained {v.get('quality_passing',0)} events after the final filters. The small calibration subset and absent independent phase review do not establish a reliable regional velocity model." if v.get('completed') else r'The VELEST pilot did not complete an accepted whole-catalog solve. The numerical failure and partial calibration runs are recorded in \path{data/continuation/velest_summary.json}. No earlier successful locations are substituted.')
if v.get('model_checks'):
    check=v['model_checks']
    velest_text+=f" The fitted layer $V_p/V_s$ ratios range from {check['minimum_VpVs']:.3f} to {check['maximum_VpVs']:.3f}. The two regional starting choices yield RMS differences of {check['between_starting_models_rms_Vp_km_s']:.3f} km/s in $V_p$ and {check['between_starting_models_rms_Vs_km_s']:.3f} km/s in $V_s$. These sensitivities limit geological interpretation."
if v.get('precision_check'):
    changes=v['precision_check']['maximum_calibration_velocity_changes_km_s']
    max_p=max(c['Vp_km_s'] for c in changes.values());max_s=max(c['Vs_km_s'] for c in changes.values())
    velest_text+=f" Repeating calibration with 64-bit rather than 32-bit arithmetic changes some fitted layers by up to {max_p:.2f} km/s in $V_p$ and {max_s:.2f} km/s in $V_s$. This substantial arithmetic sensitivity prevents accepting the pilot fit as a robust regional calibration."
(R/'continuation_velest.tex').write_text(velest_text+'\n')
if v.get('completed') and (D/'independent_velest_model.csv').exists():
    model=pd.read_csv(D/'independent_velest_model.csv')
    lines=[r'\begin{longtable}{rrrr}\toprule Layer top (km b.s.l.) & $V_p$ (km/s) & $V_s$ (km/s) & $V_p/V_s$\\\midrule\endhead']
    for r in model.itertuples(index=False):lines.append(' & '.join(f'{x:.3f}' for x in r)+r'\\')
    lines.append(r'\bottomrule\end{longtable}')
    (R/'pilot_velocity_table.tex').write_text('\n'.join(lines)+'\n')
else:(R/'pilot_velocity_table.tex').write_text('No successful pilot velocity fit is available.\n')
stages=json.loads((ROOT/'docs/stages.json').read_text())
updates={
    0:f"Partial: {a['files']} six-hour chunks downloaded; {a['jobs_by_status'].get('pending',0)} pending. {s['files']} total processed files, {s['processed_channel_hours']:.3f} channel-hours, {len(s['stations'])} stations. RAN credentials missing.",
    1:f"Executed: {s['picks']} merged picks; exclusions/probability bounds checked. Full-period inference unfinished.",
    3:f"Executed: {s['events']} provisional GaMMA events, {s['assigned_picks']} assigned picks. Explicit Tramelli 2021 alternative; exact 2018 numerical profile still missing.",
    4:f"Partial VELEST pilot: completed={v.get('completed')}; {v.get('calibration_events',0)} calibration events, {len(v.get('runs',[]))} successful runs, {v.get('quality_passing',0)} quality-passing locations. Exact subset/model validity not established.",
    5:'Generic TomoDD source retrieved, classified and compiled. Scientific differential-time pairing and both relocation rounds remain unfinished, not executed.',
    7:f"Executed: {m.get('amplitude_measurements',0)} amplitudes, {m.get('snr_passing',0)} SNR passes, {m.get('magnitude_edges',0)} amplitude-ratio equations, {m.get('calibrated_magnitudes',0)} provisional magnitudes. Initial locations; final relocated-catalog calibration unfinished.",
    8:f"Pilot histogram and maximum-curvature calculation executed on {stats.get('magnitudes',0)} values. Full-period completeness/b not established; {stats.get('b_blocker','selection and systematic limitations remain')}",
    10:f"Internal S-P checks: {loc.get('paired_observations',0)} pairs, {loc.get('nonpositive_sp',0)} nonpositive. {loc.get('associated_cpoz_p_picks',0)} CPOZ P arrivals. Relocated sector gathers and manual deep-event review unfinished.",
    11:f"Executed {h.get('valid_hours',0):.3f} common CAAM/COLB scan hours; {h.get('candidates',0)} unconfirmed crossings. Three-year review, clustering and catalog-wide FI incomplete.",
    12:f"Executed: {c['leveling_rows']} original leveling observations, {c['gnss_rows']} daily GNSS through 2025-03-20, {c['routine_located']} historical and {c['routine_study_located']} study-period located routine events. External catalog roles explicitly permitted; historical count difference unresolved."
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
