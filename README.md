# Campi Flegrei: independent observational reproduction

This repository contains an executed but **incomplete scientific reproduction** of Tan et al. (2025). It independently processes original waveforms, performs provisional GaMMA association, measures response-corrected amplitudes, scans available hybrid-template windows, and extracts the original historical leveling table. It does not contain a reproduced multiyear relocated earthquake catalog or focal-mechanism solution set.

Read [the PDF report](report/report.pdf), [panel record](docs/panel_record.json), [stage record](docs/stages.json), [input policy](docs/INPUT_POLICY.md), [remaining limits](docs/BLOCKERS.md), and [replacement record](docs/REPLACEMENTS.md). Actual execution counts are in [extended results](data/extended/summary.json), [downstream measurements](data/extended/downstream_summary.json), [hybrid search](data/extended/hybrid_summary.json), and [coverage](data/extended/access_summary.json).

No publication panel is fully independently reproduced. **Partial: 1B, S1, S2, S15C.** All other publication panels are unreproduced. The routine-catalog plots related to 1A/C and S5 are explicitly **external context**, not independently detected events. Provisional association and candidate-review plots are additional diagnostics, not substitutes for relocated or confirmed-hybrid figures.

## Rebuild the executed analysis

Use this repository as the working directory. Requirements: Python 3.11, g++, gfortran, curl, Git, antiword, pdftotext, and pdflatex with the packages used in `report/report.tex`.

```bash
mkdir -p tmp
python3.11 -m venv .venv
TMPDIR="$PWD/tmp" .venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu -r config/requirements-resume.txt
.venv/bin/python scripts/restore_inputs.py
.venv/bin/python scripts/rebuild.py --clean
```

The four supplied PDFs/ZIPs are retained at the repository root and verified before generated products are removed. The exact external input snapshot is [docs/rebuild_inputs.json](docs/rebuild_inputs.json): URLs, byte counts, SHA-256 hashes, and placement paths. Inputs and generic software are ignored under `inputs/`. Restoration verifies existing files and retrieves missing ones. **Live catalog pages can change:** a changed hash causes a clear failure; provide the recorded snapshot or explicitly audit a new source version. No changed source is silently accepted.

The offline rebuild reruns C++ equation checks; original and extended waveform inference; provisional association; an analytic association test; original/retrained picker comparisons on unlabeled CSOB/CMIS windows; original leveling/GNSS and external catalog extraction; response correction, SNR/pair measurements, S–P and location quality checks; available-interval template scanning; candidate FI/waveform review; all plots and panel tables; and two LaTeX passes. Outcomes are saved in [data/build_log.json](data/build_log.json) and [data/build_status.json](data/build_status.json). The scientific-completion flag remains false even when the build passes.

## Acquisition and limits

The public INGV FDSN service supplies observations and instrument responses. Full-period requests for all 26 discovered study stations were executed and rejected with HTTP 413 (one-billion-sample limit). Half-hour requests across four calendar dates and daily requests were also executed; receipts distinguish successful records, HTTP 204, HTTP 502 and client timeouts. This is not full-period coverage. The remaining multiyear collection and processing are unfinished, not categorically inaccessible.

```bash
.venv/bin/python scripts/extend_inputs.py sources
.venv/bin/python scripts/extend_inputs.py responses
.venv/bin/python scripts/extend_inputs.py full-requests
.venv/bin/python scripts/extend_inputs.py day --date 2024-01-01
.venv/bin/python scripts/extend_inputs.py windows --date 2025-03-20
```

These commands acquire new data and update acquisition receipts; they are separate from rebuilding the frozen snapshot. The full-period command records the known large-request failure. Continued acquisition must use smaller chunks rather than repeating that failed request shape. Calendar windows are not chosen from author catalogs.

RAN needs unavailable registration credentials. Temporary/local traces were listed remotely and one miniSEED file verified; they are original observations cut around author-selected events and were not used to seed independent discovery. Four temporary 2I stations were reached through FDSN instead. Exact archive/source outcomes are in `docs/extended_*.json` and `docs/local_archive_inventory.json`.

The original 1905--2009 leveling table was retrieved from the publisher, not digitized from a plot. The original RITE GNSS series through 2019 was also retrieved from the cited publisher supplement and aligned through overlapping observations; daily 2020--2023 observations remain missing. Routine INGV Md is now permitted as the specific external regularization reference required by supplementary S6, but no magnitude is copied into a missing result. No qualifying measured relative-amplitude pair was obtained in this sample.

The cited Calo--Tramelli initial 1D model was found only graphically in its supplement. The released fixed 3D file permits explicitly labeled alternative regional averages. These are not Tan's fitted model or an asserted exact starting profile. Generic VELEST builds, but no resolved calibration, TomoDD/HypoDD relocation or focal inversion is claimed.

## Integrity and provenance

Neither science.adw9038 ZIP was executed. Data S1--S3 do not seed analysis. A final Data S3 row-count audit found **74 rows and 58 gCAP entries**, resolving the difference between the methods and the erroneous 55-event caption. No author solution values were inputs. No Tan analysis/plotting script or digitized published figure was used.

After independent processing, `scripts/final_comparison.py` reads Data S1 solely for final time-match and horizontal-difference assessment. Its separate `data/comparison/` outputs never feed back into analysis; reference matching does not change the generated catalog or panels. This comparison is included when the rebuild generates report tables.

Generic GaMMA is pinned to `80394dd4a4c29450da599f507916ecf1db6203dd`; the trained-artifact/background release is pinned in the input receipts. VELEST's generic upstream source is downloaded, inspected and built with documented platform-only repairs. Compiler warnings and outcomes are recorded separately from scientific execution.

Project intermediates and SeisBench, matplotlib and numba caches live in `tmp/`; the environment is `.venv/`. Standard pip cache: `/home/mehffin/.cache/pip`. An earlier initial SeisBench import created `/home/mehffin/.seisbench`; current runs redirect its cache into the repository. The repository, Git history, uploaded source files and unrelated work are preserved.
