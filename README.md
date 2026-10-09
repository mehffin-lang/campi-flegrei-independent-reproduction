# Campi Flegrei: independent observational processing

This run retrieves original INGV observations and generates new station, coverage, waveform, spectral and PhaseNet-pick outputs. **The full scientific reproduction remains incomplete. No main-manuscript panel is reproduced.** S1, S2 and S15C are partial reconstructions; all other publication panels remain unreproduced. The calendar-day pick figure is an additional validation result, not an earthquake catalog.

Read [the compiled report](report/report.pdf), [the full panel record](docs/panel_record.json), [input policy](docs/INPUT_POLICY.md), [access outcomes](docs/access_attempts.json) and [replacement record](docs/REPLACEMENTS.md).

## Sources and restrictions

The supplied `tanmodel.pdf` (2,140,554 bytes) and `tanmodelsupp.pdf` (62,164,947 bytes) are readable. Both supplied `science.adw9038` ZIPs were listed and CRC-checked. They contain author-derived results and an interactive plot; none is used as input. Their complete directory inventory and checksums are in `docs/file_inventory.json`.

Original FDSN waveforms and station metadata are permitted. The retrained PhaseNet tensor artifact is explicitly permitted; this run performs independent inference, not independent training. Authors' picks, catalogs, fitted velocity models, station corrections, scripts and figure products are excluded. The routine INGV catalog is comparison-only and was not consulted. The temporary archive contains author-event-selected cuts; no such cuts enter independent detection. RAN waveforms require credentials that are unavailable here.

## Rebuild

Use the repository root. Requires Python 3.11, a C++17 compiler, curl, Poppler (`pdftotext`) and pdfLaTeX with the standard packages used in `report/report.tex`.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r config/requirements-observations.txt --extra-index-url https://download.pytorch.org/whl/cpu
.venv/bin/python scripts/retrieve_observations.py
.venv/bin/python scripts/rebuild.py --clean
```

Retrieval requests a calendar-selected day (2024-01-01) at CAAM, COLB, CSOB and CSTH plus six short files for the three written-method templates, station metadata and the authorized model artifact. Requests are hourly, with four concurrent downloads and bounded retries. This is not a download of the full three-year archive. Inputs reside in ignored `inputs/`; URL/size/SHA256 receipts are in `docs/observation_inputs.json`. Preserve those hashes when placing files manually. A cached rebuild is offline and verifies every input hash before analysis. A new retrieval manifest should be reviewed if an upstream service returns changed bytes.

Processing commands, individually:

```bash
.venv/bin/python scripts/analyze_observations.py
.venv/bin/python scripts/plot_observations.py
```

Data products are under `data/observations/`, figures under `figures/`, and LaTeX/PDF under `report/`. `data/build_log.json` records actual commands and return codes. `data/build_status.json` separates computational success from scientific incompleteness; `data/manifest.sha256` records final file hashes. The C++ checks are retained solely as useful equation validation. Their synthetic fixtures are not publication reproductions.

Project caches/intermediates remain in `.venv/`, `inputs/`, `tmp/` and `build/`. Pip uses `/home/mehffin/.cache/pip`; the initial dependency check created `/home/mehffin/.seisbench/config.json`, while analysis redirects SeisBench to `tmp/seisbench/`; TeX uses the installed system resources. Model architecture, filtering, normalization, FI windows, spectrum settings, coverage limitations and model artifact provenance are documented in the report and `config/observations.json`.

## Remaining work

The full multi-year association, velocity calibration, relocation, absolute-magnitude and focal-mechanism analyses are not implemented. Written defaults and permitted initial velocity inputs are incomplete; fitted author products cannot fill these gaps. The paper's duration-magnitude prior conflicts with the current comparison-only rule for the routine catalog. No arbitrary spatial model or synthetic earthquake catalog replaces those missing stages.
