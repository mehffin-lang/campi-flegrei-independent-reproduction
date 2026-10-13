# Local observations and focal-mechanism continuation

Executed 13 October 2026 from commit `f03a1912ccbeab4bee3d34c00136aa8218fb0e86`.
This is numerical progress, not an accepted reproduction of the fault geometry or mechanisms.
The readable local paper and supplement remain the specification. No Tan event result, pick,
fitted model, mechanism or plotted numerical array entered this continuation.

## What ran

- **Bounded acquisition:** `scripts/collect_continuous.py run --workers 4 --max-jobs 20`
  selected only `pending` requests with `attempts=0`. Nineteen readable downloads and one
  HTTP 204; no failed or repeated requests. The four half-hour CAAM requests cover
  29 January 2022 10:00–12:00 UTC. Nine other stations returned six-hour 06:00–12:00
  records; CPIS returned empty. Six stations returned 12:00–18:00 records.
  The frozen ledger lists each station, request, observed interval, hash and outcome.
- **Omitted observations:** all 14 local files identified for this continuation entered
  PhaseNet: six CAAM/COLB template records, seven local-archive fragments and the CSOB
  benchmark trace. Their event-selected windows are explicitly labeled and are not
  unbiased discovery exposure. All 19 new downloads also entered inference.
- **Current combined set:** 1,024 original files, 30 station names, 87 channels,
  8,952.452 union channel-hours; 136,376 picks (20,022 P / 116,354 S), 7,416 associated
  picks, 1,024 provisional events. These are 859 current per-file inference jobs plus
  165 previously independently processed files whose saved picks/coverage are reused.
  Unchanged current inference caches and own daily associations are reused only after
  their input/model/settings checks. Reuse is not reported as fresh inference.
- **Calibration and downstream:** 921 causal events, 38 numerical calibration candidates,
  219 VELEST filter passes, both fixed-grid TomoDD rounds, 123 retained relocated events,
  80 conditional SVD estimates, 67 provisional amplitude magnitudes, 122 CPOZ component
  traces and 383 S–P pairs. All nine requested stages exited zero.
  The new association at 2022-01-29 06:26:03.080 UTC (new ID 175) has only 1 P / 5 S;
  its first three VELEST RMS values are 0.44/0.45/0.46 s. Residual rejection removes it
  before pass 4. Thus the added data yield **no additional retained relocated event**.
- **Mechanisms:** 180 station-event records from 8 frozen candidates were inspected by
  the AI, including all 13 extra stations for event 649. Saved decisions retain 29
  first motions and 41 S/P measurements, with rejection reasons. **Human review count
  is zero.** The additional CFMN649 P onset, read from the original trace, is
  2025-03-20 06:32:18.910 UTC (about 0.03 s reading uncertainty).
- **SKHASH 1.1.5:** executed with unchanged minimum-eight-polarity, 90° azimuth-gap,
  60° plunge-gap settings. Seven candidates lack eight reliable polarities. Event649
  reaches eight but its SKHASH gap is 96.57°. Zero solutions.
- **FK/gCAP:** official generic FK3.3 and a disclosed, separately named generic gCAP
  port compiled and ran for seven events in each of two bands. Event698 has only one
  reviewed three-component packet and does not meet the declared four-station trial
  selection. Each band produced 360 Green-function components and seven finite fits.
  Low/high-band variance reduction is 3.9–14.8% / 2.3–7.1%; the double-couple orientation
  changes by 34.2–97.9°. **All mechanisms remain unaccepted.**

The number of files in `input_jobs.json` is not the complete combined file count.
`all_observation_inputs.json` covers all 1,024 inputs, including the reused baseline.
`local_input_check.json` confirms no physical miniSEED file under `inputs/` is absent
from the combined processed-coverage table. Some fragments produce no finite model
scores; processed sample hours are not claimed as complete three-component inference
exposure. Ten picks without verified location metadata are retained separately and
not passed to association.

## Evidence and provenance

| Evidence | Path |
|---|---|
| Original observations, source URLs and hashes | `data/local_extension/all_observation_inputs.json` |
| Current jobs and original-window selection roles | `data/local_extension/input_jobs.json`, `short_window_inputs.json` |
| New inference receipts (20 then 13 files) | `data/local_extension/inference_local_batch.json`, `inference_last_run.json` |
| Actual sample coverage / gaps / responses | `data/local_extension/processed_coverage.csv`, `station_coverage.csv`, `unobserved_channel_intervals.csv`, `response_coverage.csv` |
| Frozen request status and monthly ledger | `data/local_extension/request_ledger.csv.gz`, `request_station_month.csv`, `acquisition.sqlite.gz` |
| Missing association metadata | `data/local_extension/picks_without_metadata.csv` |
| Picks, association and execution | `data/local_extension/picks.csv`, `associations.csv`, `initial_events.csv`, `execution.json` |
| VELEST model, filter outputs and validation | `data/local_extension/calibration/merged4/` |
| Both TomoDD rounds / SVD / magnitudes / location checks | `data/local_extension/calibration/merged4/{tomodd,uncertainty,magnitude,location_checks}/` |
| Actual serialized controls, inputs, residuals and logs | `data/local_extension/calibration/run_records.zip`, `run_records.json` |
| Frozen candidates and comparison to new numbering | `data/coverage_extension/calibration/merged4/uncertainty/relocated_events.csv`, `data/local_extension/cohort_comparison.json` |
| Measurement provenance and waveform arrays | `data/mechanism_followup/input_provenance.json`, `measurements.csv`, `review_waveforms.npz`, `unpicked_waveforms.npz` |
| AI review decisions and images | `config/mechanism_visual_decisions.json`, `config/mechanism_review_arrivals.csv`, `data/mechanism_followup/review_decisions.csv`, `review/` |
| SKHASH inputs and zero-solution log | `data/mechanism_followup/{polarities.csv,sp_ratios.csv,control.txt,skhash.log,solutions.csv}` |
| Every candidate's unmet requirements | `data/mechanism_followup/candidate_requirements.csv` |
| gCAP fits, controls, station measurements, logs, observed and predicted SAC arrays | `data/mechanism_followup/gcap/`, `gcap_1_5/`, their `run_records.zip` archives |
| Frequency sensitivity and numerical checks | `data/mechanism_followup/gcap_band_sensitivity.csv`, `validation.json`, `gcap_numerical_check.json` |
| Figure source/output hashes and style choices | `data/mechanism_followup/plot_inventory.json` |
| All 63 panel/view records | `docs/panel_record.json` |

These directories contain independently computed results, not necessarily scientifically
accepted results. Mechanism event IDs refer to `data/coverage_extension`, while new location
IDs refer to `data/local_extension`; they must never be joined by integer ID.
The plots do not combine counts from overlapping cohorts.

**Permitted method inputs:** released retrained PhaseNet weights; generic GaMMA, VELEST,
TomoDD, HypoDD, SKHASH, FK and gCAP; the explicitly authorized Tan-distributed,
Battaglia-attributed starting grid. Its original bytes remain at
`data/grid_calibration/reference_grid.original`, SHA-256
`dc36fe2a542fc7a3b6c473c48ec109c53ddd77a1721f509b920fea97fb0166f3`.
Axes are 23 longitude × 14 latitude × 27 depth nodes, longitude fastest, degrees east/north,
depth km below sea level; Vp km/s and a dimensionless Vp/Vs volume. Padding and the discrepancy
with the written 18×18×9 km / 0.5 km model description remain disclosed. This authorization
does not establish an independently retrieved original 2008 grid or the unknown historical
transformation. Own regional averages and fits, never Tan's fitted profiles, enter the trials.

**FK/gCAP resources:** the official sources are
`https://www.eas.slu.edu/People/LZhu/downloads/fk3.3.tar` and
`https://www.eas.slu.edu/People/LZhu/downloads/gcap1.0.tar`.
`method_resources.json` records archive versions, checksums, complete listings and the limited
method-source member list extracted. Examples, example results, prebuilt binaries and plotting
scripts were not extracted or used. Compiling FK requires fixed-form unlimited line length.
The generic gCAP source required unavailable Numerical Recipes/SAC functions. The separately
named port uses an independently written 3×3 Jacobi curvature eigensolver and prefilters data
and Green functions externally; its grid search and radiation calculations are generic method
code, not Tan's analysis code. This filtering order differs from stock segment filtering.
Only our patch/build recipe is committed; downloaded method source remains under ignored
`inputs/` and `build/`. No redistribution of the original gCAP source is implied.

The fixed-matrix eigenvalue and rotation checks are isolated software assertions. FK Green
functions are theoretical predictions required by waveform inversion, never synthetic
observations. Observed/predicted pairs share one observed-peak normalization in the diagnostic.
Published reference images remain confined to the separate comparison PDF. No reference
pixels or released result tables enter the new analysis or scientific paper.

## Validation and unresolved requirements

- **Calibration:** full precision paths differ by 558 m horizontally / 0.89 km in depth;
  regional starts differ by 1.04 km in depth. Identical converged starts give identical
  printed coordinates, which does not erase the nonlinear path dependence. The prior
  held-out/instrumented diagnosis was preserved, not rerun or claimed as new validation.
- **Relocation:** 398 shared CC observations improve RMS 0.04125→0.03940 s; 4,367 shared
  picked differences improve 0.10738→0.10130 s. Maximum round-to-round movement is
  386 m / 0.372 km. Thirty-four retained events have zero CC links. No event has >100
  correlated phases, so S9 still has no qualifying numerical sample.
- **Mechanisms:** candidate-specific requirements are in `candidate_requirements.csv`.
  Seven require additional reliable first motions; 649 needs suitable coverage in the
  remaining azimuth sector. Existing broad records contain ambiguous onsets; they were
  inspected, not equated with usable measurements. Accepted gCAP interpretation also
  requires reliable locations/model, independently defensible windows and stable fits.
  The two executed bands do not supply those conditions. The AI review should not be
  described as human scientific review. No SKHASH–gCAP angle exists without SKHASH output.
- **Waveform coverage:** 842 downloaded, 36 empty, 11 failed and 73,917 pending requests.
  Pending acquisition is unfinished work, not demonstrated remote inaccessibility.
  RAN waveform credentials remain unavailable; official metadata alone do not supply
  its accelerometer traces. Responses are absent for four short intervals, totaling
  0.0667 channel-hours. Full network coverage is not claimed.
- **Exact method:** the Calò–Tramelli2018 starting profile is still unavailable; the
  cited Tramelli2021 profile supports explicitly provisional association. It did not
  block the present calibration, relocation or mechanism attempts. No contact or data
  request was made or drafted.

The SVD uncertainties are conditional on selected phases/model and explicit alternative
quadrants. Magnitude completeness and b describe a selected sample; they do not recover a
multiyear population. The 0.2–2 Hz and 1–5 Hz gCAP trials use own four-layer locations/model,
fixed source depths, a flat receiver surface at −0.5 km bsl, FK density/Q defaults, a 0.2 s
source pulse and a 10° double-couple grid. Exact phase-window, filter, topography and
event-selection settings are not asserted to reproduce the authors' undocumented controls.
The original method's 74-event selection is not the present eight-candidate selection.

## Run and rebuild

Use the repository root, Python3.11 `.venv`, generic solvers and the isolated
`.venv-skhash` environment already documented in `docs/GRID_WORKFLOW.md` and
`docs/PROVISIONAL_CONTINUATION.md`. Dependency caches remain at the preexisting user pip
cache; all new project inputs, processing caches, outputs and temporary records are inside
this repository.

```bash
# Current saved-results rebuild; no waveform request or scientific refitting.
.venv/bin/python scripts/rebuild_local_followup.py

# Document correction only: first verify every saved plot's data/output hashes.
.venv/bin/python scripts/rebuild_local_followup.py --reuse-plots

# Optional complete continuation replay from the frozen available observations.
# Retains measured AI review decisions; reuses only compatible inference caches.
# Generic method archives are retrieved only if absent, with fixed checksums.
.venv/bin/python scripts/rebuild_local_followup.py --analysis
```

The analysis sequence is `process_local_followup.py --frozen`, `audit_continuation.py`,
`acquisition_ledger.py`, `calibrate_local_followup.py`, `prepare_mechanism_software.py`,
`mechanism_measurements.py`, `run_reviewed_skhash.py`, `run_gcap_followup.py`,
`run_gcap_followup.py --high-band`, and `validate_mechanism_followup.py`, followed by
`plot_local_followup.py`, `local_followup_report.py`, and `build_documents.py --clean`.
Those scientific stages actually ran in this continuation; `execution.json` and the
per-method execution logs record outcomes. The aggregate default command is separately
run and recorded in `data/local_extension/rebuild_result.json`. It must not be described
as a second uncached raw-waveform rerun. Ordinary frozen replay does not rerun independent
visual review or automatically accept a solution.

The first presentation build compiled but failed its figure-order assertion: a text
replacement had removed the main-paper inputs for Figures 3 and 4. Those inputs were
restored and the replacement restricted to one source paragraph. No numerical result
or plotted values changed. The corrected document rebuild verifies the existing plot
hashes with `--reuse-plots`; the prior successful rendering stage is retained in its log.

Local observations are deliberately uncommitted. Restore their exact paths from the
combined input manifest and source URLs; local event-selected fragments also have original
archive/member receipts in `docs/local_waveform_receipts.json`. Restore old context/response
bundles using `docs/GRID_WORKFLOW.md`; retain the trained artifact checksums. The downloaded
observations may be revised by the provider: a checksum mismatch requires inspection, not
silent substitution. `source_revision.json` preserves the exact executed picking-driver
source and explains the subsequent addition of `--frozen` without changing the algorithm.

## Replaced presentation and preserved work

The current report and comparison replace earlier displayed Figures 2, 3, S6, S7, S8,
S10, S11, S12 and S13 with the new `figures/*_local_followup.pdf` outputs. S1 now uses
`figures/coverage_local_followup.pdf`. The blank F4 comparison is replaced by actual
unvalidated trial fits in `figures/figure_4_followup.pdf`. The new waveform-fit diagnostic
appears only in post-supplement documentation, never as a publication counterpart.
Old `*_provisional.pdf` and `*_extension.pdf` files and their numerical cohorts remain
archived; they are no longer the current figure selection. Historical audit sections
retain their original counts with explicit old-cohort labels.

Updated sources include `report/report.tex`, `main_paper.tex`, `reproduced_supplement.tex`,
`reproduction_documentation.tex`, `grid_narrative.tex`, `figure_layout.json`, the panel
table/chains, generated figure sections, and comparison pages. New detailed text is
`report/local_followup.tex`. Both PDFs remain provisional; no panel is fully reproduced.
There are **50 partial panel/views and 13 unreproduced**: S3A–D, S4B, all three S9 views,
S11 swarms1/3/4, S14/unclustered and S15D. Other historical, training and hybrid analyses
were not silently rerun or promoted to completion by this targeted continuation.

The corrected build passed: 54 report pages, 19 comparison pages, publication figure/section order verified, 63 panel/view records with existing saved numerical paths, 12 new plot records with matching input/output hashes. Published images are absent from the scientific report. Figure3/4 report and comparison pages and the mechanism diagnostic were visually inspected. See `data/local_extension/delivery_verification.json` and `report/document_build.json`.
