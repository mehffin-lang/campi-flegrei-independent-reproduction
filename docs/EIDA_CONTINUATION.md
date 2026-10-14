# Eligible continuous-observation continuation

The current continuation preserves `data/local_extension/`,
`data/coverage_extension/`, and `data/mechanism_followup/` as superseded
checkpoints. Their counts are not additive. Current numerical results are in
`data/eida_continuation/`; current source-mechanism measurements and trials are
in `data/mechanism_eida/`. A computed solution is not necessarily scientifically
accepted. Consult `result_summary.json`, the per-stage validation records, and
the panel inventory for actual outcomes.

## Observations and acquisition

`collect_eida_followup.py` resumes the existing public INGV EIDA queue, selecting
only pending requests with zero previous attempts. It never retries an identical
successful, empty or failed request. Each returned MiniSEED file is inspected,
hashed, and recorded in the SQLite ledger. Request receipts preserve HTTP status,
station, channel pattern, core interval, bytes and checksum. The original
endpoint and padded download intervals are in the observation retrieval receipts.
Coverage uses the union of actual returned samples, not requested duration.

This continuation first requests remaining intervals in the last three study
days, then calendar-selected intervals across the study years. A separate
20-station batch covers the entire six-hour interval 2024-05-20 18:00 to
2024-05-21 00:00 UTC, containing the previously specified S4 swarm benchmark.
This is purposeful sampling of continuous observations. No published picks or
event solutions enter detection, but neither independent discovery of that known
swarm nor population completeness is claimed. Many full-period requests remain
unattempted. RAN acquisition and the exact Calò–Tramelli profile are deferred.

All 14 known event-selected waveform snippets are excluded from the new
continuous-detection catalog and exposure inventory. They remain preserved for
explicitly identified downstream waveform demonstrations. The exact list is
`data/eida_continuation/eligibility.json`. Every eligible waveform is listed in
`all_observation_inputs.json`; station epochs and response coverage are checked
by `audit_continuation.py`.

## Executed workflow and limitations

The unchanged PhaseNet inference implementation uses the released trained
weights and hashes the waveform, weights, inference settings and implementation.
Daily GaMMA associations may be reused only after exact numerical pick, station
table and configuration comparisons. The alternative Tramelli et al. (2021)
starting profile remains explicit. Current IDs are local to this checkpoint.
The 165 original baseline files retain their earlier 15-second processing
margins; newer segmented inference uses 30 seconds. Their observation hashes,
saved picks and unchanged baseline configuration were checked against the prior
checkpoint (`baseline_reuse_validation.json`). This is disclosed legacy reuse,
not a claim that the baseline was rerun with the newer margin setting.

VELEST uses the expressly authorized Tan-distributed, Battaglia-attributed grid
and independently selected causal phases. `grid_provenance.json` records its
unaltered hash, axes, units and dimensional discrepancy with the cited 2008
description. Regional masks and four-layer averaging remain disclosed
approximations. The new compiler capacity is 4,096 events; both precision builds
use the same equations, array-bounds checks and memory addressing option.
`velest_build.json` records the actual compiler commands and hashes.

A fixed-model batching shortcut was tested on all 552 actual calibration events
and rejected: splitting the cohort changed some depths by 1.91 km because the
solver retains global backtracking. The production solve keeps the complete
cohort. A separate Cholesky optimization skips leading terms that are provably
zero, retaining the order of all nonzero arithmetic and the global updates.
`check_sparse_velest.py` compared six complete observed-data runs (552 events,
9,529 phases): event files, station corrections, velocity models and residual
files were byte-identical to the original dense implementation. The optimization
is installed for both precisions. A further 32-bit dense comparison of the current 552-event fixed-model prelocation
also produced byte-identical numerical outputs (`sparse32_check.json`).
Source/binary hashes and adoption timing are
recorded in `sparse_build.json`, `sparse_check.json`, and `sparse_adoption.json`.
This is a numerical equivalence check, not evidence of correct event locations.
The separate failed native single-event-mode experiment and its logs remain
preserved; it was not adopted.

Both unconstrained regional fits produced negative isotropic bulk modulus in
the 3–5 km layer (Vp/Vs 1.073 and 1.088). That calculation and the intentionally
interrupted downstream relocation are preserved in `unconstrained_calibration.zip`
with original repository paths and a verified per-file hash inventory. The
current run uses uniform velocity-layer damping 100, recorded in
`config/eida_calibration.json`. This is one explicitly disclosed regularization
alternative; the original paper does not specify this setting. It preserves
observations and quality gates and yields physically admissible trial speeds,
but the regional pilots still failed the local location-stability gate. It is
not an accepted velocity model or exact reproduction.

The expanded cohort contains 57,494 phase-pair measurements and 16,042 absolute
picks before waveform-correlation filtering. The prior generic TomoDD build
allowed only 40,000 observations. Its capacity was increased to 150,000
observations and 1,650 connected clusters, retaining array-bounds checks,
equations, weights, and the previous EOF/residual-output fixes. The original
binary is preserved and both builds are hashed in `tomodd_build.json`.
The larger cohort exposed a separate generic logging error in a cluster without
waveform-correlation observations: the diagnostic largest-residual station index
was zero. The failed run is archived in `tomodd_logging_failure.zip`. Guarding
zero-observation statistics and initializing diagnostic indices allowed processing
to continue; all eight first-cluster iteration location files remained
byte-identical (`tomodd_logging_fix_check.json`). No inverse equation changed.

Regional SVD sampling uses at most 174/165/175/166 events (the written method's
sample sizes) in the four alternative quadrants, without replacement, seed 42.
All smaller groups are retained. Every qualifying connected component of those
samples is attempted and failures are recorded independently; membership is saved.
The same zero-correlation logging defect occurred in one HypoDD component.
The diagnostic-only patch recovered three estimates from that four-event
component. An unaffected five-event component produced byte-identical locations
and errors before and after the patch (`hypodd_logging_repair.json`). The current
total is 352 conditional estimates. A separate eleven-event component still
fails because fewer than two non-airquake events remain; it was not repeated
without a changed scientific input. Ninety-five smaller components are
ineligible for this SVD calculation. Generic HypoDD clips the negative station
elevations of CFB1 and CFB3 to zero; `receiver_convention_check.json` records this
additional approximation without changing the original metadata.

The numerical sequence retains fixed-model prelocation, both velocity/station
calibration rounds, convergence checks, five whole-catalog passes and the existing
residual, pick-count and gap filters. The two fixed-grid TomoDD rounds, regional
HypoDD SVD estimates, amplitude-difference magnitude inversion, external routine
Md regularization, conditional magnitude distribution, CPOZ gathers and S–P
checks are rerun on current saved inputs. Held-out refitting excludes every fifth
chronological calibration event before fitting. Common-intermediate-start
precision tests distinguish accumulated path sensitivity from local arithmetic
differences. None of these internal tests establishes absolute location accuracy.
The 441-event fitted model reduces held-out RMS from 0.2403 to 0.2081 s for
111 interleaved events. The holdout samples the same swarms, not a separate
region or time period. Starting observations, model, station file, and controls
are byte-identical in the two precision paths. Maximum depth differences grow
from 0.15 km at fixed-model prelocation to 0.85 km after convergence iterations;
the final median and 95th percentile are 0.04 and 0.2735 km. The precise
ill-conditioned parameter combination or ray-path switch remains unidentified.
The accepted zero-term optimization is separately equivalent in both precisions;
there is no evidence that it causes the divergence.

Source-mechanism review IDs are linked to current own locations by shared,
identical observed phases, a unique maximum overlap and origin times within two
seconds. An unmatched candidate explicitly retains its historical own geometry
only for a downstream check. Larger current candidates require own provisional
ML≥2.2 and at least eight retained P picks; this is not the paper's Md selection.
All eight historical review candidates have a unique current match; no historical
geometry fallback was needed. Six larger current candidates are added. Old AI
judgments transfer only when the corresponding saved numerical waveform
arrays are identical. Changed or new packets require a separate recorded AI
visual review; no human review is asserted. S/P requires independently picked
phases, verified response/orientation, signal/noise checks and inspection for
possible clipping. Additional observations do not justify accepting ambiguous
polarities. SKHASH keeps the eight-polarity, 90° azimuth and 60° plunge gates.
FK/gCAP uses own trial locations and model, with the previously documented
exploratory density, Q, band, time-window and source choices. Band-dependent fits
and returned mechanisms remain subject to validation.

## Commands

From the repository root, with the documented Python environments and generic
method binaries already installed:

```bash
# Verify the frozen original observations; no network access by default.
.venv/bin/python scripts/restore_eida_observations.py
# Add --download only to restore missing originals from their saved public URLs.

# Verify the executed numerical checkpoint, redraw its figures, build both PDFs.
.venv/bin/python scripts/rebuild_eida_followup.py

# Rerun the numerical stages on the frozen input manifest, then figures and PDFs.
# Compatible inference/daily-association caches require exact input/config matches.
.venv/bin/python scripts/rebuild_eida_followup.py --analysis
```

The analysis command does not download data or perform human visual review.
It refuses to transfer saved review judgments if the measured waveform windows
change. It uses current saved AI decisions, whose limitations remain explicit.
Acquisition and creation of a new checkpoint are separate:

```bash
.venv/bin/python scripts/collect_eida_followup.py --max-jobs 256 --workers 4
.venv/bin/python scripts/process_eida_followup.py --freeze
```

Do not build the documents while acquisition or numerical outputs are changing.
The document builder verifies its scientific inputs stayed unchanged and checks
main paper → reproduced supplement → documentation order, followed by a separate
comparison-only PDF. Published references appear only in the comparison PDF.

Run receipts are in `pipeline_execution.json`, `execution.json`,
`post_execution.json`, `rebuild_result.json`, and the saved solver records. These
distinguish executed stages from available commands. Large original observations,
dependencies and temporary files remain ignored inside the repository. Standard
dependency caches retain the locations documented in the README. Existing
historical-context and training-demonstration gaps are not resolved by EIDA
acquisition.

## Current measured outcomes

The executed continuation adds 275 successful files and one empty response from
276 distinct previously unattempted requests (3.481 GB). No new request failed.
The full queue still contains 73,641 pending requests, 11 earlier failures and
37 empty responses. These are separate from actual sample coverage. The current
eligible manifest has 1,285 files, 26 station names, 83 channels, and 13,467.933
union channel-hours; all have response epochs/stages/sensitivity metadata.
This existence check does not prove instrument calibration accuracy.

All eligible local observations entered inference. Merged output contains
246,668 picks and 3,271 provisional associations. Calibration uses 552 candidates,
464 from 20 May 2024; the data strongly favor one sampled swarm. Whole-catalog
filters retain 1,435 trials and the two TomoDD rounds retain 1,050 events. Ten
regional SVD components succeed, one fails after airquake removal, and 95 smaller
components are ineligible. There are 352 conditional uncertainty estimates.
The 868 amplitude-inversion magnitudes give conditional Mc = −0.1 and
b = 0.822 ± 0.032 for 592 values at/above Mc. These are selected-sample statistics,
not a continuous-catalog completeness measurement or publication agreement.

The mechanism cohort has 303 station-event records, 205 reviewable P windows,
99 accepted AI first-motion signs, and 108 accepted exploratory S/P measurements.
Eight new approximate P marks are saved in `config/mechanism_eida_arrivals.csv`;
seven produce usable signs, while the COLB 101400 polarity is rejected after
closer review. All are downstream-only. The original and modified waveform arrays
are compared explicitly; the pre-addition checkpoint remains in
`before_additional_arrivals.zip`. Zero human reviews are claimed.

SKHASH returns quality-D solutions for candidates 100331 and 101760, with plane
uncertainties of 39–59 degrees. Four other candidates fail its actual perturbed-ray
azimuth-gap test. The nominal surface-station gap is recorded separately and
must not be mistaken for the solver's perturbed-ray gate. Eight candidates have
fewer than eight accepted first motions. Candidate 100948 has no usable reviewed
measurements and uncertain identity amid preceding activity; 101760 also has
near/pre-origin motion at CAAM/COLB. These flags do not silently alter the catalog.

FK/gCAP produces 12 trial fits in each band. Variance reduction is 1.3–14.4%
at 0.2–2 Hz and 1.4–9.1% at 1–5 Hz; orientations change by 45–95 degrees.
The four own SKHASH–gCAP Kagan angles are 35.6–79.1 degrees, none below the
paper's 30-degree agreement criterion. No scientific mechanism is accepted.
The unchanged generic minimum-eight, 90-degree azimuth and 60-degree plunge gates
are explicit implementation choices, not recovered event-specific Tan settings.

The expanded CAAM/COLB search covers 140.656 common hours and finds 1,843
unconfirmed crossings. Of 36 displayed candidates inspected by AI, four show
preceding-packet tails and three ongoing activity without an isolated onset;
the other 29 transients remain unclassified. The 1,807 undisplayed crossings
remain unreviewed. The broader frequency-index screen measures 3,270 events;
107 have negative mean FI, and 62 of these lack any station above 5 dB SNR.
Only ten best-station windows in that negative-mean set were visually screened.
No three-year hybrid chronology or confirmed hybrid family is claimed.

The numerical stages were run through recorded failures and resumptions; the
hash-verification/figure/PDF rebuild is run separately. The default build must
not be described as a fresh full execution of `--analysis`. The complete request
ledger and all stage receipts distinguish unfinished work from remote access
failures. No source requiring RAN access or the exact Calò–Tramelli profile was
contacted or requested in this continuation.
