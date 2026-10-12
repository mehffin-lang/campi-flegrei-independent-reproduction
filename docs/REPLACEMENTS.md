# Replaced and preserved files

The first-run commit `df8c8c7` remains in Git history. The interrupted source-access-only attempt was uncommitted and is superseded. Replacement began only after all four uploads were available and the two PDFs' methods/captions had been read.

Removed obsolete first-run files:

- `src/validation.cpp`, `config/validation.txt`.
- `figures/validation.pdf`, `figures/validation.png`.
- `data/convergence.csv`, `data/picks.csv`, `data/residuals.csv`, `data/sensitivity.csv`.
- `scripts/plot.py`, `scripts/audit.py`.
- `report/validation_table.tex`, `report/sensitivity_table.tex`.
- Stale `sources/retrieval.json` and obsolete access-report artifacts/scripts.

Replaced: `README.md`, `.gitignore`, `docs/BLOCKERS.md`, `docs/PROVENANCE.md`, `docs/panel_record.json`, `sources/README.md`, `scripts/rebuild.py`, `report/report.tex`, `report/report.pdf`, and generated `data/checks.csv`, build/status/audit/hash records. The new numerical checks concern equations in the actual supplement, not the first-run travel-time model. No old success or validation claim carries over.

Added: `src/method_checks.cpp`, `config/method_checks.cfg`, `scripts/plot_methods.py`, `scripts/report_tables.py`, `docs/file_inventory.json`, `docs/panels.json`, `docs/METHODS.md`, `docs/REPLACEMENTS.md`, and the newly generated CSVs, method figures and report tables.

Preserved unchanged: `tanmodel.pdf`, `tanmodelsupp.pdf`, both `science.adw9038*.zip` uploads, `AGENTS.md`, and `brad-lipovsky-academic-style-guide.md`. The branch includes the user's upload commits, repository remote and all Git history. Unrelated user work was not modified. Extracted PDF text and reference-review images are local intermediates under `tmp/`; no archive was extracted.

## Current observational run

After successful PDF/method/caption checks and ZIP inventory, the following prior agent outputs were changed:
- Replaced `report/report.tex`, `report/report.pdf` and generated tables with an observational analysis report; previous files remain in Git history.
- Removed `figures/method_checks.pdf`, `figures/method_checks.png` and `scripts/plot_methods.py`. The synthetic-only figure presentation is superseded by actual waveform, spectrum, station and coverage figures.
- Replaced `scripts/rebuild.py`, updated `scripts/report_tables.py`, panel records, README and blocker/provenance documents.
- Regenerated the retained C++ validation CSVs and build logs/status/manifest. These remain labeled analytic consistency fixtures, not earthquake results.
- Added own retrieval, observational analysis, plotting and panel-update scripts; new input receipts, configuration, pinned dependencies and observational CSV/NPZ/figures.

Preserved useful C++ equation checks, permitted guidance files, all four user-supplied files, Git history, repository identity and unrelated user work. Large raw observations/model inputs and environment are ignored locally, with retrieval URLs and SHA256 receipts committed. No author archive was executed or used as analytical input.

## Resumed run, 9 October 2026

The previous report source/PDF, station and coverage PDFs/PNGs, generated report tables, panel JSON records, build status/log/manifest, README, input policy, and blocker descriptions are replaced with this run's evidence. `scripts/rebuild.py` and `scripts/update_panel_record.py` now include the extended workflow. New processing scripts and `config/requirements-resume.txt` accompany it; `config/association.json` records the explicit alternative-profile assumptions. New numerical outputs live in `data/extended/` and new figures in `figures/`.

The supplied PDFs/ZIPs, useful C++ validation source, original observational retrieval/processing and correctly labeled E1/E2/E3 template displays are preserved. The old four-station waveform outputs are recomputed as a retained validation subset, not mislabeled as the expanded analysis. No user source or unrelated work is deleted. Historical commits preserve superseded reports.

Important corrections: the INGV Md calibration exception is now permitted; fixed external backgrounds are distinguished from Tan's fitted products; full-period HTTP 413 is a chunking limitation, not proof of inaccessible data; Data S3 actually has 74 rows/58 gCAP entries, not the caption's 55. A coverage-aggregation development bug caused by pandas' variable timestamp precision was corrected before delivery, with an explicit sample-duration consistency assertion.

Added historical displacement outputs: original leveling-table extraction, original RITE GNSS through 2019, and a separately plotted written December 2023 monitoring estimate. Added original/retrained PhaseNet probability comparisons at CSOB/CMIS and an internal S–P consistency calculation. These additional diagnostics are not substituted for S4's exact benchmark or S12's relocated sector gathers. The magnitude attempt evaluates all provisional events, not only the smaller VELEST calibration subset.

## Presentation-only revision, 12 October 2026

Replaced `report/report.tex` and `report/report.pdf` with the requested main-paper, reproduced-supplement, then reproduction-documentation order. The main text follows the original named sections; publication figures retain their original numbers and order, with partial/missing-result labels. Existing audit prose, numerical tables and supporting evidence are preserved after the supplement. Non-original diagnostics are removed from the paper/supplement presentation, with only essential examples retained and labeled in the documentation; their files remain unchanged.

Added `report/comparison.pdf` and its LaTeX source for 19 ordered side-by-side comparisons. Published images are confined to that PDF and are never analysis inputs. Added a presentation-only document builder and verification record, with baseline hashes proving preservation of scientific data/figures/scripts. Updated README, `.gitignore` and only the final document-build invocation in `scripts/rebuild.py`. No scientific processing was rerun or upgraded to complete. See `docs/REPORT_LAYOUT.md` for file-level organization and build instructions.

## Scientific continuation, 12 October 2026

After rechecking both readable PDFs and listing/CRC-checking both author ZIPs, this run replaces the generated report and comparison PDFs, their generated LaTeX fragments/tables, the panel/layout/status records, README and current blocker/input-policy documentation. All original uploads and Git history are preserved. The permitted routine-catalog roles supersede the earlier prompt restriction on Figures 1A/1C/S5; author-derived catalog substitution remains prohibited.

- Added current `data/continuation/` observational selections, GNSS datum/overlap tables, response/coverage and inference records, picks/associations, independent VELEST pilot models/locations/corrections, magnitude measurements/equations, location checks and hybrid scan outputs. These supersede the 9-event/429-channel-hour claims for the current report. The earlier `data/extended/` baseline is retained and freshly regenerated by its own scripts.
- Replaced the report's old 2019-ending displacement figure with `figure_1B_displacement.pdf` from original daily observations through March 2025; updated main Figure 1 with routine panels A/C in `figure_1_combined.pdf`. Added `figure_S5_routine.pdf`, `figure_S6_pilot.pdf`, `figure_S8_pilot.pdf`, `continuation_coverage.pdf` and `continuation_stations.pdf`. The superseded `historical_leveling_partial`, `historical_catalog_context`, `routine_catalog_context`, `coverage_partial` and `stations_partial` PDFs/PNGs are removed after verifying the new counterparts exist; their scripts/data and prior Git versions are preserved. Exact removals are recorded in `docs/replaced_context_figures.json`. Useful independent template/picker/diagnostic figures remain.
- Added independent collection, checkpointing, inference, context, velocity-pilot, audit and rebuild scripts. Updated the existing downstream/location/hybrid routines to support the current dataset without erasing their earlier recipes.
- The first pilot VELEST attempt rejected nonpositive initial travel times; the next encountered a generic Fortran layer-count serialization mismatch. Those failures are documented. Explicit input-consistency filtering and format-only model serialization correction precede the successful pilot runs. No author-fitted model filled the gap.
- Recorded the exact Calò–Tramelli search and a verified numerical published alternative, rather than digitizing its graph. Added the second original GNSS release resolving the 2025 interval. Added a small permitted context-source snapshot; large raw inputs and project intermediates remain ignored with retrieval/hash receipts.
- The main/supplement/documentation order and the separate comparison-only PDF are preserved. Published references appear only in the comparison PDF. No unrelated user work, guidance file, uploaded source document or author archive is deleted or modified.

The expanded parallel amplitude attempt initially failed with `BrokenProcessPool`. Spawned workers replace forked workers, and hash-verified rebuild resumption preserves the passed association stage; the failed attempt remains recorded.

At 708 eligible events, the original 658-event VELEST capacity caused a memory fault. The generic build now declares capacity 1,024 and enables bounds checks. A subsequent single-precision Cholesky failure led to a recorded 64-bit arithmetic run with unchanged equations and damping. Both failed attempts and actual recompilations are preserved. Earlier pilot locations are cleared before each new solve and never substitute for a failed current result.

The executed build outcome and final counts, rather than this descriptive change list, are authoritative in `data/continuation/rebuild_status.json` and `report/document_build.json`.

A final numerical review removed the unsupported 20-event cutoff from the pilot b-value calculation. The likelihood statistic and formal sampling error are now calculated for the eight available values at/above pilot Mc, with selection bias explicitly excluded from that error. S8's partial figure, corresponding records, and both PDFs were rebuilt; upstream picks, locations, amplitudes and calibrated magnitudes were not changed. The follow-up commands and hashes are recorded separately in `data/continuation/magnitude_followup.json` and `rebuild_status.json`.
