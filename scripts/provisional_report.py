"""Integrate executed, explicitly provisional analyses in publication order."""
from pathlib import Path
import json,re
import pandas as pd
import grid_report as gr
ROOT=gr.ROOT;D=ROOT/'data/grid_calibration/merged4';R=ROOT/'report'
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def main():
    u=read(D/'uncertainty/summary.json');d=read(D/'diagnosis/summary.json');m=read(D/'magnitude/downstream_summary.json');ms=read(D/'magnitude/magnitude_statistics.json');ps=read(D/'panels/summary.json');f=read(D/'focal/summary.json');settled=read(D/'settled_trial/summary.json')
    rows=read(ROOT/'docs/panel_record.json');layout=read(R/'figure_layout.json');byid={x['panel']:x for x in rows}
    common='Provisional independent observations and processing; sparse coverage, unreviewed phases, calibration path sensitivity. Not established fault geometry or exact reproduction.'
    mapping={
      '2':('figure_2_provisional.pdf',['2A','2B'],['weekly_counts.csv','sectors.csv'],'Weekly counts and depth evolution of the sparse relocated subset. Weeks without own events are not joined as measured zeros. External routine counts use a separately labeled right axis. Geographic masks are explicit alternatives; no confirmed-hybrid markers are added.'),
      '3':('figure_3_provisional.pdf',['3/map','3/northing-depth','3/easting-depth'],['relocated.csv'],f'{ps["events"]} independently relocated trial events, 0.111--7.965 km depth. Own relative magnitudes set sizes where available; crosses mark missing magnitudes. This scattered subset does not establish the published ring or its depth limit.'),
      'S6':('figure_S6_provisional.pdf',['S6/map','S6/northing-depth','S6/easting-depth'],['velest.csv'],f'{ps["velest_events"]} independently fitted VELEST events pass the numerical pick/RMS/gap filters. Physical layer ordering and the final small-update gate pass; stagnation, held-out prediction, regional and precision-path stability prevent acceptance. These are plotted as provisional results.'),
      'S7':('figure_S7_provisional.pdf',['S7A/map','S7A/easting-depth','S7B','S7D','S7F','S7C','S7E','S7G'],['../uncertainty/regional_svd.csv'],f'{u["svd_events"]} conditional HypoDD SVD estimates from every supported connected component in four explicit alternative quadrants. The names in the computation are not verified original region membership. Reported 2-sigma errors are retained, including kilometer-scale outliers. Zero cross-correlation counts cannot appear on logarithmic count axes; they remain in the map and saved table. KDE uses Scott bandwidth in log10(error), an explicit display convention.'),
      'S10':('figure_S10_provisional.pdf',[f'S10/{y}' for y in range(2022,2026)],['year2022.csv','year2023.csv','year2024.csv','year2025.csv'],'Independently selected calendar-year subsets. Event counts reflect sparse exposure and numerical filtering, not regional seismicity rates. All years have at least one provisional relocated result.'),
      'S11':('figure_S11_provisional.pdf',[r['panel'] for r in ps['groups'] if r['panel'].startswith('S11') and r['events']>0],[f'swarm-{i}.csv' for i in range(1,5)],'Selections use the dates written in the published panel titles, with inclusive end days. Only nonempty selections have partial counterparts. Empty selections are explicitly labeled: they do not establish absence of earthquakes.'),
      'S12':('figure_S12_provisional.pdf',[f'S12{x}' for x in 'ABCDEFGH'],['sectors.csv','cpoz_index.csv','cpoz_gathers.npz'],f'{ps["cpoz_traces"]} independently picked CPOZ component traces, aligned -1/+7 s about P and filtered above 4 Hz, joined to same-cohort relocated events. Alternative masks use geography without imposing the publication\'s depth bands. Trace colors show normalized recorded amplitude; strips do not interpolate missing events. Manual onset/depth review remains incomplete.'),
      'S13':('figure_S13_provisional.pdf',['S13A','S13B'],['relocated.csv'],'Own relocated coordinates are plotted for full-caldera and onshore views. Independent coarse coastline replaces the satellite layer, whose retrieval and rendering remain unimplemented. No publication pixels enter either map.')}
    data_command='.venv/bin/python scripts/grid_panel_data.py';plot_command='.venv/bin/python scripts/publication_plots.py'
    for item in layout:
        if item['figure'] in mapping:
            file,panels,files,note=mapping[item['figure']]
            sources=[str((D/'panels'/x).resolve().relative_to(ROOT)) for x in files]
            assert all((ROOT/x).exists() for x in sources)
            item.update(partial_panels=panels,independent_files=['figures/'+file],file_labels=[item['figure']+'; provisional numerical counterpart'],caption=note+' '+common,missing='')
            if item['figure']=='S11':item['missing']='S11/swarm-1, swarm-3 and swarm-4 have no surviving independently relocated events in their written calendar windows; sparse exposure, not evidence that no earthquakes occurred.'
            for panel in panels:
                r=byid[panel];r.update(status='partially reproduced',blocker=common+' '+note,parameters=note,inputs=sources,input_files=sources,saved_data='; '.join(sources),data_command=data_command if item['figure']!='S7' else '.venv/bin/python scripts/grid_uncertainty.py',plot_command=plot_command,output='figures/'+file,output_files=['figures/'+file],independent_data_generation=True,agreement_with_publication='Not quantitatively established; subset and methodology differ.',provenance='Independently computed from eligible waveforms, responses, own picks and own locations; authorized Tan-distributed reference grid. See data/grid_calibration/input_classification.json.',attempt='Executed; numerical result plotted even though scientific acceptance remains unresolved.')
        if item['figure']=='S8':
            item['caption']=f'Partial relocated-subset magnitude calculation: {m["calibrated_magnitudes"]} own estimates, {ms["matched_Md"]} matched routine Md anchors in panel A. {m["amplitude_measurements"]} response-corrected channel measurements, {m["snr_passing"]} above 5 dB, {m["magnitude_edges"]} relative-amplitude equations. Mc={ms["Mc"]:.1f}, b={ms["b"]:.3f} +/- {ms["b_sigma"]:.3f} from {ms["events_ge_Mc"]} selected magnitudes. Calibration comparison is not independent validation; sparse acquisition cannot establish population completeness or b-value.'
            for panel in item['panels']:
                r=byid[panel];src=[str((D/'magnitude'/f).relative_to(ROOT)) for f in ['amplitude_measurements.csv','magnitude_edges.csv','magnitudes.csv','routine_matches.csv','figure_S8A.csv','figure_S8B.csv','magnitude_statistics.json']]
                r.update(inputs=src,input_files=src,saved_data='; '.join(src),data_command='.venv/bin/python scripts/downstream_checks.py --dataset grid --workers 6; .venv/bin/python scripts/magnitude_statistics.py --grid',plot_command=plot_command,blocker=item['caption'],parameters='Tan S1-S3 relative-amplitude method; direct least squares, squared normalized correlations and unit Md regularization are disclosed departures/settings.',independent_data_generation=True,agreement_with_publication='Conditional subset estimates only; not a test of full-catalog Mc=0.4 or b=0.97.')
        if item['figure']=='4':
            item['missing']=f'SKHASH was executed: {f["measured_polarities"]} automated first-motion measurements on {f["candidate_events"]} own events; {f["stable_screen_polarities"]} passed the provisional sign/SNR screen. Seven events lack eight stable polarities; the remaining event has a 186.158-degree gap, exceeding the unchanged 90-degree gate. No mechanism is returned. Reviewed polarities, S/P constraints and independent gCAP/FK processing remain missing; no beachballs can be plotted.'
            for panel in item['panels']:byid[panel].update(blocker=item['missing'],attempt='SKHASH 1.1.5 executed; all candidates rejected by observation/geometry checks.',data_command='.venv/bin/python scripts/grid_focal_attempt.py',saved_data='data/grid_calibration/merged4/focal/polarity_screen.csv; data/grid_calibration/merged4/focal/run.log')
        if item['figure']=='S9':
            item['missing']='The documented NCCP+NCCS>100 selection was computed on the provisional relocated catalog and returned zero events. No qualified spatial result exists to plot. More waveform-linked neighboring events are needed; the threshold was not relaxed.'
            for panel in item['panels']:byid[panel].update(blocker=item['missing'],attempt='Exact written count filter executed; zero passing events.',data_command=data_command,saved_data='data/grid_calibration/merged4/panels/best_located.csv')
        if item['figure']=='S14':
            item.update(partial_panels=['S14/1','S14/2','S14/3'],independent_files=['figures/figure_S14_candidates.pdf'],file_labels=['Template-family candidates; not confirmed clusters'],caption='Partial candidate-family analysis from original observations. Twelve strongest independent correlation crossings per E1/E2/E3 template are displayed with measured frequency index and horizontal amplitude ratio. Template assignment is not manual confirmation or validated clustering. The amplitude ratio is not called a relative magnitude because common propagation paths are unverified. These are not the published 70 events or their full-period history.',missing='S14/unclustered: no independent unclustered hybrid sample or validated family assignment. The three-template threshold scan cannot itself supply that class.')
            for panel in item['partial_panels']:
                files=['data/grid_calibration/merged4/hybrid/'+name for name in ['hybrid_candidates.csv','display_candidates.csv','display_waveforms.npz']]
                byid[panel].update(status='partially reproduced',inputs=files,input_files=files,saved_data='; '.join(files),data_command='.venv/bin/python scripts/extend_hybrid_scan.py --dataset grid; .venv/bin/python scripts/grid_hybrid_candidates.py',plot_command=plot_command,blocker=item['caption'],output='figures/figure_S14_candidates.pdf',independent_data_generation=True,agreement_with_publication='Unconfirmed candidate-family counterpart; confirmed clusters and timing evolution untested.')
        if item['figure']=='S15':
            item.update(partial_panels=['S15A','S15B','S15C'],independent_files=['figures/hybrid_E1.pdf','figures/hybrid_E2.pdf','figures/hybrid_E3.pdf'],file_labels=['S15A analogue: different documented E1 event','S15B analogue: different documented E2 event','S15C: documented E3 event'],caption='Partial numerical waveform/spectral counterparts. A/B analogues use the written-method E1/E2 family templates, which are different events from the published A/B examples. They are explicitly not exact event reproduction. C uses E3. All are processed original CAAM/COLB observations; normalization and spectral settings are disclosed. No author waveform or spectral array is used.',missing='S15D: no retained independently relocated event with depth <0.6 km south of 40.83 N in this cohort, hence no suitable west-Accademia extremely-shallow example. Incorrectly labeled examples are not substituted.')
            for panel,event in [('S15A','E1'),('S15B','E2')]:
                files=['data/observations/'+event+'_waveforms.csv']
                files += ['data/observations/'+event+'_'+sta+'_'+comp+'_spectrum.npz' for sta in ['CAAM','COLB'] for comp in ['Z','E']]
                byid[panel].update(status='partially reproduced',inputs=files,input_files=files,saved_data='; '.join(files),data_command='.venv/bin/python scripts/analyze_observations.py',plot_command=plot_command,blocker=item['caption'],output='figures/hybrid_'+event+'.pdf',independent_data_generation=True,agreement_with_publication='Different documented template event: methodological analogue, not exact event agreement.')
    for r in rows:
        if r['panel'].startswith(('1A','S5')):r['parameters']=re.sub(r'Full color ranges:.*?routine_plot_scope.csv\.', 'Fixed depth color limits 0--5 km with explicit under/over treatment; 1A endpoints are approximate because not labeled.',r['parameters'])
        if r['status']=='partially reproduced':r['plot_command']=plot_command
    # Keep missing-panel records consistent with the actually executed selection
    # and solver attempts, rather than retaining pre-computation audit text.
    for item in layout:
        if item['figure'] not in ['S11','S14','S15']:continue
        for panel in set(item['panels'])-set(item['partial_panels']):
            row=byid[panel];row['blocker']=item['missing']
            row['data_command']=data_command if item['figure']!='S14' else '.venv/bin/python scripts/extend_hybrid_scan.py --dataset grid; .venv/bin/python scripts/grid_hybrid_candidates.py'
            row['attempt']='Computed on the current independent subset; no qualifying numerical counterpart. See saved selection/measurement record.'
            row['saved_data']={'S11':'data/grid_calibration/merged4/panels/'+panel.split('/')[-1]+'.csv','S14':'data/grid_calibration/merged4/hybrid/hybrid_summary.json','S15':'data/grid_calibration/merged4/panels/summary.json'}[item['figure']]
            assert (ROOT/row['saved_data']).is_file(),row['saved_data']
            if item['figure']=='S11':row['parameters']='Four written calendar windows from the publication panel titles; inclusive start, exclusive day after end. No location or event values digitized.'
    for name in ['panel_record.json','panels.json']:write(ROOT/'docs'/name,rows)
    write(R/'figure_layout.json',layout)
    partial=[r['panel'] for r in rows if r['status']=='partially reproduced'];missing=[r['panel'] for r in rows if r['status']=='not reproduced']
    (R/'continuation_panel_summary.tex').write_text(f'{len(partial)} panel/views have partial numerical counterparts and {len(missing)} remain unreproduced. Independent data generation and agreement with the publication are recorded separately.\n')
    table=[r'\begin{longtable}{>{\raggedright\arraybackslash}p{.13\linewidth}>{\raggedright\arraybackslash}p{.28\linewidth}>{\raggedright\arraybackslash}p{.49\linewidth}}',r'\toprule Panel/view & Quantity & Status and remaining limitation\\\midrule\endhead']
    for r in rows:table.append(' & '.join([gr.tex(r['panel']).replace('/',r'/\allowbreak{}'),gr.tex(r['quantity']),gr.tex(r['status']+'. '+r['blocker'])])+r'\\[3pt]')
    table.append(r'\bottomrule\end{longtable}');(R/'panels_table.tex').write_text('\n'.join(table)+'\n')
    chain=[]
    for item in layout:
        if not item['independent_files']:continue
        r=byid[item['partial_panels'][0]];chain.append(r'\paragraph{Figure '+gr.tex(item['figure'])+r'.} '+gr.tex(', '.join(item['partial_panels']))+r'. Data: \path{'+r['data_command']+r'}. Plot: \path{'+plot_command+r'}. Saved numerical inputs: ')
        vals=sorted({p.strip() for panel in item['partial_panels'] for p in byid[panel].get('saved_data','').split(';') if p.strip()})
        if not vals:vals=r.get('input_files',r.get('inputs',[]))
        if isinstance(vals,str):vals=[vals]
        chain.extend(r'\par\path{'+str(v)+r'}' for v in vals[:7]);chain.append(r'\par Output: \path{'+item['independent_files'][0]+r'}. Full upstream observation hashes and command chain are in \path{docs/panel_record.json}.')
    (R/'partial_panel_chains.tex').write_text('\n'.join(line.rstrip() for line in chain)+'\n')
    held=d['heldout'];fit=held.get('fitted',{});start=held.get('starting',{})
    new=rf'''\section{{Additional validation and provisional analyses}}
The new figures expose available numerical results rather than replacing unvalidated locations with blank panels. Independent generation does not establish their scientific accuracy. The frozen calibration cohort and original 3D grid are unchanged; the retained original grid hash and conventions are documented above.

\paragraph{{Precision and convergence diagnosis.}}
The original 32/64-bit initial model, station file, observations and control files are byte-identical. Both prelocation runs stop at 14 iterations. Their maximum depth difference is initially 0.02 km and grows to 0.89 km through coupled updates. Common-start tests give identical printed round-1 locations and zero printed round-2 depth difference; the latter horizontal difference is 11.1 m. Backup decisions diverge in round 2; subsequent paths stop either at iteration limits or after four backups. Instrumented, otherwise unchanged generic solvers reproduce the original output bytes. The damped prelocation normal-matrix condition numbers range from {d['instrumentation']['condition_number_range'][0]:.0f} to {d['instrumentation']['condition_number_range'][1]:.0f}; this test does not support a catastrophic linear-solve failure. Nonlinear paths, ray changes and two-decimal restart serialization amplify initial differences. Exact arithmetic attribution of every ray transition remains untested.

Repeated fixed-model prelocation, up to ten 14-iteration passes in each precision, still fails the unchanged 100 m stability gate. The 64-bit last pass moves an event 282 m horizontally and 0.24 km vertically. More iterations alone do not resolve this oscillation. No locations from this failed correction are substituted. Every fifth calibration event was withheld: 30 events train the model, 8 events (126 phases) test it. Unweighted held-out phase RMS is {start.get('residual_rms_s',float('nan')):.4f} s for the starting profile and {fit.get('residual_rms_s',float('nan')):.4f} s for the refitted profile. A smaller solver event statistic is a different quantity and cannot reverse this failed prediction check. Manual phase/association review and absolute-location validation remain necessary.

\paragraph{{Relocation and conditional uncertainty.}}
Across 124 common events, rounds 1 and 2 differ by a median {u['median_horizontal_m']:.1f} m and maximum {u['max_horizontal_m']:.1f} m horizontally; median absolute depth change is {u['median_absolute_depth_km']:.3f} km and maximum {u['max_depth_km']:.3f} km. On the same {u['matched_observations']['cc']['n']} waveform constraints, RMS improves from {u['matched_observations']['cc']['round1_rms_s']:.4f} to {u['matched_observations']['cc']['round2_rms_s']:.4f} s. The same {u['matched_observations']['picked']['n']} picked-phase constraints improve from {u['matched_observations']['picked']['round1_rms_s']:.4f} to {u['matched_observations']['picked']['round2_rms_s']:.4f} s. Fixed grid, positive travel times, all-cluster residual coverage and recomputed station-gap checks pass. These are internal checks, not absolute accuracy. {u['zero_cc_events']} events have no retained waveform correlations. No event passes S9's $NCCP+NCCS>100$ filter.

SVD was attempted on every connected component with at least four events in four explicit quadrants; {u['svd_events']} estimates were returned. Their 2-sigma depth errors reach 4.002 km, whereas the publication describes most coordinate errors near 10 m. The regional masks, sample sizes and starting locations differ, so this is a consequential failure to recover comparable precision, not a contradiction of the original estimates. S7 retains the large uncertainties. S12 uses {ps['cpoz_traces']} recorded component traces joined to the same relocated cohort. Sector masks and spectral normalization are explicit assumptions; no published depth bands select our events.

\paragraph{{Magnitude and source mechanisms.}}
The relocated-subset magnitude stage measured {m['amplitude_measurements']} channels, with {m['snr_passing']} passing 5 dB, and inverted {m['magnitude_edges']} relative-amplitude equations to obtain {m['calibrated_magnitudes']} magnitudes. Routine duration magnitudes enter only as regularization after independent detection and location. All accepted components have full numerical rank; formal errors are conditional on the response, location, weighting and unit regularization assumptions. Maximum curvature gives $M_c\simeq {ms['Mc']:.1f}$ and the conditional likelihood estimate is $b={ms['b']:.3f}\pm {ms['b_sigma']:.3f}$ ({ms['events_ge_Mc']} above $M_c$). This selected, discontinuously observed sample cannot establish the published full-catalog $M_c=0.4$ or $b=0.97$.

SKHASH 1.1.5 now executes on {f['measured_polarities']} automated measurements from {f['candidate_events']} events; {f['stable_screen_polarities']} pass an explicit sign/SNR screen. Seven events fail the minimum-eight-polarity rule, and event 641 fails the unchanged azimuthal-gap rule (186.158 versus 90 degrees). No mechanism is returned. These are unreviewed candidate polarities, not Tan's manual measurements; no supplied mechanism or S/P value is used. Independent gCAP/FK processing, reviewed S/P measurements and event-specific waveform settings remain incomplete. The generic software is isolated in \path{{.venv-skhash}} because its NumPy requirement differs from the main analysis environment; the main NumPy 2.4.6 was restored. Dependency caches remain under the existing user pip cache; scientific products remain inside this repository.

\paragraph{{Commands and evidence.}}
\path{{scripts/diagnose_grid_paths.py}}, \path{{scripts/settle_grid_prelocation.py}}, \path{{scripts/grid_uncertainty.py}}, \path{{scripts/downstream_checks.py --dataset grid}}, \path{{scripts/grid_focal_attempt.py}} and \path{{scripts/grid_panel_data.py}} generate the new saved products. The single procedure \path{{.venv/bin/python scripts/rebuild_provisional_workflow.py}} executes these stages and compiles both documents. \path{{docs/PROVISIONAL_CONTINUATION.md}} records the full command and input chain, including acquisition scope. Procedure completion is separate from scientific acceptance.
'''
    new=new.replace('Manual phase/association review and absolute-location validation remain necessary.', 'Manual phase/association review and absolute-location validation remain necessary. The own fitted 1--3 km layer has Vp/Vs=1.17. Passing positive-velocity ordering alone does not establish a plausible or well-constrained elastic structure; this low ratio warrants scientific review.')
    new=new.replace('M_c\\simeq -0.0','M_c\\simeq 0.0')
    new=new.replace(r'\paragraph{Commands and evidence.}',r'\paragraph{Commands and evidence.}\begingroup\small\raggedright')+r'\par\endgroup'+'\n'
    (R/'provisional_validation.tex').write_text(new)
    # Correct assertions superseded by these executed stages, retaining the
    # earlier controls and their failed-run evidence.
    path=R/'grid_calibration.tex';text=path.read_text().replace('Reviewed phases, held-out refitting for this model and independent absolute-location validation remain undone.','Reviewed phases and independent absolute-location validation remain undone; held-out refitting is reported in the additional validation section.').replace('Failed or unvalidated outputs do not populate Figures 2--4, S6--S7 or S9--S13.','Available provisional numerical results now populate Figures 2--3, S6--S7, S10--S13; scientific acceptance remains unresolved.').replace('Figures 3 and 4A--B have no valid independent counterparts, so none is invented for style matching.','Figure 3 now has an explicitly provisional counterpart. Figure 4A--B still lack a returned mechanism; no beachball is invented.')
    path.write_text(text)
    path=R/'reproduction_documentation.tex';text=path.read_text();tag=r'\input{report/provisional_validation.tex}'
    if tag not in text:text=text.replace(r'\input{report/grid_calibration.tex}',r'\input{report/grid_calibration.tex}'+'\n'+tag)
    text=text.replace('The current amplitude/SNR stage measured', 'The earlier 1,003-association checkpoint measured').replace('These are actual executed outputs, not a promised future count.', 'These historical outputs are retained for comparison with the distinct current-grid cohort; they no longer supply Figure S8.')
    text=text.replace('relocated CPOZ sector gathers, manual deep-event review', 'exact original CPOZ sector selection, manual deep-event review')
    text=text.replace('The frozen calibration cohort has', 'The historical 1,003-association cohort has')
    text=text.replace('E1 and E2 are not substituted for the different published S15A/B examples.', 'E1 and E2 are explicitly different-event analogues in S15A/B, not reproductions of those exact events.')
    text=text.replace('The current authorized-grid rebuild is \\path{scripts/rebuild_grid_workflow.py};', 'The current procedure is \\path{scripts/rebuild_provisional_workflow.py --calibration};')
    text=text.replace('Quarantined, unverified grid attribution: Battaglia', 'Explicitly authorized Tan-distributed starting grid, attributed to Battaglia')
    text=text.replace('Unmatched panels have text notices in this paper and explicit placeholders only in the comparison PDF.', 'Panels with no usable numerical result have explicit missing-result notices. Available provisional results and clearly labeled alternative examples are plotted rather than withheld for failing validation.')
    path.write_text(text)
    old=R/'continuation_magnitude_statistics.tex';text=old.read_text()
    if not text.startswith('Historical'):old.write_text('Historical 1,003-association checkpoint (superseded for Figure S8): '+text)
    (R/'grid_narrative.tex').write_text(gr.tex(f'The independently processed checkpoint contains 1,015 provisional associations; 916 pass causal input checks and 38 form the unreviewed calibration subset. Grid-derived VELEST yields 216 filter-passing events. Two fixed-grid TomoDD rounds leave {ps["events"]} gap-passing trial events. Figure 2 shows their observed-window weekly counts and depth evolution; sparse exposure does not support full-period seismicity-rate or migration inferences.')+'\n')
    path=R/'main_paper.tex';text=path.read_text();a=text.index('\n',text.index(r'\section*{A clearer view of the current phase of unrest}'))+1;b=text.index(r'\input{report/figure_sections/F3.tex}',a)
    text=text[:a]+gr.tex(f'Figure 3 shows the {ps["events"]} independently relocated trial events. Five lie deeper than 5 km and are retained with an over-range color. Their sparse, scattered distribution does not recover the ring fault or its proposed depth limits. Calibration-path differences reach 0.89 km in depth and conditional SVD errors reach 4 km; fault-scale interpretations are therefore premature. Figure 4 remains unreproduced because no event passes the attempted focal-mechanism constraints.')+'\n'+text[b:];path.write_text(text)
    path=R/'reproduced_supplement.tex';text=path.read_text()
    cohort=read(ROOT/'data/calibration_followup/expanded/analysis_summary.json')
    for macro,key in [('CurrentPicks','picks'),('CurrentPPicks','p_picks'),('CurrentSPicks','s_picks'),('CurrentAssigned','assigned_picks'),('CurrentEvents','events')]:
        text=text.replace('\\'+macro+'{}',f'{cohort[key]:,}')
    hybrid=read(D/'hybrid/hybrid_summary.json')
    text=text.replace('Local convergence is achieved after documented layer merging,', 'The final small-update gate is reached after documented layer merging,')
    # These macros otherwise refer to an older scan snapshot.
    text=text.replace(r'\CurrentHybridHours{}',f'{hybrid["valid_hours"]:.3f}').replace(r'\CurrentHybridCandidates{}',str(hybrid['candidates']))
    text=re.sub(r'The search covered .*?(?=\n\\paragraph\{Depth)',lambda _:gr.tex(f'The search covered {hybrid["valid_hours"]:.3f} hours of available common CAAM/COLB intervals and returned {hybrid["candidates"]} unconfirmed threshold crossings. Figure S14 displays an explicitly unconfirmed highest-correlation subset with measured FI and horizontal-amplitude ratios; no family is declared a confirmed hybrid cluster.'),text,flags=re.S)
    number_file=R/'continuation_numbers.tex';numbers=number_file.read_text()
    for key,value in [('CurrentHybridHours',f'{hybrid["valid_hours"]:.3f}'),('CurrentHybridCandidates',str(hybrid['candidates']))]:
        numbers=re.sub(r'\\newcommand\{\\'+key+r'\}\{[^}]*\}',lambda _:chr(92)+'newcommand{'+chr(92)+key+'}{'+value+'}',numbers)
    number_file.write_text(numbers)
    replacements={
      r'\paragraph{Earthquake relocation.}':r'\paragraph{Earthquake relocation.} Two fixed-grid TomoDD rounds and regional HypoDD SVD analyses were executed. Figures S6--S7 and S10--S13 now show supported provisional numerical results. No event satisfies S9\textquotesingle s more-than-100-correlated-phase filter. All locations retain unresolved calibration and phase-validation limits.',
      r'\paragraph{Local magnitude.}':rf'\paragraph{{Local magnitude.}} The relocated subset gives {m["calibrated_magnitudes"]} provisional magnitudes from {m["magnitude_edges"]} amplitude equations. Figure S8 shows calibration matches and the conditional magnitude distribution. Routine duration magnitudes are external anchors, not independent measurements or validation.',
      r'\paragraph{Focal mechanism estimation.}':r'\paragraph{Focal mechanism estimation.} The SKHASH attempt returned no mechanisms: seven candidates lack eight stable automated polarities and the remaining candidate fails the 90-degree azimuthal-gap rule. Manual polarity/S--P review and independent gCAP/FK processing remain incomplete.',
      r'\paragraph{Depth of earthquakes in the central region.}':rf'\paragraph{{Depth of earthquakes in the central region.}} Figure S12 now displays {ps["cpoz_traces"]} P-aligned CPOZ component traces with explicit alternative geographic masks. Relocated depths and onsets remain provisional. Neither these gathers nor the small SVD subsets establish the publication\textquotesingle s depth limits.'}
    for prefix,newtext in replacements.items():text=re.sub(re.escape(prefix)+r'.*?(?=\n\n|\n\\paragraph|\n\\section)',lambda m:newtext,text,flags=re.S)
    text=text.replace('Numerical results and validation are reported after the supplement.','Figure S6 shows the provisional numerical result; detailed validation follows the supplement.').replace('but does not substitute for the regional uncertainty or common-receiver tests in Figures S7 and S12.','and is complemented by provisional regional uncertainty and common-receiver tests in Figures S7 and S12.')
    text=text.replace('The first two templates are different examples from the published S15A/B panels and are not inserted in their place.', 'The first two written-method family templates appear as clearly labeled S15A/B analogues; they are different events and do not reproduce those exact examples.')
    text=text.replace('It did not produce independently confirmed families for Figure S14.', 'Figure S14 displays an explicitly unconfirmed, highest-correlation candidate subset with measured FI and horizontal amplitude ratios; no family is declared a confirmed hybrid cluster.')
    text=text.replace('Cluster-relative magnitudes were not assigned because cluster membership has not been established.', 'The candidate displays give log horizontal-amplitude ratios within each template group. These are not called relative magnitudes because shared source paths and cluster membership have not been validated.')
    model=pd.read_csv(D/'uncertainty/model.csv')
    table=r'\paragraph{Table S1: own provisional one-dimensional model --- partial.} The following independently fitted four-layer model is a numerical counterpart, not an accepted physical model or the authors\textquotesingle{} fit. Tops are km below sea level; velocities are km/s. Regional averaging, merged boundaries and validation failures are documented below.\par'+'\n'+r'\begin{center}\begin{tabular}{rrrr}\hline Top & $V_p$ & $V_s$ & $V_p/V_s$\\\hline'+'\n'
    table+='\n'.join(f'{r.layer_top_km:.1f} & {r.Vp_km_s:.2f} & {r.Vs_km_s:.2f} & {r.VpVs:.3f}'+r'\\' for r in model.itertuples())+'\n'+r'\hline\end{tabular}\end{center}'+'\n'
    a=text.index(r'\paragraph{Table S1:');b=text.index(r'\paragraph{Table S2:',a);text=text[:a]+table+text[b:]
    path.write_text(text)
    status=read(ROOT/'data/grid_calibration/current_status.json');status.update(panel_counts={s:sum(r['status']==s for r in rows) for s in ['independently reproduced','partially reproduced','not reproduced']},provisional_panels=partial,unreproduced_panels=missing,additional_results=dict(svd_events=u['svd_events'],magnitudes=m['calibrated_magnitudes'],cpoz_traces=ps['cpoz_traces'],focal_solutions=f['solutions']))
    write(ROOT/'data/grid_calibration/current_status.json',status)
    status['summary']='The frozen 1,015-association cohort yields 216 VELEST numerical-filter passes and 123 final TomoDD gap passes. Small final changes can reflect backup stagnation; identical-input precision paths, regional starts and held-out prediction fail scientific acceptance. Both relocation rounds and conditional downstream analyses executed. The separately numbered coverage extension is recorded in data/coverage_extension/report_summary.json.'
    status['tomodd_status']='Both fixed-grid rounds executed. Matched residual, geometry and arrival-preservation checks pass; calibration sensitivity and absolute-location validation remain unresolved.'
    write(ROOT/'data/grid_calibration/current_status.json',status)
    stages=read(ROOT/'docs/stages.json')
    updates={
      1:f'Frozen 1,015-association cohort: {cohort["picks"]} independent picks. Later coverage extension is a separate identifier set, never joined by integer ID.',
      4:'216 numerical-filter passes; common-start precision test isolates accumulated nonlinear path sensitivity. Held-out phase RMS worsens from 0.2177 to 0.2198 s; extended prelocation still oscillates. No scientific acceptance.',
      5:'Both fixed-grid rounds executed; 123 final gap passes. Matched-observation residuals improve, but round-to-round shifts and calibration dependence remain. Numerical results plotted provisionally.',
      6:f'{u["svd_events"]} conditional SVD estimates returned from supported components in four alternative quadrants. Up to 4.002 km depth error; original regional masks and absolute accuracy unresolved.',
      7:f'{m["amplitude_measurements"]} measurements, {m["snr_passing"]} SNR passes, {m["magnitude_edges"]} equations, {m["calibrated_magnitudes"]} current-cohort provisional magnitudes. Routine Md is calibration only.',
      8:f'Conditional selected-subset Mc={ms["Mc"]:.2f}, b={ms["b"]:.3f} +/- {ms["b_sigma"]:.3f}, N above Mc={ms["events_ge_Mc"]}. Population completeness untested.',
      9:'Actual SKHASH attempt: 76 measurements, 35 stable automated polarities, zero solutions after unchanged polarity/gap filters. Manual review, S/P and gCAP/FK remain incomplete.',
      10:f'{ps["cpoz_traces"]} actual P-aligned CPOZ traces; 382 positive S-P pairs, 0.1784 s approximate-model residual RMS; 44 deep events flagged for review. Exact masks and manual depth validation unresolved.',
      11:f'{hybrid["valid_hours"]:.3f} common hours, {hybrid["candidates"]} unconfirmed crossings. Thirty-six candidate-family displays; no confirmed hybrid clusters or full-period history.'}
    for i,value in updates.items():stages[i]['status']=value
    write(ROOT/'docs/stages.json',stages)
    classification=read(ROOT/'data/grid_calibration/input_classification.json')
    used={r['file'] for r in classification['observations']}
    for name in ['magnitude/amplitude_measurements.csv','panels/cpoz_index.csv','hybrid/display_candidates.csv']:
        used.update(pd.read_csv(D/name).source.dropna())
    existing={r['file']:r for r in classification['observations']}
    import hashlib
    receipts={r['file']:r for r in read(ROOT/'docs/continuous_retrievals.json') if r.get('file')}
    for name in sorted(used-set(existing)):
        existing[name]=dict(file=name,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),url=receipts.get(name,{}).get('url'),classification='Original waveform observations; measured by own downstream stage')
    classification['observations']=list(existing.values())
    classification['method_inputs'].append(dict(file='data/grid_calibration/merged4/focal/summary.json',role='Generic SKHASH 1.1.5 provenance and isolated software hash; own screened observations only'))
    classification['method_inputs']=list({r['file']:r for r in classification['method_inputs']}.values())
    classification['context']='Routine catalog is used only in labeled context and post-detection magnitude calibration; it supplies no picks, associations or locations. GNSS and source-provided leveling estimates retain separate provenance labels.'
    classification['own_outputs'].append('data/coverage_extension/ (separate event identifiers; original observations and own processing)')
    classification['own_outputs']=list(dict.fromkeys(classification['own_outputs']))
    write(ROOT/'data/grid_calibration/input_classification.json',classification)
    # The solver's final small change can follow its four-backup stop, which is
    # stagnation rather than proof of reaching a robust optimum.
    summary=read(D/'summary.json')
    for region,info in summary['regions'].items():
        info['accepted']=False;info['local_change_gate_passed']=info.get('converged',False)
        info['scientific_acceptance_note']='Small last-pass change only; precision/start sensitivity, backup termination and held-out prediction prevent scientific acceptance.'
    write(D/'summary.json',summary)
    for name in ['grid_calibration.tex','provisional_validation.tex','grid_narrative.tex']:
        path=R/name;text=path.read_text().replace('Four-layer fits converge locally','Four-layer fits pass the last-pass change gate').replace('converged model, not the still-moving second-round fit','last-pass model, not the still-moving second-round fit').replace('local convergence does not remove path sensitivity','a small final change does not remove path sensitivity')
        if name=='provisional_validation.tex':text=text.replace('Backup decisions diverge in round 2;', 'The small final update can result from four-backup stagnation and is not proof of an optimum. Backup decisions diverge in round 2;')
        path.write_text(text)
    print(json.dumps(status,indent=2))
if __name__=='__main__':main()
