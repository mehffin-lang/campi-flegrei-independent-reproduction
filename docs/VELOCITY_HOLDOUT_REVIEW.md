# Independent velocity tests, 15 October 2026

No profile is validated. This continuation starts from commit `6e532df` and
preserves the earlier catalog, models, panels and failed tests. It runs three
predeclared parameterizations, six sensitivity variants each, and one separate
training-only exclusion check. All use original EIDA observations processed
within this project. No author event solution, fitted model or figure value is
an analysis input. Background downloads remain outside this frozen experiment.

## Inputs, selection and validation

- Observations: `data/availability_extension/catalog_december/picks.csv`,
  `associations.csv`, `stations.csv`, and `selection/selected_initial_events.csv`.
  Their parent waveform hashes are in `input_jobs.json` and
  `all_observation_inputs.json` in that directory. The permitted trained weights
  and waveform processing are recorded in its `processing_checkpoint.json`.
- Prior selection and residuals: `data/availability_extension/velocity_december/`.
  The new `data/velocity_holdout_review/frozen_holdout.cnv` is **identical** to
  the previous 2025 holdout input, including phase weights and initial locations.
- Calibration pool: 490 pre-2025 events; 464 are on 20 May 2024. The previous
  balanced fit used 46 events / 709 arrivals. The new primary subset uses 52
  events / 827 arrivals, with 62 / 990 in the selection sensitivity. It samples
  every available training day and provisional 1-km depth bin, supplementing
  rare training station/phase pairs where possible. These are provisional
  association depths, not known source depths.
- All 62 eligible 2025 events / 1,065 arrivals remain held out. They occur on
  1 January, 1 February and 18–20 March. No held-out arrival enters model or
  station-delay fitting. Holdout locations and origin times are nuisance fits;
  these scores test conditional travel-time prediction, not absolute accuracy.
- The already inspected holdout informed the diagnostic design. It is an
  unchanged **reused validation set**, not a previously unseen final test.
  All registered trials are reported; none was selected by hiding failures.
- `experiment_plan.json` records the specification and input/code hashes before
  fits. `training_cap5.csv`, `training_cap8.csv` and the corresponding CNVs retain
  exact selections. Their inherited `role` column describes the parent
  experiment; membership in these new training files defines the present fit.
  `summary.json`, `experiment_results.csv`, and native run
  evidence retain every outcome. `preflight_serialization_failure.log` records a
  tuple/list registration-check defect caught before any scientific run; its
  correction changed serialization comparison only.

## Model choices

The four-layer initialization is Tramelli et al. (2021), Table 1, DOI
10.1038/s41598-021-86506-6, extended to -0.5 km at the surface and truncated to a
halfspace below 3 km. It is an explicit alternative, **not Calò–Tramelli (2018)**.
The three-layer initialization merges the upper layers to 1.8 km/s: the
travel-time-weighted average across their 1 and 0.5 km thicknesses is 1.789 km/s,
rounded to the stated display/initialization choice. Other initial Vp values
are 3 and 5.5 km/s. Initial Vs=Vp/1.78; both P and S velocities then float.

Families are four layers with damped delays, three layers with damped delays,
and three layers with delays fixed at zero. The latter is a restrictive
alternative to Tan's joint calibration, not an assertion that actual station
delays vanish. Delay damping is 10 rather than the former 0.1; this damps updates,
not a Bayesian prior or a hard bound on the final correction. Layer damping is
10. The origin/horizontal/depth/velocity damping is 0.01/0.1/0.1/1; P/S weights
are 1/0.5. Maximum depth and velocity updates remain 0.2 km and 0.1 km/s.
Reference P delay remains fixed at IV.CSOB. No low-velocity layers are allowed.

Each family tests ±5% initial speeds, 52 versus 62 training events, 10× velocity
damping, 32-/64-bit precision, and additional iterations. Runs use 21 fixed
prelocation iterations, 14 velocity-only iterations and five 14-iteration joint
blocks. The third versus fifth blocks test convergence. Holdout scores use 35
location-only iterations; a second 35-iteration pass checks location stability.
The original 100 m horizontal / 0.1 km depth / 0.05 km/s velocity / 0.02 s delay
gates are unchanged. Improved holdout prediction and physical velocity checks
remain necessary. No family passes all requirements.

Tan's written method is in `tanmodelsupp.pdf`, pages S4–S5. Generic software
guidance is `inputs/extended/velest_guide.pdf`, especially the minimum-1D-model
and damping discussion. Generic VELEST binaries and their hashes are recorded
per run. Source code is `build/velest-sparse.f`; no Tan analysis code is used.

## What the tests establish

| Base trial | Train RMS, initial → fit (s) | Holdout RMS, initial → fit (s) | Status |
|---|---:|---:|---|
| Four layers, damped delays | 0.2166 → 0.1778 | 0.2406 → 0.2416 | Not validated |
| Three layers, damped delays | 0.2169 → 0.1801 | 0.2432 → 0.2413 | Not validated |
| Three layers, zero delays | 0.2169 → 0.2118 | 0.2432 → 0.2274 | Not validated |

For the previous fit, unsupported station/phase pairs explain 74.7% of the net
added squared error; supported pairs explain 25.3%. The zero-delay trial improves
both groups (893 represented arrivals: 0.2376 → 0.2219 s; 172 unrepresented:
0.2705 → 0.2541 s). Its six sensitivities have holdout RMS 0.2252–0.2309 s, but
depths change by up to 1.58 km, horizontal positions by 800 m, and velocities by
0.28 km/s. Its printed 32-/64-bit results agree; that does not eliminate
initialization or selection sensitivity. Another holdout location pass moves
event 2403 from 3.00 to 2.18 km. Four held-out events move over 100 m horizontally
and seven over 0.1 km vertically. The poorer depth stability is not waived because
aggregate residuals improve.

The three-layer zero-delay base profile is saved in
`three_zero_delays_base_profile.csv`: layer tops [-0.5,1,3] km bsl,
Vp [1.77,2.86,5.41] km/s and Vs [0.96,1.82,3.29] km/s. This is a **provisional
fit**, not an accepted replacement for any downstream model. Model spread is a
sensitivity range, not a confidence interval. No absolute-depth validation or
new relocation, magnitude or mechanism is claimed.

## Waveform and ray review

`review/decisions.csv` documents AI visual review of 24 original three-component
windows: 18 ambiguous and six onset-consistent, with no arrival edits. All 72
reviewed channels have one matching epoch and a response in the saved StationXML.
Classifier probability is not phase correctness. `review/network_decisions.json`
records four network gathers; no human review is claimed. A separate sensitivity
omits only training event 1532, whose assigned P arrivals lie in an existing
decaying packet. This is not proof of a false event. Its 51-event fit gives
holdout RMS 0.2287 s, but further iterations still change depth by 0.57 km and
horizontal position by 245 m. **No holdout event was excluded.**

Per-phase native ray vertices are matched to CNV tokens and independently
summed in `*_rays.csv`. For the zero-delay trial, the ≥3 km layer is crossed by
80/366 training P and 115/461 training S rays, versus 223/415 and 347/650 held-out
rays. Source depths are conditional on the provisional model. The aggregate
native two-model ray table is inconsistent (e.g. 86 sources in the previous
46-event fit), so it is not used. This is a final statistics-output problem;
the assessment uses per-ray vertices and the actual model files. Travel-time
checks from rounded vertices differ by RMS 0.0038–0.0075 s from saved residual
predictions; exact agreement is not expected from 0.01-km/0.01-s serialized
coordinates/times and 0.01-km/s velocities. See `ray_consistency.json`.

## What is still needed

- Review training phase identities and associations, including event 1532,
  before treating the fitted profile as a physical velocity estimate. Several
  coherent events also contain questionable individual onsets; discarding
  entire difficult events on residual alone would be unjustified.
- Obtain or identify qualified, coincident pre-2025 arrivals for the absent
  training pairs: CGAU P/S, CLAC S, CREM P/S, CSOC P/S, CRUS P/S and CUMA P/S.
  Their exact networks and holdout counts are in `missing_training_pairs.csv`.
  For the 2I stations, saved EIDA availability advertises late-2024 HH records;
  StationXML station epochs can begin earlier and do not establish waveform
  availability. The already processed 1 December six-hour window produced no
  event meeting this project's calibration screen.
- Improve independent geometry/depth constraints and ray sampling around and
  below the 3-km interface. The current association depth distribution differs
  between training and holdout. The number of additional events needed cannot
  be established from these runs.
- An expert-reviewed holdout version, if later made, must be retained separately
  and evaluated alongside this frozen test. A new untouched time block would
  be needed for a genuinely new final prediction test after model selection.

RAN and the exact Calò–Tramelli profile were not requested or pursued. Their
absence did not prevent these tests. No new background waveform enters the
experiment without future picking, association, quality checks and a versioned
data split. The existing collector/picker remain separate. Automatic watcher
PID 3325726 was stopped to prevent an old fitting/report recipe overwriting this
assessment; collection and picking were preserved.

## Rebuild and exact evidence

From the repository root, using the existing `.venv` and generic VELEST build:

```bash
# Verify saved observations/results, regenerate diagnostics and both PDFs:
.venv/bin/python scripts/rebuild_velocity_holdout.py

# Independently refit the registered cases, preserving the previous summary
# and native run archive, then repeat validation and document generation:
.venv/bin/python scripts/rebuild_velocity_holdout.py --fit
```

The detailed commands already executed were:

```bash
.venv/bin/python scripts/diagnose_velocity_holdout.py
.venv/bin/python scripts/test_velocity_parameterizations.py --prepare
.venv/bin/python scripts/test_velocity_parameterizations.py --run
.venv/bin/python scripts/analyze_velocity_holdout.py --ablations
.venv/bin/python scripts/review_velocity_unstable_events.py
.venv/bin/python scripts/check_velocity_review_exclusion.py
.venv/bin/python scripts/rebuild_velocity_holdout.py
```

`--prepare` freezes a new plan; do not use it to overwrite a different historical
experiment. Default rebuilding does not infer or relabel visual-review decisions.
Those are saved assessments, not automatically generated reference labels.
The wrapper restores the prior December run archive and this project's own
`solver_evidence.tar.gz` if native
working files are absent. Original waveform inputs must be restored using
`docs/AVAILABILITY_EXTENSION.md` for raw-window regeneration. Models and
residuals need only the frozen own arrival files and station metadata.

Evidence resides in `data/velocity_holdout_review/`; all model, arrival,
station-correction, residual, per-ray, selection and decision files are retained.
`solver_evidence.json` gives the native archive checksum. The archive contains
only our run inputs/outputs and logs. Diagnostic figures are
`figures/velocity_holdout_diagnostic.pdf` and `figures/velocity_ray_coverage.pdf`.
They appear only after the reproduced supplement, not as reproduced paper
panels or in the comparison PDF. Existing panel counts/statuses remain unchanged.
`rebuild_result.json` records compilation and protected-file checks.

The existing `report/report.tex`/`report/report.pdf` and
`report/comparison.tex`/`report/comparison.pdf` remain the deliverables. The new
supporting source is `report/velocity_holdout_review.tex`. Earlier failed model
records and empirical figure data were preserved. No standard dependency cache
location changed; project-specific files remain inside this repository.
