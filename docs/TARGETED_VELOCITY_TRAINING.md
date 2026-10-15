# Targeted pre-2025 velocity training, 15 October 2026

**No profile is validated.** One reviewed event adds 20 arrivals and seven
previously absent station/phase combinations, but does not resolve model and
location sensitivity. This versioned experiment is in
`data/velocity_holdout_review/training_extension_20261015/` (abbreviated `D`).
The 602 earlier velocity-trial files were hash-checked and preserved. Starting
commit: `e92078122085e323cf840ea8e608deaa783ab01d`.

## Coverage and provenance

The broad collector and incremental picker were stopped. `D/broad_queue_pause.json`
records their state and two preserved incomplete files, excluded from coverage
and inference. No RAN records or exact Calò–Tramelli profile were sought.

`D/target_coverage_before.csv` distinguishes advertised and stored data. Training
support ended in May 2024; target EIDA data start in July (CRUS/CUMA) or November
(CGAU/CREM/CSOC, and CLAC on November 13). These are availability dates, not
instrument deployment dates. CRUS has no advertised data for the previously
processed December 1 interval. The four 2I stations already had six-hour December
1 recordings, but no qualifying calibration event. Context spilling backward
from a 2025 request is excluded from pre-2025 training acquisition.

The new batches cover December 12 and 19, 00:00–06:00 UTC: six stations, three
components, 12 files, **216 core channel-hours**, 123,535,872 bytes. December 12 is
the first complete calendar day after all six have simultaneous advertised
coverage; December 19 adds a day one week later. Dates use availability, not
catalogs or holdout performance. The measured-size estimate was 123,116,584 bytes.
The 40 GiB free-space reserve plus 8 GiB processing allowance was retained.
All requests succeeded. Exact URLs, parameters, hashes and segments are in
`D/availability/`, `D/receipts/`, `D/coverage_ledger.csv` and `D/request_ledger.csv`.
Processed exposure excludes transfer context. The twelve completed requests were
registered in the global ledger to prevent duplicate retrieval; see
`D/global_ledger_registration.json`. The broad queue was not resumed.

The permitted retrained PhaseNet weights, 1 Hz preprocessing, 0.3 thresholds and
previously documented alternative GaMMA profile were retained. The batches yield
**1,205 P + 6,132 S picks** and three provisional associations, saved in
`D/catalog_dec12/` and `D/catalog_dec19/`. This is neither a full network nor a
completeness sample. Seven short records at CAAM, CBAC, CFMN, COLB, CPOZ, CSOB and
CSTH then connect the project's December 12 packet to the established network.
All succeeded: 615,936 bytes against a 756,000-byte estimate. `D/ties_dec12/`
records these **event-selected calibration clips**, excluded from continuous
exposure and discovery claims. Their times came only from this project's picks.
`D/catalog_ties_dec12/` preserves the ensuing provisional associations.

All new EIDA headers match their StationXML epochs, coordinates, responses and
rates. Absolute clock accuracy has not been independently verified. Original
EIDA records are observations; trained weights and the Tramelli (2021) Table 1
initialization are permitted method resources. Reviewed arrivals and fits are
project calculations. No Tan-derived results, published figure values, digitized
points or synthetic observations enter the experiment. Both local PDFs were
readable; extracted methods remain in the versioned `tmp` directory.

## Review and admission

Tan specifies a high-quality calibration subset without a complete numerical
screen. This project's disclosed screen is unchanged: causal arrivals, at least
four P and two S, more than ten phases, gap below 180 degrees, and provisional
depth strictly between 0.001 and 7.999 km. Passing it is not model validation.

`D/review/` contains raw/filtered windows, metadata and decisions. Reviews are
**Codex visual inspection, not independent human seismologist validation**.
Filtered traces are displays; the new manual time is read from raw counts.

- December 1 event 1952 still has a 216.1-degree gap; event 1961 has ten arrivals.
  Neither is admitted; possible extra arrivals remain uncertain.
- The December 12 packet was split by later coda picks. CGAU P is clear in raw
  counts at **04:34:26.21 UTC**, with approximate reading uncertainty 0.03 s.
  Its later automated P lies in coda. The earlier project-picked CRUS S at
  **27.44 s** replaces the later 28.31 s peak. CUMA P/S and CAAM S are uncertain
  and excluded; no CSOC arrival is created. Possible later events remain uncertain.
- Reassociation of the 20 reviewed arrivals yields one event: 10 P, 10 S,
  gap 156.2 degrees, provisional depth 2.84 km. This is not a known depth.
  `D/qc/reviewed_arrivals.csv` records admissions, exclusions and changes.
  The manual P's unit association weight is **not a PhaseNet probability**.
  VELEST P/S weights remain 1/0.5.
- December 19 fails causality (S before P), with only two P picks, a boundary
  depth and a 197.4-degree gap. Review does not justify forced arrivals.

Training is now **53 events/847 arrivals**, or 63/1,010 in the selection test.
CGAU P/S, CLAC S, CREM P/S and CRUS P/S gain **one arrival each**. CSOC P/S and
CUMA P/S remain absent. One event cannot establish repeatable station corrections.
The 827 inherited training arrivals are unchanged, not all newly reviewed;
previously noted uncertain/coda picks remain a possible source of instability.
No exact number of additional events sufficient to pass validation can be
established from this experiment.

## Fits and unchanged validation

`D/fit_preregistration.json` retained all three earlier families and six
sensitivities before new association/review. Two files had already been picked
at registration, as disclosed there. No 2025 score selected a family or setting.
Every training fit finished before validation; `D/fits/training_frozen.json`
seals them. Earlier training CNV blocks were checked byte-for-byte before addition.

All 18 fits ran. Four/three-layer joint fits reduce training RMS to 0.1750/0.1784 s
but worsen 2025 RMS to 0.2458/0.2463 s. The restricted zero-delay trial changes
training RMS 0.2174 to 0.2115 s and holdout RMS **0.2432 to 0.2272 s**, but sensitivity
reaches **898 m horizontally, 1.57 km depth and 0.27 km/s velocity**. Extra training
iterations change locations by 177 m/0.15 km; extra fixed-model holdout iterations
change them by 305 m/0.20 km. Its printed 32/64-bit results agree; that does not
resolve initialization/selection sensitivity. No profile passes every criterion.

Unchanged limits: 100 m horizontal, 0.1 km depth, 0.05 km/s velocity, 0.02 s delay,
physical monotonic velocities, convergence and better holdout RMS than both the
family initialization and original reference. Delay sensitivity is checked across
trials and iterations, implementing the previously stated 0.02 s requirement.
2025 arrivals were never changed or used to estimate velocities or corrections.
As in the established test, **held-out event locations/origin times are adjusted
with the model fixed**: conditional prediction, not absolute-location validation.
The previously examined 2025 set is not a pristine blind test.

The preserved zero-delay fit has 80/366 P and 115/461 S paths in the layer starting
at 3 km, including interface paths. Only **48 P/76 S rays** extend strictly below
it, from nine sources. The new base fit has 52/376 P and 83/471 S strict deep
paths; none belongs to the added event. The change is in older estimated
geometries. The added event spans 2.70–3.04 km across fits, so improved deep
resolution is not established. Native vertices are rounded to 0.01 km.
See `D/deep_ray_coverage_before.csv`, `D/ray_coverage_after.csv`,
`D/new_event_depth_sensitivity.csv`, `D/experiment_results.csv`,
`D/sensitivity_results.csv` and `D/training_station_phase_residuals.csv`.
Sensitivity ranges are not statistical confidence intervals.

Needed next: more distinct pre-2025 events with clear target and backbone phases,
including CSOC/CUMA and events with stable deeper constraints, across dates/source
regions. Additional public intervals exist but were **not retrieved in this
bounded experiment**, not declared inaccessible. Expert review may clarify some
uncertain windows; it cannot manufacture absent observations. No lower thresholds
are proposed. No failed model is promoted to the catalog or publication panels.

## Commands, inputs and preservation

Use the existing `.venv` and generic VELEST 32/64 builds; each native receipt
records its binary hash. `inputs/` and `tmp/` remain inside the checkout, ignored
by Git. Receipt URLs, parameters, sizes and SHA-256 hashes identify the large
input files and their required locations. Missing files must be restored from
those URLs and verified before resume; mismatching files are not silently reused.
No project cache is added outside the repository. The standard Matplotlib user
cache remains at `/home/mehffin/.cache/matplotlib`; SeisBench/Numba and all
project inference caches remain inside the checkout.

Executed stages (logs accompany the native evidence archive):

```sh
.venv/bin/python scripts/extend_velocity_training.py inventory
.venv/bin/python scripts/extend_velocity_training.py query
.venv/bin/python scripts/extend_velocity_training.py retrieve
.venv/bin/python scripts/check_target_metadata.py
.venv/bin/python scripts/process_target_training.py --tag catalog_dec12 --day 2024-12-12
.venv/bin/python scripts/process_target_training.py --tag catalog_dec19 --day 2024-12-19
.venv/bin/python scripts/prepare_observational_selection.py --observations data/velocity_holdout_review/training_extension_20261015/catalog_dec12
.venv/bin/python scripts/prepare_observational_selection.py --observations data/velocity_holdout_review/training_extension_20261015/catalog_dec19
.venv/bin/python scripts/retrieve_training_ties.py plan
.venv/bin/python scripts/retrieve_training_ties.py query
.venv/bin/python scripts/retrieve_training_ties.py retrieve
.venv/bin/python scripts/process_target_training.py --tag catalog_ties_dec12 --jobs ties_dec12/new_input_jobs.json --base-picks catalog_dec12/picks.csv
.venv/bin/python scripts/review_target_training.py --catalog data/velocity_holdout_review/training_extension_20261015/catalog_ties_dec12 --events 0,1,2 --tag ties_dec12
.venv/bin/python scripts/prepare_reviewed_training.py
.venv/bin/python scripts/fit_extended_training.py prepare
.venv/bin/python scripts/fit_extended_training.py fit
.venv/bin/python scripts/fit_extended_training.py validate
.venv/bin/python scripts/check_extended_rays.py
```

The inventory/plan is a frozen snapshot; do not rerun it against the changed
global ledger. Acquisition resumes from existing plans/receipts. Review preparation
replays disclosed decisions; it does not automate human review. Changed inputs
require a **new version directory**, not overwriting this run. Do not run the
older waveform-review scripts that inspect 2025 for this task.

Presentation rebuild from saved numerical outputs:

```sh
.venv/bin/python scripts/summarize_training_extension.py
.venv/bin/python scripts/build_documents.py --clean
```

The new source `report/velocity_training_extension.tex` appears first in the
post-supplement documentation. The report and comparison PDFs are rebuilt, with
no replacement of empirical publication panels. The old report remains in Git;
all earlier velocity results and empirical figures remain unchanged.
`D/verification.json` and `report/document_build.json` record checks.
