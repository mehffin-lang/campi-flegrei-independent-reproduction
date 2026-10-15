# Synchronized figures and training-arrival review, 15 October 2026

This bounded continuation starts at commit `537742c`. Its versioned record is
`data/velocity_holdout_review/sync_training_review_20261015/` (D below).
Previous velocity experiments and publication-panel numerical files are preserved.
There is no full workflow rerun, broad EIDA collection, author-derived input,
synthetic observation, RAN request, or contact with an outside party.

## PDF synchronization

The initial PDFs matched their saved `report/document_build.json` hashes.
`report/figure_layout.json` supplies the same 20 generated figure files to both
PDFs. `docs/panel_record.json` supplies 63 statuses: 53 partial and ten not
reproduced. The builder checks this mapping against the LaTeX fragments, the
actual compiler input records, and all 19 comparison pages. It now saves every
panel's numerical-file hashes, shared figure hash, status, commands, and UTC PDF
file timestamps. Missing parts of combined figures remain missing, not generated
results. These checks establish document agreement, not scientific validation.

The first synchronized build is saved in `D/initial_pdf_sync.json`.
All comparison pages and the report's main/supplementary figure pages were
visually inspected. Published figures occur only in the separate comparison,
clearly labeled “Published reference.” The numerical inputs were not regenerated.
The report's new velocity review follows the supplement. Earlier experiments are
retained with checkpoint labels. The latest build manifest records the final PDF
hashes and times after that update.

## Observations and reviewed training data

Local coverage was checked in `D/pre2025_stored_intervals.csv` and
`D/local_target_coverage.csv`. The six target stations already had December 12
and 19 observations; the four 2I stations and CUMA also had December 1 data.
CRUS has no advertised December 1 coverage. Target availability starts in
July--November 2024, after most selected training events.

The additional window is December 13, 2024, 00:00--02:00 UTC: the next calendar
day after the previous December 12 window, chosen without event or holdout
information. Only six available, locally missing requests were retrieved, with
two transfers at a time. Estimated size was 20,519,430 bytes; actual size is
20,906,496 bytes, with 36 core channel-hours. Transfer context is excluded from
that duration. Every request succeeded. The 40 GiB free-space reserve plus 8 GiB
processing allowance remained protected; no backlog request was started.
`D/availability/`, `D/receipts/`, `D/request_ledger.csv`, `D/coverage_ledger.csv`
and `D/download_plan.json` give exact channels, epochs, URLs, sizes and hashes.
These two-hour successes do not mark any entire six-hour backlog request complete.

All six headers have valid metadata epochs, responses, coordinates and sampling
rates. Absolute clocks were not independently checked. Released PhaseNet weights
are permitted method resources, identified by their hashes in
`D/catalog_dec13/summary.json`; the previous preprocessing and alternative GaMMA
profile are unchanged. Processing gives 163 P and 922 S picks, **zero
associations**, and therefore no newly admitted calibration arrivals. CUMA
produces zero picks. This is a six-station sample, not evidence of absent
earthquakes or catalog completeness. Other publicly advertised intervals remain
unretrieved; lack of usable phases in this window is not an access failure.

Six previously flagged training arrivals were reviewed in enlarged original raw
and 1--20 Hz display windows. CFMN P/event159, CMSN S/265, CFMN S/264, and CSFT P,
CPOZ S and CFMN S/1055 remain uncertain. Their times were not changed or forced;
they are excluded only from the new training experiment. Network review also
leaves event1532's distinct-event interpretation unresolved: several assigned
P picks lie in an earlier decaying packet. It is excluded as uncertain, not
declared false. Original data and previous results remain intact.

`D/reviewed_arrivals.csv`, `D/reviewed_events.json` and `D/review/` contain the
decisions, numerical windows, original-file hashes, plots and metadata checks.
These are **Codex visual reviews, not independent human seismologist validation**.
The 18 enlarged-window and 85 network-gather metadata rows have matching epochs,
responses and rates. No 2025 waveform was reviewed. Other inherited training
arrivals were not all reviewed anew.

The unchanged event screen then excludes event159; the primary set becomes
51 events/816 arrivals, and the selection sensitivity 62/997.
`D/training_catalog/selection/input_quality.csv` records the actual gates.
Seven target station/phase combinations still have just one observation each;
CSOC P/S and CUMA P/S remain absent (`D/training_gap_counts.csv`).

## Numerical diagnosis and tests

`D/saved_precision_inputs.json` verifies identical initial arrivals, model,
station file and controls for the earlier 32/64-bit trials. Iteration-zero RMS
differs by about 2 microseconds; later location paths diverge, including near
the 3 km interface. `D/saved_precision_diagnosis.csv` and
`D/saved_precision_iteration_rms.csv` distinguish stages and event IDs. This
rules out a detected setup mismatch, but does not isolate the exact ray-branch
cause for this cohort. Depth and station-delay tradeoffs remain plausible
contributors, rather than a proven exclusive cause.

The native source has uninitialized local `nofreadp`/`nofreads` counters in
`ACTUALSTATIONS`. Their only uses are accumulation and diagnostic printing;
they do not enter the inversion equations. The source hash and excerpt are in
`D/native_count_diagnostic.json` and `D/native_count_excerpt.txt`. Input-token
and per-ray counts are used instead. No solver equation or binary was changed.

The three previously declared layer parameterizations and all six sensitivities
are retained. Layer boundaries, P/S weights 1/0.5, initial Vp/Vs 1.78, damping,
iteration schedule, and thresholds are recorded in `D/plan.json` and
`D/fits/plan.json`. The new fit uses only the reviewed pre-2025 training table.
No profile is chosen by its 2025 score. All 18 training fits were complete and
hash-frozen before the separate validation stage. The 62-event/1,065-arrival
holdout bytes, phases, weights and membership remain unchanged.

As before, evaluation refits held-out locations and origins with velocities and
station delays fixed: conditional arrival prediction, not absolute-location
truth. This previously examined validation set is not a pristine blind test.
Acceptance still requires improved holdout RMS relative to initialization and
the original baseline, physical velocities, convergence, and sensitivity within
100 m horizontally, 0.1 km depth, 0.05 km/s velocity and 0.02 s station delay.
No threshold was relaxed. Results and individual gates are in
`D/experiment_results.csv`, `D/acceptance_checks.csv`, `D/sensitivity_results.csv`,
and `D/fits/validation_summary.json`.

All 18 trials completed, but **no profile passed all criteria**. Base results:

| Parameterization | Training RMS, initial → fitted (s) | 2025 RMS, initial → fitted (s) | Maximum depth sensitivity (km) |
|---|---:|---:|---:|
| Four layers, fitted delays | 0.20395 → 0.15840 | 0.24062 → 0.24316 | 1.65 |
| Three layers, fitted delays | 0.20444 → 0.16033 | 0.24324 → 0.24459 | 1.00 |
| Three layers, zero delays | 0.20444 → 0.19808 | 0.24324 → 0.22707 | 1.09 |

All base profiles pass the velocity plausibility checks but fail iteration and
held-out-location convergence. The zero-delay case moves by 889 m horizontally
and 0.56 km in depth under additional training iterations; its maximum
cross-variant changes are 733 m, 1.09 km and 0.32 km/s. Training RMS on a changed
observation set is not directly comparable as evidence of improved predictive
accuracy. Removing uncertain arrivals has not established stability.

The zero-delay base has 53/363 P and 77/453 S paths strictly below 3 km, from
nine model-estimated deep sources. The preceding December 12 event lies between
2.70 and 3.06 km across fits; its apparent deep contribution is model-dependent.
Layerwise travel-time sums agree with serialized residuals to 0.0050–0.0083 s RMS,
subject to native output rounding. This checks arithmetic, not phase truth.

Still needed: clear pre-2025 CSOC/CUMA P and S onsets recorded jointly with the
established network; repeated events for the seven singly represented target
station/phase pairs; further scientific review of coda associations and
interface-sensitive events; and additional independent deep-path constraints.
The required number of events is not established. Public intervals remain
available for later targeted work, not exhausted. The exact Calò–Tramelli profile
was not sought and cannot be assumed to resolve these observation and stability
problems. No fitted profile is labeled as that published model, and no new fit
is promoted into Figures 2–4 or S6.

## Commands and preservation

Use the repository's existing `.venv`, pinned trained weights, and generic VELEST
builds. Large raw waveforms remain in
`inputs/velocity_holdout_review/sync_training_review_20261015/`; exact retrieval
URLs, placement paths and checksums are in D. Native run files and logs are in
`tmp/velocity_holdout_review/sync_training_review_20261015/`, with a compressed
evidence copy under D. All project outputs remain inside the checkout. The
standard Matplotlib user cache remains `/home/mehffin/.cache/matplotlib`.

Executed sequence:

```sh
.venv/bin/python scripts/build_documents.py --clean
.venv/bin/python scripts/advance_velocity_review.py plan
.venv/bin/python scripts/advance_velocity_review.py query
.venv/bin/python scripts/advance_velocity_review.py retrieve
.venv/bin/python scripts/advance_velocity_review.py review
VELOCITY_REVIEW_VERSION=sync_training_review_20261015 .venv/bin/python scripts/review_target_training.py --events 1532,1055 --tag inherited_network
VELOCITY_REVIEW_VERSION=sync_training_review_20261015 .venv/bin/python scripts/check_target_metadata.py
VELOCITY_REVIEW_VERSION=sync_training_review_20261015 .venv/bin/python scripts/process_target_training.py --tag catalog_dec13 --day 2024-12-13
# Recorded visual decisions are the versioned reviewed_arrivals.csv/reviewed_events.json.
.venv/bin/python scripts/advance_velocity_review.py diagnose
.venv/bin/python scripts/advance_velocity_review.py prepare
.venv/bin/python scripts/advance_velocity_review.py fit
.venv/bin/python scripts/advance_velocity_review.py validate
VELOCITY_REVIEW_VERSION=sync_training_review_20261015 .venv/bin/python scripts/check_extended_rays.py
.venv/bin/python scripts/present_velocity_sync_review.py
.venv/bin/python scripts/build_documents.py --clean
```

The frozen `plan` must not be regenerated in place. Acquisition skips receipts
and verifies successful-file hashes; it does not retry identical failed requests.
Changed inputs require a new experiment directory. `fit` verifies and reuses
already frozen results. Do not rerun `validate` unnecessarily; the saved native
receipts and outputs document its actual execution. The last two commands rebuild
the report from saved results without downloading data or rerunning analyses.
Old diagnostic scripts that review 2025 are not part of this continuation.
