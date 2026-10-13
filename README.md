# Campi Flegrei: provisional observational reproduction

The [latest local-file continuation](docs/local_followup.md) processed 14 previously omitted observation files and 19 new public downloads. The checkpoint contains **1,024 files, 30 station names, 8,952.452 union channel-hours, 136,376 picks and 1,024 provisional associations**. Its rerun gives **219 VELEST filter passes, 123 relocated gap passes, 80 conditional SVD estimates and 67 provisional amplitude magnitudes**. The new association failed residual filtering, so the retained relocated sample did not grow. Calibration remains sensitive to precision paths (0.89 km depth) and regional starts (1.04 km). These are not accepted structural results.

Figure 4 now shows seven **unaccepted gCAP/FK trial fits**, using the frozen previous cohort's candidate identifiers. AI inspection of 180 station-event records produced 29 usable first motions and 41 S/P measurements; no human review is claimed. SKHASH returned no mechanism: seven candidates lack eight polarities; event 649 has a 96.57-degree gap, above the unchanged 90-degree limit. gCAP variance reduction is 3.9–14.8% / 2.3–7.1% in two bands, with 34–98-degree orientation changes. The method port, assumptions, every candidate's requirements, observed/predicted waveforms and logs are disclosed in [data/mechanism_followup](data/mechanism_followup). No accepted mechanism is claimed.

The bounded acquisition attempted 20 previously unattempted requests: 19 downloads, one HTTP 204, no failures or repeat requests. **73,917 requests remain pending**. Four additional station names occur only in short single-channel windows; this is not full-network coverage. Earlier cohorts remain archived and are not additive event counts. The CAAM/COLB scan remains at 78.773 common hours and 823 unconfirmed crossings; this continuation did not repeat that scan.

The study is **not fully reproduced**. Both PDFs are provisional. The pipeline processes retrieved observations independently; routine-catalog panels are external context, and the explicitly cited 2021 starting profile is an exploratory alternative.

- [Scientific report](report/report.pdf), source [report/report.tex](report/report.tex).
- [Figure comparisons only](report/comparison.pdf), source [report/comparison.tex](report/comparison.tex).
- [Current processing checkpoint](data/local_extension/analysis_summary.json), [executed stages](data/local_extension/execution.json), [panel record](docs/panel_record.json).
- [Current procedure and scientific limitations](docs/local_followup.md), [input restoration](docs/GRID_WORKFLOW.md), [replacement record](docs/REPLACEMENTS.md).

Available counterparts include **1A–C, 2, 3, 4A–B (unaccepted waveform fits), S1, S2, S4A, S5–S8, S10, the sampled S11 swarm, S12–S13, S14 candidate families and S15A–C**. All are partial or provisional; S15A/B use explicitly different example events, and S14 shows unconfirmed candidates. No panel is fully reproduced. Remaining empty comparisons have specific missing observations, unsupported selections or failed computations recorded in the panel inventory. The current S6 contains own numerical inversions from the explicitly authorized Tan-distributed reference grid; the [superseded unverified workflow](quarantine/unverified_background/README.md) remains quarantined. The distributed grid's dimensional discrepancy and unknown historical transformation are disclosed.

Figure 1B distinguishes leveling surveys, source-provided estimates/reconstruction, and daily GNSS observations. Routine INGV events in 1A/1C/S5 are not independently detected events. S2 now uses an audited local projection, corrected coastline handling, leader labels and explicit unresolved station metadata. The 51 identifiers have not been reconciled to 48 instruments.

## Rebuild

Use the existing Python 3.11 environment, or follow dependency setup in [CONTINUATION.md](docs/CONTINUATION.md). From this repository:

```bash
.venv/bin/python scripts/rebuild_local_followup.py --analysis
```

This reruns frozen inference/association, calibration/relocation, magnitudes and location checks, the reviewed SKHASH and two-band FK/gCAP trials, then figures and both PDFs. It retains saved AI visual judgments, without asserting human review. Omit `--analysis` to validate the saved checkpoint and rebuild only plots and documents. See [the current procedure](docs/local_followup.md) for input restoration, exact commands, implementation departures and measured limitations. No waveform downloads occur in this command. Compatible inference caches and unchanged own daily associations may be reused after checks. Large observations stay under ignored `inputs/`, with source receipts and hashes. Mechanism IDs belong to the frozen `data/coverage_extension/` cohort; never join them to `data/local_extension/` by integer ID.

For a document-only rebuild from saved results:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

Do not run a document build concurrently with acquisition or analysis: its hash check requires a stable scientific checkpoint. Main-text sections precede the reproduced supplement, then the audit documentation. Missing paper results are text notices, not placeholder figures. The separate comparison PDF has 19 pages in original order; missing comparisons use explicit placeholders there only. Published images never enter the scientific report or processing.

## Input boundaries

Permitted resources include original waveform/GNSS observations, public metadata, trained PhaseNet weights with pinned attribution, and generic method software. Routine INGV duration magnitudes are external calibration priors, not independent magnitude observations. Tan-derived catalogs, phases, fitted models and focal mechanisms are not current analysis inputs. The current rebuild does not compute statistics from Tan result tables. Superseded comparisons are archived only as an audit trail.

Synthetic and analytic fixtures are kept in [tests/results](tests/results), never empirical catalogs or paper figures. Rejected numerical experiments are under [data/exploratory](data/exploratory), with explicit acceptance flags. The old grid-dependent entry points are disabled; Git preserves their history.

Project caches and intermediates are in `tmp/`; dependencies are in `.venv/` and the isolated `.venv-skhash/`. Standard pip cache: `/home/mehffin/.cache/pip`. An early import created `/home/mehffin/.seisbench`; current runs redirect that cache into the project. Nobody has been contacted on the user's behalf.
