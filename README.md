# Campi Flegrei: provisional observational reproduction

The [authorized-grid continuation](docs/GRID_WORKFLOW.md) independently runs grid-derived VELEST calibration and both fixed-3D TomoDD rounds. It retains 216 numerically filtered VELEST trials and 123 second-round gap passes, but calibration path dependence prevents scientific acceptance. All current figure groups are restyled from saved numerical products, with fixed comparable color scales and explicit under/over-range treatment. [Current rebuild outcome](data/grid_calibration/rebuild_status.json).

The study is **not fully reproduced**. Both PDFs are provisional. The pipeline processes retrieved observations independently; routine-catalog panels are external context, and the explicitly cited 2021 starting profile is an exploratory alternative.

- [Scientific report](report/report.pdf), source [report/report.tex](report/report.tex).
- [Figure comparisons only](report/comparison.pdf), source [report/comparison.tex](report/comparison.tex).
- [Executed counts and checks](data/continuation/analysis_summary.json), [rebuild outcome](data/continuation/rebuild_status.json), [panel record](docs/panel_record.json).
- [Current procedure](docs/CONTINUATION.md), [blockers](docs/BLOCKERS.md), [replacement record](docs/REPLACEMENTS.md).

Partial counterparts are **1A–C, S1, S2, S4A, S5 (three views), S8A–B and S15C**. No panel is fully reproduced. All other main/supplement panels remain unreproduced. S6 has been withdrawn: its old background-grid-dependent locations and fitted models are [quarantined](quarantine/unverified_background/README.md). The preserved Tan-distributed grid is now explicitly permitted as a disclosed reference input. Its dimensional discrepancy is documented; new independent trials remain unvalidated for scientific interpretation.

Figure 1B distinguishes leveling surveys, source-provided estimates/reconstruction, and daily GNSS observations. Routine INGV events in 1A/1C/S5 are not independently detected events. S2 now uses an audited local projection, corrected coastline handling, leader labels and explicit unresolved station metadata. The 51 identifiers have not been reconciled to 48 instruments.

## Rebuild

Use the existing Python 3.11 environment, or follow dependency setup in [CONTINUATION.md](docs/CONTINUATION.md). From this repository:

```bash
.venv/bin/python scripts/rebuild_grid_workflow.py
```

This verifies the expanded independent observation-processing checkpoint, rebuilds generic solvers, reruns grid-derived calibration and relocation, restyles saved results and builds both PDFs. See GRID_WORKFLOW.md for exact scope, input restoration and optional remeasurement. It does not complete the pending multiyear retrieval queue or bypass missing scientific prerequisites. Large waveforms remain local under ignored `inputs/`, with download URLs and checksums. The ordinary rebuild reuses only matching per-file inference caches, whose keys include observations, time cores, weights, preprocessing, inference code and software versions.

For a document-only rebuild from saved results:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

Do not run a document build concurrently with acquisition or analysis: its hash check requires a stable scientific checkpoint. Main-text sections precede the reproduced supplement, then the audit documentation. Missing paper results are text notices, not placeholder figures. The separate comparison PDF has 19 pages in original order; missing comparisons use explicit placeholders there only. Published images never enter the scientific report or processing.

## Input boundaries

Permitted resources include original waveform/GNSS observations, public metadata, trained PhaseNet weights with pinned attribution, and generic method software. Routine INGV duration magnitudes are external calibration priors, not independent magnitude observations. Tan-derived catalogs, phases, fitted models and focal mechanisms are not current analysis inputs. The current rebuild does not compute statistics from Tan result tables. Superseded comparisons are archived only as an audit trail.

Synthetic and analytic fixtures are kept in [tests/results](tests/results), never empirical catalogs or paper figures. Rejected numerical experiments are under [data/exploratory](data/exploratory), with explicit acceptance flags. The old grid-dependent entry points are disabled; Git preserves their history.

Project caches and intermediates are in `tmp/`; dependencies are in `.venv/`. Standard pip cache: `/home/mehffin/.cache/pip`. An early import created `/home/mehffin/.seisbench`; current runs redirect that cache into the project. Nobody has been contacted on the user's behalf.
