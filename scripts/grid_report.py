"""Current grid-run evidence and plotting records, without promoting failed fits."""
from pathlib import Path
import json,re,hashlib,zipfile
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/grid_calibration';R=ROOT/'report'
def tex(s):return ''.join({'&':r'\&','%':r'\%','_':r'\_','#':r'\#','<':r'$<$','>':r'$>$'}.get(c,c) for c in str(s))
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    s=read(D/'merged4/summary.json');v=read(D/'merged4/validation.json');t=read(D/'merged4/tomodd/summary.json');inv=read(D/'input_inventory.json');g=read(D/'grid_provenance.json');style=read(ROOT/'data/continuation/routine_plot_style.json');nr=s['paper_filter_passing'];best=s['lowest_converged_phase_RMS_region'];final=s['regions'][best]['runs'][-1];prec=v['precision_difference']
    tomostat=t['status'];tomofacts='; '.join('round '+str(x['round'])+(': '+str(x.get('output_events',0))+' outputs, '+str(x.get('gap_passing_events',0))+' gap passes' if 'error' not in x else ': failed; '+x['error'][:160]) for x in t['runs'])
    overview=f"The expanded {inv['events']}-association checkpoint supplies {inv['usable_causal_events']} causally usable events and {s['calibration_events']} calibration candidates. The explicitly authorized Tan-distributed reference grid now supplies independently averaged starting profiles. Four-layer fits converge locally, and {nr} events pass the paper's numerical filters after five catalog passes. Full 32/64-bit inversion paths still differ by {prec['max_depth_km']:.2f} km in depth; their locations remain exploratory. {tomostat.capitalize()}. No validated multiyear structural or mechanism result is claimed."
    (R/'grid_narrative.tex').write_text(tex(overview)+'\n')
    text=rf'''\section{{Authorized-grid calibration and fixed-grid relocation}}
This section supersedes the calibration completion statements in earlier checkpoints. Older experiments remain below as historical diagnostics. The present run uses the expanded cohort; integer event identifiers must not be joined to the older 1,003-event cohort.

\paragraph{{Reference input and transformation.}}
Tan et al.'s distribution at revision \path{{f84c9c9dc6bb1501a95a833f6634199a63d4f3b3}} supplies \path{{models/3d_vmod}}, attributed to Battaglia et al. (2008; doi:10.1111/j.1365-2478.2007.00687.x). The current instruction explicitly permits that file as a starting/reference input. Its unchanged {g['bytes']:,}-byte copy is \path{{data/grid_calibration/reference_grid.original}}; SHA-256 is \path{{{g['sha256']}}}. It is not claimed to be an independently retrieved original 2008 array. The grid contains 23 longitude, 14 latitude and 27 depth nodes, ordered longitude fastest, then latitude and depth. Longitude/latitude are degrees east/north, depth is km below sea level, $V_p$ is km/s, and the second volume is dimensionless $V_p/V_s$. Pointwise $V_s=V_p/(V_p/V_s)$. Depth extends from $-0.5$ to a 200 km padding node; the shallow model ends at 7 km. The original article describes an 18 by 18 by 9 km volume with 0.5 km spacing, unlike these irregular/padded axes. The historical transformation remains undocumented. The generic TomoDD reader and manual establish the encoding; the current 3D file is not regridded.

Regional averaging uses explicit assumed boxes: $14.01$--$14.21^\circ$E, $40.76$--$40.87^\circ$N for the caldera and $14.11$--$14.16^\circ$E, $40.80$--$40.84^\circ$N for Pozzuoli--Solfatara. Node weights are $\cos(\mathrm{{latitude}})$; $V_p$ and pointwise $V_s$ are averaged separately. Exact $V_p=0.1$ km/s nodes are interpreted as nonsolid/air and excluded from the 1D average. The first entirely solid plane, 0.1 km deep, extends upward to $-0.5$ km. Horizontal padding and the terminal 200 km layer are excluded from regional depth integration. These masks, layer boundaries and weights are assumptions where Tan gives region names without numerical masks. They do not recover an undocumented transformation.

\paragraph{{Independent observations and corrections to the failed pilot.}}
The saved expanded input contains {inv['processed_files']} processed files, {inv['stations']} station names and {inv['channel_hours']:.3f} union channel-hours. Independent association times span {tex(inv['period'][0])} to {tex(inv['period'][1])}, with large gaps; this is not full-period coverage. {inv['usable_causal_events']} of {inv['events']} associations have positive travel times and no observed nonpositive S--P pairs. Calibration additionally requires at least four P and two S picks, more than ten total picks, gap below $180^\circ$ and no initial 0/8 km depth-bound hit, leaving {s['calibration_events']} unreviewed candidates. This is not Tan's manually selected 373-event sample. No routine catalog or author result selects these events.

The first eight-layer attempts produce $V_p\leq V_s$ after the station-delay inversion and are rejected. The generic VELEST guide recommends avoiding low-velocity layers initially, locating events before velocity inversion, merging similar unresolved layers and damping unresolved deep velocities. Accordingly LOWVELOCLAY is zero, prelocation uses 14 iterations, and four layer tops are $-0.5,1,3,5$ km. The deepest velocity damping is 100, other layer damping is 1; deeper unconstrained velocities are not freely fitted. A failed damping-1000 attempt overflowed the fixed-width output field and is retained as a serialization failure. The corrected four-layer run preserves physical ordering. It performs two seven-iteration calibration rounds followed by three declared convergence checks, without changing observations or relaxing the paper's final filters. The reference P delay is fixed at {tex(s['reference_station'])}. The converged model, not the still-moving second-round fit, supplies the catalog run.

\paragraph{{Validation and catalog filtering.}}
Both regional fits satisfy the stated local stability gates: every horizontal/depth change below 100 m, velocity change below 0.05 km/s, and station-delay change below 0.02 s in the final extra pass. The lower converged unweighted phase RMS is {final['residual_rms_s']:.3f} s ({tex(best)}). These are numerical gates, not absolute accuracy. Regional starts still give maximum differences of {s['starting_model_dependence']['max_horizontal_m']:.1f} m horizontally and {s['starting_model_dependence']['max_depth_km']:.2f} km in depth. Complete 32/64-bit paths differ by {prec['max_horizontal_m']:.1f} m horizontally, {prec['max_depth_km']:.2f} km in depth, {v['velocity_difference_km_s']:.2f} km/s in velocity and {v['station_delay_difference_s']:.2f} s in station delay. Starting both precisions from the same converged fit instead gives identical printed coordinates and velocities. Thus local convergence does not remove path sensitivity; printed equality does not bound unprinted differences. Reviewed phases, held-out refitting for this model and independent absolute-location validation remain undone. The fit is not accepted as a scientific catalog.

All {inv['usable_causal_events']} usable events enter the fixed-model run. Three passes precede $|r|>0.4$ s rejection; another pass precedes $|r|>0.3$ s rejection. The fifth pass and final six-pick, 0.25 s reported-RMS and $300^\circ$ gap filters leave {nr} exploratory locations. Fixed models and station corrections were checked after each pass; rejected phases are not replaced. The generic reported event statistic differs from unweighted phase RMS, as verified in the preceding checkpoint.

\paragraph{{Observed differential times and TomoDD.}}
{tex(tomofacts)}. {tex(tomostat)}. The neighbor graph and windows belong to this expanded event set; no old-cohort waveform cache is reused. Exact measured counts, failed windows, controls and residuals are in \path{{data/grid_calibration/merged4/tomodd}}. Original absolute picks supply phase-pair times; response-corrected two-second windows supply coherency-weighted delays. Ten nearest neighbors, 1--15 Hz filtering, correlation/coherence at least 0.6, maximum lag 0.25 s, six-phase clustering links, LSQR damping 50 and two four-iteration weight blocks are explicit assumptions where configuration is unpublished. JOINT=0 fixes the 3D grid. A second round rebases travel-time differences to the independently updated origins. Generic method tables required by the solver are separated from the example observations in its distribution. No author-fitted corrections, velocity model or earthquake result is substituted. Failed or unvalidated outputs do not populate Figures 2--4, S6--S7 or S9--S13.

\paragraph{{Display verification and scientific boundaries.}}
Every current generated figure is rebuilt from saved numerical products by \path{{scripts/publication_plots.py}}. Input/output hashes and panel correspondence are in \path{{data/grid_calibration/style/plot_inventory.json}}. Figure S5 uses the printed 0--5 km depth limits and ticks 0,1,2,3,4,5; Figure 1A has printed ticks 0,2,4 but unlabeled endpoints, so 0--5 km is an explicitly approximate normalization rather than an exact recovery. Neither numerical table changes. Magenta denotes depths above 5 km: {style['1A']['over_count']} in 1A and {style['S5']['over_count']} in S5; white is reserved below zero. Missing magnitudes remain crosses. The area law $0.7+3\,10^{{M_d-2}}$ points squared is a display assumption, not a recovered published formula. S4/S15 do not print a numerical spectral color scale; their disclosed normalized-PSD display is $-80$ to 0 dB, with white/black under/over colors. Counts and ranges are saved in \path{{spectral_scales.json}}. S2 uses documented instrument classes; no copied relief or elevation colorbar is manufactured. Diagnostic figures have consistent typography but are explicitly not publication figures. Figures 3 and 4A--B have no valid independent counterparts, so none is invented for style matching.

\paragraph{{Rebuild and audit trail.}}
Run \path{{.venv/bin/python scripts/rebuild_grid_workflow.py}} from the repository root. It checks the existing independent processing checkpoint, rebuilds generic solvers, regenerates grid-derived starts, executes calibration/validation and both relocation attempts where supported, plots saved data and compiles both PDFs. The saved independent waveform-window cache may be reused only with matching input/output hashes; \path{{--remeasure}} recomputes it from recordings. The current procedure does not imply that unfinished full-period acquisition or inference was executed. Controls, own serialized inputs, logs and results are preserved in \path{{data/grid_calibration/run_records.zip}}; machine-readable procedure and scientific outcomes are separate. Earlier models/results remain in Git and their labeled historical directories. The current grid authorization changes input eligibility, not numerical validation requirements.
'''
    text=text.replace(r'\path{f84c9c9dc6bb1501a95a833f6634199a63d4f3b3}',r'\path{f84c9c9d} (full revision in the source receipt)')
    text=text.replace('Older experiments remain below as historical diagnostics.','Earlier experiments are retained separately as historical diagnostics.')
    last=t['runs'][-1]
    if 'error' not in last:
        text+=tex(f"The generic solver originally overwrote earlier clusters' residual tables. The output-only patch appends every cluster; final gaps now use only stations with positive-weight retained residuals. This correction changes the trial gap-passing counts and supersedes the last-cluster-only diagnostics, which are preserved separately. All {last['residual_events']} final output events have residuals represented. The final per-observation RMS is {last['residual_RMS_s']['waveform']:.4f} s for waveform differences and {last['residual_RMS_s']['phase']:.4f} s for picked-phase constraints. Neither value establishes correct event identity or absolute location accuracy.")+'\n'
    text+=r'''
\begin{figure}[H]\centering
\includegraphics[width=.97\linewidth]{figures/grid_calibration_diagnostic.pdf}
\caption{Reproduction diagnostic, not a publication panel. Grid-derived starting and independently fitted layer velocities, exploratory second-round TomoDD locations and the change in depth between rounds. Fixed color limits are 0--5 km; magenta retains deeper results. Calibration path dependence and unreviewed phases prevent interpreting these patterns as recovered faults.}
\end{figure}
'''
    (R/'grid_calibration.tex').write_text(text)
    rows=read(ROOT/'docs/panel_record.json')
    for r in rows:
        if r['status']=='partially reproduced':r['plot_command']='.venv/bin/python scripts/publication_plots.py';r['style_record']='data/grid_calibration/style/plot_inventory.json'
        if r['panel'].startswith(('S6','S7')) or r['panel'].split('/')[0] in ['2A','2B','3','4A','4B']:
            r.update(related_data_command='.venv/bin/python scripts/rebuild_grid_workflow.py',related_saved_data='data/grid_calibration/merged4/summary.json; data/grid_calibration/merged4/validation.json; data/grid_calibration/merged4/tomodd/summary.json',attempt=overview,blocker='Grid input explicitly authorized; historical transformation and averaging masks not recovered exactly. Local calibration convergence passes, full-path precision and start-model dependence do not. Unreviewed phases and sparse coverage; no accepted relocated scientific catalog. '+tomostat)
    for f in ['panel_record.json','panels.json']:write(ROOT/'docs'/f,rows)
    table=[r'\begin{longtable}{>{\raggedright\arraybackslash}p{.12\linewidth}>{\raggedright\arraybackslash}p{.25\linewidth}>{\raggedright\arraybackslash}p{.52\linewidth}}',r'\toprule Panel/view & Quantity & Status, specification and limitation\\\midrule\endhead']
    for r in rows:table.append(' & '.join([tex(r['panel']).replace('/',r'/\allowbreak{}'),tex(r['quantity']),tex(r['status']+'. '+r['documentation']+'. '+r['parameters']+'. '+r['blocker'])])+r'\\[3pt]')
    table.append(r'\bottomrule\end{longtable}');(R/'panels_table.tex').write_text('\n'.join(table)+'\n')
    chain=(R/'partial_panel_chains.tex').read_text();chain=chain.replace('scripts/plot_continuation.py','scripts/publication_plots.py').replace('scripts/plot_calibration_followup.py','scripts/publication_plots.py').replace('scripts/plot_observations.py','scripts/publication_plots.py');(R/'partial_panel_chains.tex').write_text(chain)
    layout=read(R/'figure_layout.json')
    for item in layout:
        if item['figure']=='2':item['missing']='Panels A and B need a validated multiyear relocated catalog and independent magnitudes. The expanded 1,015 associations now enter grid-derived calibration and two TomoDD trials, but path sensitivity and sparse coverage prevent acceptance.'
        if item['figure'] in ['S6','S7']:item['missing']='No validated independent counterpart. Authorized-grid VELEST now runs on the expanded cohort but remains path-sensitive; '+tomostat+'. Diagnostics are retained after the supplement. No rejected locations are presented as reproduced structure.'
        if item['figure'] in ['1','S5']:
            item['caption']=re.sub(r' The color scale.*','',item['caption'])
            item['caption']=item['caption'].replace('extension beyond 2023 shaded. ','')
            item['caption']=re.sub(r' Depth colors(?: run|:).*','',item['caption'])
            item['caption']+=' Depth colors: fixed 0–5 km, red to blue; magenta >5 km, no data clipping. S5 limits/ticks are printed; 1A endpoints are unlabeled and 0–5 km is an explicit approximation. Circle area law is an explicit display assumption, not recovered exactly. Missing magnitudes are crosses. Routine events are external context.'
        if item['figure']=='S1':
            item['caption']=item['caption'].replace('The separately frozen calibration cohort retains its older event identifiers.','Current grid-derived calibration uses this expanded checkpoint. Earlier diagnostics retain separate identifiers.')
            if 'midpoint' not in item['caption']:item['caption']+=' Vertical ticks show observed-interval midpoints where durations are too short to resolve; ticks do not imply continuous coverage.'
        if item['figure']=='S2':item['caption']=item['caption'].split(' Colors distinguish broadband')[0]+' Colors distinguish broadband (red), short period (yellow) and accelerometer (white) instruments; no independent relief raster is available.'
    write(R/'figure_layout.json',layout)
    stages=read(ROOT/'docs/stages.json')
    if stages:
        stages[4]['status']=overview
        stages[5]['status']=tomostat+'. '+tomofacts+'. Independently measured delays; no scientifically accepted relocated catalog.'
        stages[6]['status']='Earlier alternative-model quadrant SVD diagnostics remain historical. No S7 uncertainty from accepted current-grid calibration/relocation; precise regional selection and reviewed phases unresolved.'
        write(ROOT/'docs/stages.json',stages)
    # Preserve exact executed files, including failed trials, outside ignored scratch.
    members={}
    with zipfile.ZipFile(D/'run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for base in ['velest','merged4','tomodd','path_diagnosis','settled_trial','uncertainty']:
            for p in sorted((ROOT/'tmp/grid_calibration'/base).rglob('*')):
                if p.is_file() and p.suffix not in ['.npz']:
                    name=str(p.relative_to(ROOT/'tmp/grid_calibration'));z.write(p,name);members[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    write(D/'run_records.json',members)
    write(D/'current_status.json',dict(summary=overview,calibration_scientifically_accepted=False,tomodd_status=tomostat,panel_counts={status:sum(x['status']==status for x in rows) for status in ['independently reproduced','partially reproduced','not reproduced']}))
    receipts=read(ROOT/'data/calibration_followup/expanded/processed_input_receipts.json');used=set(pd.read_csv(D/'merged4/tomodd/retained_picks.csv').source)
    classification=dict(observations=[r for r in receipts if r['file'] in used],metadata=[dict(file=f'inputs/continuation/{net}_responses.xml',sha256=hashlib.sha256((ROOT/f'inputs/continuation/{net}_responses.xml').read_bytes()).hexdigest(),role='Official response/epoch metadata; sensitivity removal in waveform measurement') for net in ['IV','2I']],
       method_inputs=[dict(file='data/grid_calibration/reference_grid.original',role='Explicitly authorized Tan-distributed reference grid; not independently sourced original 2008 bytes',sha256=g['sha256']),dict(file='docs/tomodd_source_receipt.json',role='Generic method software and mandatory global reference tables; example results excluded')],
       own_outputs=['data/grid_calibration/regional_node_means.csv','data/grid_calibration/merged4/','data/grid_calibration/style/'],
       context='Existing routine catalog and GNSS/leveling inputs remain restricted to labeled context/calibration. No routine values enter the current VELEST/TomoDD runs.',
       published_reference='Local paper/supplement supply written methods. Published image files occur only in the separate comparison document, never empirical plotting inputs.',
       synthetic='No synthetic observations, test fixtures or injected waveforms enter the new calibration, relocation or empirical figure inputs.',
       trace='Raw receipt hashes are inherited from the checked expanded processing manifest; waveform extraction code is differential_times.windows, new measurements are run_grid_tomodd.py, which retains original pick source/time identities. Generic method software and released weights retain their earlier pinned receipts.')
    assert used=={r['file'] for r in classification['observations']}
    write(D/'input_classification.json',classification)
if __name__=='__main__':main()
