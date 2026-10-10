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
