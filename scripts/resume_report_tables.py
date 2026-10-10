"""Report actual resumed-run outputs; never infer scientific completion from code."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'data/extended'/name).read_text())
def tex(s):
    return str(s).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%').replace('>',r'$>$').replace('<',r'$<$')
s=load('summary.json');a=load('access_summary.json');d=load('downstream_summary.json');h=load('hybrid_summary.json');v=load('association_validation.json')
(ROOT/'report/resume_numbers.tex').write_text('% All numerical results are read from executed output files.\n')
(ROOT/'report/resume_access.tex').write_text(f"The frozen rebuild snapshot contains {a['rebuild_input_files']} external files ({a['rebuild_input_bytes']:,} bytes). Original and extended processing read {a['waveform_files']} waveform files from {len(a['waveform_stations'])} stations, representing {a['channel_hours']:.3f} channel-hours after unioning overlapping intervals. This is a lower bound on retrieved coverage, not a full-network availability estimate.\n")
(ROOT/'report/resume_results.tex').write_text(f"Extended inference produced {s['picks']:,} merged picks ({s['p_picks']:,} P and {s['s_picks']:,} S). GaMMA provisionally associated {s['assigned_picks']} picks into {s['events']} events. Only {d['calibration_eligible']} events pass the stated geometry screen; none has completed independent VELEST/TomoDD processing. The magnitude attempt measured {d['amplitude_measurements']} channel amplitudes, {d['snr_passing']} above 5 dB, and produced {d['magnitude_edges']} qualifying equations and {d['calibrated_magnitudes']} calibrated magnitudes. Post-association external matching found {d['routine_matches']} unique temporal matches within two seconds; these did not affect event detection or acceptance. The template search scanned {h['intervals']} intervals ({h['valid_hours']:.3f} hours of valid start times), generating {h['candidates']} unconfirmed candidates. Analytic association location error was {v['location_error_km']:.3g} km and origin-time error {v['origin_error_s']:.3g} s.\n")
stages=[
('1. Collection',f"Executed calendar windows and whole-period requests; {len(a['waveform_stations'])} stations retrieved. Full-period chunked download remains unfinished. RAN credentials unavailable."),
('2. Phase picking',f"Executed: {s['picks']} picks; exclusions and merging checked. Full-period inference remains unfinished."),
('3. Training / S3--S4','Retraining not run. STEAD short links return 403; local labels and exact selections/splits missing. Original/retrained inference comparison executed on unlabeled CSOB/CMIS windows, not the exact S4 benchmark.'),
('4. Association',f"Executed: {s['events']} provisional events with an alternative external profile. Exact cited numerical starting profile missing; no author event seeds."),
('5. VELEST',f"Generic software compiled. {d['calibration_eligible']} geometry-screened candidates do not resolve the chosen layered model/corrections; inversion not run."),
('6. TomoDD','Not run. Independent calibrated input catalog and complete differential-time/configuration workflow missing.'),
('7. HypoDD SVD','Not run. Depends on independently relocated regional subsets and fitted model; generic software source accessible.'),
('8. Magnitudes',f"Measurements executed; {d['magnitude_edges']} qualifying pair equations, {d['calibrated_magnitudes']} calibrated magnitudes. Routine Md permission is resolved."),
('9. Completeness / b','Not calculated: no independently calibrated magnitude sample.'),
('10. Focal mechanisms','Not run. Reviewed polarities, calibrated locations/model and gCAP configuration missing. Generic software accessible. Data S3 row-count discrepancy resolved.'),
('11. Location checks','Residuals, gaps and internal S--P checks executed. Zero associated CPOZ P arrivals; relocated sector gathers, manual deep-event review and SVD validation unfinished.'),
('12. Hybrid search',f"Executed on {h['valid_hours']:.3f} available hours; {h['candidates']} unconfirmed candidates. Three-year classification, clustering and catalog-wide FI review unfinished."),
('13. Historical context','Executed original leveling-table extraction (128 entries) and external routine-catalog context. Original RITE GNSS processed through 2019 with explicit overlap alignment; daily 2020--2023 continuation missing.')]
lines=[r'\begin{longtable}{p{.20\linewidth}p{.73\linewidth}}',r'\toprule Stage & Actual execution and limitation\\\midrule\endhead']
lines += [tex(k)+' & '+tex(val)+r'\\[4pt]' for k,val in stages]
lines += [r'\bottomrule\end{longtable}']
(ROOT/'report/stages_table.tex').write_text('\n'.join(lines)+'\n')
(ROOT/'docs/stages.json').write_text(json.dumps([dict(stage=k,status=val) for k,val in stages],indent=2)+'\n')
