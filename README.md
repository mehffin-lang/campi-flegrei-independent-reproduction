# Campi Flegrei: provisional observational reproduction

The [current continuation](docs/PROVISIONAL_CONTINUATION.md) plots the available independent numerical results while preserving failed scientific validation. The frozen 1,015-association cohort yields 216 filtered VELEST locations and 123 final TomoDD gap passes, 90 conditional SVD solutions, 65 relative-amplitude magnitudes and 118 CPOZ traces. None establishes a validated multiyear catalog. Held-out phase RMS worsens from 0.2177 to 0.2198 s; precision and regional-start path sensitivity persist. [Executed rebuild](data/grid_calibration/provisional_rebuild.json).

The separately processed coverage extension has **997 files, 26 station names, 8,706.970 channel-hours, 134,483 picks and 1,023 provisional associations**. Its own rerun gives **219 VELEST filter passes, 123 final TomoDD gap passes, 80 conditional SVD solutions and 67 amplitude magnitudes**. These overlap the earlier cohort and must not be added as separate earthquakes. Both cohorts are shown with explicit labels; their event IDs are never joined. Public downloads work, but 73,937 requests remain pending. The CAAM/COLB scan covers 78.773 common hours and returns 823 unconfirmed crossings, not confirmed hybrids.

The study is **not fully reproduced**. Both PDFs are provisional. The pipeline processes retrieved observations independently; routine-catalog panels are external context, and the explicitly cited 2021 starting profile is an exploratory alternative.

- [Scientific report](report/report.pdf), source [report/report.tex](report/report.tex).
- [Figure comparisons only](report/comparison.pdf), source [report/comparison.tex](report/comparison.tex).
- [Frozen processing checkpoint](data/calibration_followup/expanded/analysis_summary.json), [current verification](data/grid_calibration/provisional_verification.json), [panel record](docs/panel_record.json).
- [Current procedure and scientific limitations](docs/PROVISIONAL_CONTINUATION.md), [input restoration](docs/GRID_WORKFLOW.md), [replacement record](docs/REPLACEMENTS.md).

Available counterparts include **1A–C, 2, 3, S1, S2, S4A, S5–S8, S10, the sampled S11 swarm, S12–S13, S14 candidate families and S15A–C**. All are partial or provisional; S15A/B use explicitly different example events, and S14 shows unconfirmed candidates. No panel is fully reproduced. Remaining empty comparisons have specific missing observations, unsupported selections or failed computations recorded in the panel inventory. The current S6 contains own numerical inversions from the explicitly authorized Tan-distributed reference grid; the [superseded unverified workflow](quarantine/unverified_background/README.md) remains quarantined. The distributed grid's dimensional discrepancy and unknown historical transformation are disclosed.

Figure 1B distinguishes leveling surveys, source-provided estimates/reconstruction, and daily GNSS observations. Routine INGV events in 1A/1C/S5 are not independently detected events. S2 now uses an audited local projection, corrected coastline handling, leader labels and explicit unresolved station metadata. The 51 identifiers have not been reconciled to 48 instruments.

## Rebuild

Use the existing Python 3.11 environment, or follow dependency setup in [CONTINUATION.md](docs/CONTINUATION.md). From this repository:

```bash
.venv/bin/python scripts/rebuild_provisional_workflow.py --calibration --extension
```

This verifies the frozen independent observation checkpoint, rebuilds generic solvers, reruns grid-derived calibration and relocation, runs the new diagnostics and supported downstream analyses, then builds both PDFs. Omit `--calibration` to reuse hash-verified calibration and measured differential times. See PROVISIONAL_CONTINUATION.md for exact scope and dependencies. It does not complete the pending multiyear retrieval queue or bypass missing scientific prerequisites. Large waveforms remain local under ignored `inputs/`, with download URLs and checksums. Inference caches are reused only with matching observations, time cores, weights, preprocessing, implementation and software versions. The separate `data/coverage_extension/` cohort must never be joined to earlier integer event IDs.

For a document-only rebuild from saved results:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

Do not run a document build concurrently with acquisition or analysis: its hash check requires a stable scientific checkpoint. Main-text sections precede the reproduced supplement, then the audit documentation. Missing paper results are text notices, not placeholder figures. The separate comparison PDF has 19 pages in original order; missing comparisons use explicit placeholders there only. Published images never enter the scientific report or processing.

## Input boundaries

Permitted resources include original waveform/GNSS observations, public metadata, trained PhaseNet weights with pinned attribution, and generic method software. Routine INGV duration magnitudes are external calibration priors, not independent magnitude observations. Tan-derived catalogs, phases, fitted models and focal mechanisms are not current analysis inputs. The current rebuild does not compute statistics from Tan result tables. Superseded comparisons are archived only as an audit trail.

Synthetic and analytic fixtures are kept in [tests/results](tests/results), never empirical catalogs or paper figures. Rejected numerical experiments are under [data/exploratory](data/exploratory), with explicit acceptance flags. The old grid-dependent entry points are disabled; Git preserves their history.

Project caches and intermediates are in `tmp/`; dependencies are in `.venv/` and the isolated `.venv-skhash/`. Standard pip cache: `/home/mehffin/.cache/pip`. An early import created `/home/mehffin/.seisbench`; current runs redirect that cache into the project. Nobody has been contacted on the user's behalf.
