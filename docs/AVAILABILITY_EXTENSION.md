# Availability-led acquisition and independent velocity experiments

The starting checkpoint is commit `2ee4f6d52cc3cee45b954b70f0c6689d11ec317c`.
Earlier observations, model versions, catalogs and figures are preserved. This
extension is provisional. Numerical filter passage is not location validation.

## Observations and scope

`tanmodel.pdf` and `tanmodelsupp.pdf` are readable local specifications. The
supplement specifies 23 broadband, nine short-period and 16 accelerometer
instruments, 21 January 2022 through 20 March 2025 inclusive. The permitted
released station metadata contain 51 identifiers. Their correspondence to 48
physical instruments remains incompletely established; identifiers are not
silently collapsed. `station_crosswalk.csv` preserves that distinction.

`data/availability_extension/source_specification.json` records source hashes,
the baseline inventory, units and provenance classes. Inputs are original EIDA
waveforms, public StationXML, permitted PhaseNet weights, and the published
alternative initialization. No author-derived catalog, pick, location, fitted
velocity or numerical figure values enter the new inversion.

The current official INGV endpoints are listed by the
[FDSN data-center registry](https://www.fdsn.org/datacenters/detail/INGV/):

- `https://webservices.ingv.it/fdsnws/availability/1/query`
- `https://webservices.ingv.it/fdsnws/dataselect/1/query`
- `https://webservices.ingv.it/fdsnws/station/1/query`

Detailed availability is queried per candidate station and stated HH/EH band.
It is not inferred from an earliest/latest extent. Receipts retain request
parameters, URL, date, response status, bytes and checksums. The advertised
interval table is compared with actual miniSEED trace intervals. Station/month
coverage is a union, so request overlap and context are not double counted.
Raw trace coverage differs from finite PhaseNet-score exposure.

Eight station/band queries returned HTTP 204: V0106, CDOV, CROS, CASE, V0102,
V0105, V0104 and CMDP. These responses do not establish absence from other
archives. No restricted RAN or author access is requested. Event-selected local
snippets are excluded from detection and coverage. The published station list
serves as metadata, not as an event-selection source.

`metadata_validation.json` checks response epochs, coordinate ranges and sample
rates. It does not certify response calibration. Existing static station
coordinates approximate small epoch changes; `station_metadata_epoch_ranges.csv`
records those changes. Instrument-response accuracy and automatic phase
identities remain separate validation questions.

## Storage and resumption

`storage_budget.json` fixes a **40 GiB free-space reserve**, above the original
20 GiB project guard and above 20% of initially available space. It is checked
during streaming. Retrieval retains an additional 8 GiB for processing caches
and outputs above the fixed reserve, plus an allowance for concurrent writes. No
storage is reserved by filling files. Seven representative transfers measured
compressed bytes per newly covered channel-second; this is a station-dependent
estimate, not a guarantee or confidence interval.

Requests use two workers and six-hour station/band cores, with 30-second context.
Calendar-month rotation spreads retrieval over the study period. A common
**1 December 2024, 00:00–06:00 UTC** window has priority: the four public 2I
stations began recording in November 2024 but had no training arrivals in the
original calibration set. This choice follows metadata and missing training
support, not known earthquake times. The 2025 holdout remains excluded from
velocity/correction fitting.

`inputs/availability_extension/requests.sqlite` is the live ledger. Completed
files are checked by checksum on resumption. Existing empty/failed identical
requests are retained as separate outcomes. `collector_handoff.json` records
a controlled restart to change calendar priority; two interrupted `.part`
files were retained under `tmp/availability_extension/interrupted_transfers`
and never processed. They are not recorded as coverage or service failures.

Resume collection:

```bash
.venv/bin/python scripts/availability_extension.py retrieve
```

Do not start a second collector against the same ledger. To reconstruct the
target on a fresh checkout, place original input files according to the saved
observation manifests, preserve the recorded storage budget, then run:

```bash
.venv/bin/python scripts/availability_extension.py inventory
.venv/bin/python scripts/availability_extension.py availability
.venv/bin/python scripts/availability_extension.py plan
.venv/bin/python scripts/availability_extension.py sample
.venv/bin/python scripts/availability_extension.py retrieve
```

Availability responses and waveforms remain local under ignored `inputs/`.
Source receipts and checksums are committed. Re-querying in the future may
produce a different availability version; preserve the old receipts first.
The collector stops at exhausted eligible requests, the storage reserve, or its
documented service safeguard after eight consecutive failed transfers. Such a
stop is not a claim of complete coverage: remaining advertised intervals and
their size estimate are retained. Rate limits and client transfer timeouts must
be distinguished when assessing a service stop.

## Picking, association and models

Incremental picking can run alongside collection:

```bash
.venv/bin/python scripts/pick_available_eida.py
```

Its own arrivals are cached only after waveform/model/settings/implementation
and core-interval identity checks. Failed files are recorded rather than
retried indefinitely. `inputs/availability_extension/stop_incremental_picking`
is an explicit stop sentinel. A shared lock prevents conflicting new picking
checkpoints. The existing PhaseNet preprocessing and excluded S picks at CASE,
CFB1 and CFB3 remain unchanged. Missing components and unavailable finite scores
are not counted as observed data.

The scientific commands actually used for the first frozen extension are:

```bash
.venv/bin/python scripts/process_availability_extension.py --freeze --workers 4
.venv/bin/python scripts/prepare_observational_selection.py
CF_VELEST_TIMEOUT=1800 .venv/bin/python scripts/estimate_observational_profile.py \
  --observations data/availability_extension/catalog \
  --selection data/availability_extension/catalog/selection \
  --output data/availability_extension/velocity_canonical
CF_VELEST_TIMEOUT=1800 .venv/bin/python scripts/locate_observational_profile.py
.venv/bin/python scripts/validate_observational_profile.py \
  --profile data/availability_extension/velocity_canonical
```

`--freeze` explicitly advances the input set; omit it to use the saved input
manifest. Preserve a completed catalog/model directory under a new version
before advancing it. Do not join event indices from different checkpoints.

The alternative initialization is [Tramelli et al. (2021), Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC8009907/),
already documented in `docs/velocity_profile_search.json`. Its top extends to
−0.5 km; fixed interfaces are −0.5, 0.5, 1 and 3 km below sea level, followed by
a halfspace. The 10-km interface is omitted because the shallow calibration
events do not resolve it. Initial Vp/Vs is 1.78; fitted P and S velocities are
independent. This is neither the exact Calò–Tramelli profile nor an observed
velocity model. No further attempt to obtain that profile is made.

The source scripts and model summaries specify damping, P/S weights, station
reference, step limits, iteration counts and quality filters. Six experiments
test initial speeds, single/double precision, event selection and depth-step
control. All eligible 2025 calibration events are held out before fitting the
model or corrections. The main training set caps each UTC day at 20 evenly
spaced events; a second experiment uses all pre-2025 candidates. This explicit
weighting departure reduces dominance by the May 2024 swarm; it is not Tan's
manual event selection. Holdout locations/origins are fitted nuisance
parameters, so the residual test is conditional, not absolute location accuracy.

The instrumented first precision failure is reproduced by:

```bash
.venv/bin/python scripts/diagnose_initial_divergence.py
```

`precision/diagnosis.json` traces a direct/refracted ray switch for event 1065,
CBAG S, to the first large depth-step difference. Diagnostic binaries reproduce
the original outputs byte-for-byte. The code does not impose an arbitrary ray
tie-break. A separate input-order defect is documented in
`phase_order_validation.json`: unrelated new picks changed equal-time CNV row
ordering. New inversion inputs sort by event, station, phase and time. The
old and expanded calibration sets then serialize identically. The original
uncanonical runs and their source versions remain under `velocity_existing`,
`velocity_expanded` and `implementation_versions`.

Whole-cohort locations use five fixed-model passes, 0.4/0.3 s residual rejection,
at least six retained phases, RMS ≤0.25 s and azimuthal gap ≤300°. Numerical
filter passage does not override a failed velocity/holdout test. Prior TomoDD,
magnitude and mechanism products keep their earlier checkpoint identity;
they are not silently assigned the new model.

## Documents and validation

```bash
.venv/bin/python scripts/rebuild_availability_extension.py
```

This verifies the frozen numerical manifest, regenerates saved-output plots,
updates the existing manuscript and comparison sources, and compiles both PDFs.
It does not initiate downloads or rerun unrelated analyses. The manuscript
contains no published figure images. The comparison remains 19 side-by-side
figure pages. Live acquisition indices are explicitly excluded from the
document builder's immutability check; frozen scientific files remain protected.

The new velocity diagnostic belongs after the reproduced supplement and is
not a publication-panel reproduction. Figures S1/S6 and Table S1 identify the new
provisional model when present. Figures 2–4 and other dependent products retain
their explicitly identified prior checkpoint until independently rerun.

Logs are under `tmp/availability_extension`; retained execution archives and
hash manifests make the numerical inputs and output files inspectable without
running the pipeline. Raw observations and temporary files remain in this
repository. Dependency environments/caches retain their existing locations;
new code uses the existing `.venv`, `tmp/seisbench`, `tmp/numba` and
`tmp/matplotlib`. No project artifacts are written elsewhere.


## Exact input restoration and live continuation

On a fresh checkout, restore the prior observations first, then verify or restore
this extension. The second command only requests files with existing successful
receipts; it never retries a previously empty or failed request.

```bash
.venv/bin/python scripts/restore_eida_observations.py --download
.venv/bin/python scripts/restore_availability_inputs.py --download
```

A remote response with a different checksum is rejected. It requires a new
observation version and new processing, rather than reuse of prior results.
The committed ledger snapshot reconstructs the ignored SQLite database when
absent. Detailed advertised intervals are retained numerically in
`data/availability_extension/advertised_intervals.csv`; the original response
bytes remain in ignored `inputs/availability_extension/` with checksums.

The collector refreshes coverage after each completed batch. The local
`watch_available_eida.py --collector-pid PID` process records those snapshots
and the current request states when transfer outcomes change. After that collector actually stops, it takes over
from incremental picking, freezes all completed observations in a new timestamped
directory, and attempts inference, association, the same six velocity experiments,
location passes, and document rebuild. Its command, exit status, and logs are
recorded in `data/availability_extension/continuation_status.json`. This scheduled
continuation is not a claim that future numerical work has succeeded. Do not
start a second watcher or collector. No additional agent is launched.

For a new scientific checkpoint, use fresh output directories:

```bash
.venv/bin/python scripts/rebuild_availability_extension.py --run-analysis \
  --catalog data/availability_extension/catalog_new \
  --profile data/availability_extension/velocity_new
```

This command refuses to overwrite earlier cohort/model directories. Without
`--run-analysis`, the current pointer in `current_analysis.json` identifies the
frozen checkpoint; its exact numerical inputs, model source, and solver binaries
are verified before figures and documents are rebuilt. Live retrieval indices
are excluded from document-only immutability checks; frozen scientific files
are still protected. Later downloads do not silently alter a published checkpoint.
The comparison remains 19 ordered reference/result pages. S1 and S6 are replaced
by the new own location experiment unless another panel update is explicitly
recorded. The new velocity diagnostic belongs after the supplement only.

`durable_handoff.json` records the detached collector, picker and watcher processes.
Their continued existence was checked after the launching command exited. Four
incomplete transfers across the two controlled handoffs are retained locally
for provenance and never counted as data, failures, or completed coverage.


## Duplicate and gap reconciliation

`check_availability_overlap.py` checks file hashes and channel/time/sample-rate
keys for the frozen cohort. The December checkpoint has five duplicate file
pairs (1,327 paths, 1,322 distinct hashes) and 403.573 raw channel-hours of
interval overlap. Coverage is always a union; duplicated files are retained
for the audit trail. Pick merging and association identity checks remain active.

The repeated files exposed a planning error: detailed availability advertises
small gaps within successful earlier requests. Refetching those entire windows
returned identical bytes. `reconcile_availability_requests.py --apply` marks
88 remaining whole-window repeats as `prior_success_unverified_gaps`;
0.140511 advertised channel-hours within them remain unverified. These are not
called empty or covered. The live collector rechecks status before each batch
and skips these full-window repeats; the planner now assigns that state at
construction. The original collector source remains in implementation_versions.
Fresh, unattempted available windows continue. Targeted checks of the small
advertised internal gaps are separate remaining work; their intervals remain in
the coverage inventory. No new data are inferred from availability metadata.
