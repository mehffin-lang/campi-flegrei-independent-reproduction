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
