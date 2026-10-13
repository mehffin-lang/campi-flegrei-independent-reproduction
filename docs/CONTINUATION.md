> Current continuation: [GRID_WORKFLOW.md](GRID_WORKFLOW.md). The Tan-distributed reference grid is now explicitly authorized; the records below describe earlier checkpoints and their then-current restrictions/results.

# Provisional observation checkpoint and rebuild

This workflow is incomplete scientifically. A successful build means the frozen retrieved subset and both PDFs were regenerated, not that the publication was reproduced. Actual counts are in `data/continuation/analysis_summary.json`, `downstream_summary.json`, `hybrid_summary.json`, `catalog_frequency_index.json`, `panel_status.json` and `rebuild_status.json`.

## Setup and clean rebuild

Use Python 3.11, Git, curl, g++, gfortran, make, antiword, Poppler (`pdftotext`, `pdftoppm`) and TeX Live (`pdflatex`). Keep `tanmodel.pdf`, `tanmodelsupp.pdf` and the two uploaded `science.adw9038` ZIPs at the repository root. Their filenames, sizes, hashes, readable captions and archive directory classifications are recorded in `docs/file_inventory.json`. No archive is executed.

```bash
mkdir -p tmp/continuation build
python3.11 -m venv .venv
TMPDIR="$PWD/tmp" .venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu -r config/requirements-resume.txt
.venv/bin/python scripts/restore_inputs.py --continuation
.venv/bin/python scripts/rebuild_continuation.py
```

Reuse `.venv` if installed. `--fresh` recomputes baseline and continuous PhaseNet inference, association, downstream measurements, numerical tests, figures and both PDFs. Without `--fresh`, baseline independent picks and matching per-file caches are retained; later stages still execute. Cache identities include raw-file hash, time core, settings, weight/metadata hashes, inference code and software versions. Failed or missing cache entries must not count as processed coverage. Resume a failed build only with `--resume`, which verifies passed-stage hashes.

The offline build requires the exact large raw waveform inputs locally. `restore_inputs.py --continuation` downloads missing inputs using receipt URLs and rejects mismatching bytes. The small contextual snapshots are in `sources/continuation_context_inputs.zip`; written-source/access evidence is in `sources/revision_written_sources.zip`. Additional verified source receipts, the observed S4A benchmark window and written provenance evidence are bundled in `sources/resumption_inputs.zip`, with `docs/resumption_rebuild_inputs.json` checksums. The frozen administrative request database is `sources/acquisition_checkpoint.sqlite.gz`; it includes pending jobs, which are not observations. Waveforms remain ignored under `inputs/`. Recreated published image crops remain ignored in `report/reference_assets/` and enter only `report/comparison.pdf`.

Do not run a document build concurrently with downloads or scientific processing. It verifies that current scientific files retain their hashes. The document-only command is:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

Its LaTeX roots are `report/report.tex` and `report/comparison.tex`; build checks and logs are in `report/document_build.json` and `document_build_log.json`. The scientific paper has main sections, partial supplementary results, then audit/supporting material. Missing results are text notices, not placeholder figures. The comparison PDF has all 19 published figures in order and clearly labeled missing comparisons.

The current amplitude stage uses sixteen spawned workers, each with a bounded 32-file cache of unchanged miniSEED observations. Every measurement window is copied before preprocessing. `tests/check_window_reads.py` checks exact sample and timestamp agreement between bounded reads and cached slices on 60 real windows before the magnitude stage. This is a software equivalence check, not an empirical result or a proof for every possible file. An earlier direct-read run was intentionally interrupted to change this execution strategy; the interruption was not a data-access failure. Passed inference and association stages were retained through hash-verified resumption. `data/continuation/rebuild_attempts.json` preserves failed/interrupted attempts; the final status records the executed outcome.

## Continue acquisition

```bash
.venv/bin/python scripts/collect_continuous.py plan
.venv/bin/python scripts/collect_continuous.py spread
.venv/bin/python scripts/collect_continuous.py run --workers 6
.venv/bin/python scripts/collect_continuous.py summary
```

`plan` creates the full Jan 21, 2022–Mar 20, 2025 six-hour queue from official availability. `spread` adds half-hour calendar checks at the study start, subsequent quarter starts, and March 1, 2025, for every candidate station with reported availability. These checks improve temporal sampling but do not replace the full queue. Short intervals run first, then chronological order, without any catalog-based event selection. Optional `--max-jobs N` makes a bounded batch. Do not run two collectors against the same SQLite queue.

Every response is checked by reading miniSEED headers, checking station/channel identities and hashing bytes. Failed, interrupted, no-data and pending requests contribute no coverage. Actual intervals are clipped and unioned; source/core margins are not extra study time. Downloaded exposure and actual finite PhaseNet-score exposure are distinct. `prediction_coverage.csv` and `prediction_coverage_summary.json` report finite scores in station-hours by phase for the continuous checkpoint; older baseline files lack this telemetry. SeisBench imputes missing components with zero for inference only. Imputed values never count as observations or enter empirical waveform plots. `request_ledger.csv.gz` records every status, `request_station_month.csv` aggregates the administrative ledger, and `station_coverage.csv`, `response_coverage.csv`, and `unobserved_channel_intervals.csv` describe actual processed observations and gaps. Gaps in this retrieval do not prove that the remote archive has no data.

A collector priority change is recorded in `docs/acquisition_priority_change.json`; unfinished transfers were requeued rather than counted. There is a 20 GiB free-space reserve. The earlier six-hour sample extrapolated to approximately 970 GB of raw full-period retention, versus about 152 GiB free at the start of this revision. This is an estimate, not an archive size measurement. Full retention needs additional storage or an explicitly documented processing/retention procedure; the present run retains all successfully downloaded original data.

After a finished batch, freeze its administrative/source receipts and regenerate:

```bash
.venv/bin/python scripts/freeze_continuation.py
.venv/bin/python scripts/rebuild_continuation.py
```

A fresh clone can restore the local request database from the compressed checkpoint before resuming collection; do not overwrite a more recent local database:

```bash
.venv/bin/python -c 'import gzip,pathlib; p=pathlib.Path("inputs/continuation/acquisition.sqlite"); assert not p.exists(); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(gzip.decompress(pathlib.Path("sources/acquisition_checkpoint.sqlite.gz").read_bytes()))'
```

Catalog frequency-index measurements run in six spawned workers grouped by original file. Each station window is copied before response removal. The final verification checks finite station indices, original-file membership, unique event/station measurements, and agreement between saved station measurements and saved event means. These numerical checks do not classify hybrids or replace onset/coda review.

## Scientific boundaries and sources

- **Observations/context:** INGV FDSN IV/2I traces and instrument responses; original RITE daily text series from Zenodo 17132077 and 22259337; Del Gaudio's historical numerical table; external INGV routine HTML snapshots retrieved October 12, 2026. No published pixels are analytical inputs. The 128 historical entries comprise 114 leveling surveys, 13 source estimates and one source reconstruction; source classes, original dates and uncertainty strings are retained. Daily GNSS already covers 2020–2023 and through March 20, 2025.
- **Routine catalog:** context only for 1A/1C/S5 and stated post-detection duration-magnitude calibration. Current selections yield 12,503 located study-period records, 420 above the written publication count. The version discrepancy is unresolved; no count-tuning filter is used. `docs/revision_access.json` records live and archive queries.
- **Method artifacts:** trained PhaseNet release and metadata pinned to `f84c9c9dc6bb1501a95a833f6634199a63d4f3b3`; generic GaMMA pinned to `80394dd4a4c29450da599f507916ecf1db6203dd`; generic VELEST source/portability changes documented in `data/extended/velest_build.json`. These are allowed method resources, not Tan-derived result inputs.
- **Starting velocity:** Tramelli et al. (2021), Table 1, has layer tops [0, .5, 1, 3, 10] km below sea level, Vp [1.7, 2, 3, 5.5, 5.7] km/s and Vs=Vp/1.78. `prepare_continuation.py` reads the actual written table. It is an exploratory alternative, not the unavailable exact 2018 profile. `docs/velocity_profile_search.json` records the search and missing model fields; no contact or request was made in this continuation.
- **Station membership:** the 51 released identifiers comprise 25 HH, 9 EH and 17 HN codes; the written methods specify 23 broadband, 9 short-period and 16 accelerometers. Two HH coordinate coincidences are not verified aliases, and the additional HN membership remains unresolved. No identifier was removed merely to match 48.
- **Quarantine:** the author-distributed 2008-attributed grid differs geometrically from the original written specification; original numerical data and transformation provenance are unverified. It and all historical dependent locations/fits are excluded from current processing (`docs/background_grid_provenance.json`). The quarantined grid is not a required input to the current rebuild or restore manifest. Current `run_velest.py` is disabled. `velest_stability.py` separately tests both real precisions with the 2021 alternative; no output is accepted as S6/Table S1 or fed into relocation.
- **Magnitude pilot:** 5 s signal, 2 s noise, 5 dB power SNR; own picked or predicted P; all available stations, including those without associated picks; response-corrected velocity, prefilter .1/.2/35/45 Hz and water level 60. Pair separation < one fifth of common station distances, at least two common stations; log10 peak-amplitude ratios, squared zero-lag correlation weights, unit-weight routine-Md regularization. Only identifiable anchored components produce magnitudes. Conditional formal uncertainty uses the residual-scaled inverse normal matrix; it omits systematic model/response/calibration effects. Mc uses 0.1-unit maximum-curvature bins; b uses Aki–Utsu half-bin correction and Shi–Bolt sampling error. These are limited-sample pilot quantities.
- **Location/hybrid diagnostics:** own S–P checks retain failures. P-aligned CPOZ gathers are not relocated-sector validation. The CAAM/COLB template scan uses the three written-method times, 8 s windows, .2–6 Hz and mean correlation >=.25. Crossings are unconfirmed. Candidate FI uses CAAM Z; catalog screening averages eligible station Z FIs from 8 s windows and measures SNR. Neither low FI nor prior-arrival flags confirm hybrid families or resolve coda contamination.
- **Synthetic software checks:** outputs are only under `tests/results`. Injected arrays are created in `tests/template_assertions.py` solely for assertions; no empirical output receives them. The current workflow does not execute the old Tan result-table comparison; superseded comparison products are audit archives only.

Access problems are distinct from unfinished implementation. The EIDA information-page TLS chain failed here, while official FDSN waveform/metadata endpoints worked. RAN registration/authentication pages are accessible; waveform credentials are missing. The local temporary archive has 319,889 readable directory entries for miniSEED files; seven bounded-range waveform examples were read successfully. Four advertised codes (CGAU, CLAC, CREM, CSOC) are absent from that saved directory. The examples are access inspections, not empirical detections. The archive contains windows selected around Tan-detected events; it cannot provide unbiased continuous exposure or detection seeds. Further stages and exact user-supplied input needs are in `docs/BLOCKERS.md`. Nobody was contacted.

Project-specific caches are in `tmp/`, dependencies in `.venv`; standard pip cache is `/home/mehffin/.cache/pip`. An earlier SeisBench cache at `/home/mehffin/.seisbench` is not used by current runs.

Public RAN station metadata were also retrieved from `https://ran.protezionecivile.it/IT/stazioni.php` and its XML download. The 860-member metadata archive was listed first; 17 selected XMLs and the directory are frozen in the revision bundle. `scripts/station_geometry.py` invokes `scripts/inspect_ran_metadata.py` to validate the frozen metadata and write the RAN response/installation tables. The full ZIP may stay local; the selected XMLs suffice for a clean rebuild. There are 57 study-overlapping HN/HG response epochs, 42 exact released-identifier matches across all sources, and nine unresolved identifiers. NAP is HG in the official record and HN in the released metadata; it is not silently renamed. POZA closed on 15 January 2025. These public metadata do not grant access to registered waveform downloads.

An additional all-network INGV StationXML query for V0106, CDOV, CROS, CASE, V0102, V0105, V0104 and CMDP returned HTTP 204; see `docs/unresolved_station_search.json`. This is a service-specific result, not evidence that local deployment metadata do not exist.

## Added observation checks and partial analyses

The continuation rebuild now executes `tests/check_annotation_telemetry.py` on observed recordings to verify that retaining finite prediction intervals leaves the pick list unchanged. `scripts/association_quality.py` saves all causality flags and deterministic waveform review examples; nonpositive propagation or same-station S–P excludes an event from magnitude equations/calibration and the VELEST precision pilot. This necessary screen is an explicit addition, not a substitute for manual phase review.

`scripts/differential_times.py` saves response-corrected original waveform windows and neighboring-event differential times. Ten-neighbor selection uses provisional alternative-model positions; the declared windows, coherence and lag thresholds are assumptions. Neither TomoDD round nor HypoDD uncertainties are claimed. Its known-delay tests write only `tests/results/`.

`scripts/benchmark_window.py` runs permitted original/retrained PhaseNet weights on an original 120-second CSOB observation window two hours after the contextual 20 May 2024 mainshock time. The exact published alignment is unverified. Its picks are saved separately and never added to the independently detected catalog. This is partial S4A inference, not training or a labeled accuracy assessment.

`scripts/cpoz_gathers.py` produces diagnostic HHZ and HHN gathers, −1 to +7 seconds around independent P picks, filtered above 4 Hz. They are not S12 sector validation. `scripts/hybrid_review_windows.py` saves six observed examples chosen by correlation and signal/noise, without automatic confirmation. Per-station scan scores are retained; a mean-score threshold crossing alone does not establish detection at both stations.

The earlier checkpoint and visual-review evidence are preserved under `data/resumption/`. Current outputs supersede the old pilot counts. See `docs/REPLACEMENTS.md` and `docs/resumption_sources.json` for replacement and source-access records. The current rebuild mode (fresh or cache reuse), executed commands and any failed stages are recorded in `data/continuation/rebuild_status.json` and `rebuild_log.json`; a successful build is not complete scientific reproduction.

A current association attempt was deliberately stopped after inspecting the permitted GaMMA library's worker-level random initialization. `scripts/gamma_reproducibility.py` resets the numerical initialization seed to 42 plus the deterministic DBSCAN label for each cluster. This disclosed choice changes no observations or likelihood equations and uses no Tan analysis code. `tests/check_association_repeatability.py` compares serial and parallel association on two observation windows selected from this project's own baseline review, with different parent random states. It is a repeatability check, not labeled detection accuracy. Association and dependent products are rebuilt; compatible inference caches are retained. The interrupted stage is preserved as return code −15 in the rebuild-attempt history.

Each executing stage now streams its log under `tmp/continuation/stage_XX.log`; the completed text and return code are retained in `data/continuation/rebuild_log.json`.

`docs/zenodo_release_inventory.json` and `sources/zenodo_archive_directory.bin` preserve the R61 ZIP directory inspection. Only the permitted weight/configuration members were decoded; they exactly match the normally restored model files. The extra range-inspection copies under ignored `inputs/resumption/` are not additional analysis prerequisites. Author code/result members and `raw_picks.csv` were not read.

`scripts/catalog_frequency_review.py` saves observed review windows for every negative-mean-FI candidate, selecting the two highest station SNRs and lowest station FI without changing the catalog. All nine current diagnostic pages (26 station windows) were inspected; the qualitative notes and output hashes are in `data/resumption/catalog_frequency_visual_review.json`. No reviewed onset labels or hybrid classifications were assigned. The procedure regenerates these diagnostics, while the report uses the inspection record only when the numerical-array hash still matches. This additional review motivated a presentation/validation follow-up after the first successful 31-stage rebuild; the preceding 27 scientific stages were retained after hash verification, and the new review, plotting, report and verification stages were executed again. Both attempts are preserved; a completed attempt is not recorded as a failed one.

The deferred exact-profile assessment is `docs/deferred_profile_assessment.json`. It was made after the other current scientific checks and waveform inspections, using the readable written sources and their recorded public-source inventories. No author contact, request draft, digitization or fitted-model substitution was made.


The subsequent calibration/relocation tests and Figure 1A/S5 style update are documented in [CALIBRATION_FOLLOWUP.md](CALIBRATION_FOLLOWUP.md). Run `scripts/rebuild_calibration_followup.py` for the incremental frozen follow-up. That procedure records numerical and scientific failures explicitly and does not turn the exploratory locations into accepted results.
