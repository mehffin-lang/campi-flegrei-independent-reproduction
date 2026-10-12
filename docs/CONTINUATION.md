# Observational continuation, 12 October 2026

The full scientific reproduction is incomplete. The current deliverable is an executed, frozen observation checkpoint with explicit partial panels, independent pilot inversions, and an auditable remaining workload. The current numerical counts are authoritative in `data/continuation/analysis_summary.json`, `downstream_summary.json`, `velest_summary.json`, `hybrid_summary.json`, and `panel_status.json`.

## Build

Run from this repository, using Python 3.11. System tools are Git, curl, g++, gfortran, make, antiword, Poppler (`pdftotext`, `pdftoppm`), and TeX Live (`pdflatex`). The supplied main/supplement PDFs and both original ZIP files must remain at the root. The rebuild checks their sizes, hashes, readability and archive CRCs before replacing products.

```bash
mkdir -p tmp/continuation build
python3.11 -m venv .venv
TMPDIR="$PWD/tmp" .venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu -r config/requirements-resume.txt
.venv/bin/python scripts/restore_inputs.py --continuation
.venv/bin/python scripts/rebuild_continuation.py --fresh
```

Use the existing `.venv` when already installed. `--fresh` recomputes the earlier independent baseline and all new picking rather than accepting pick caches. Without it, the earlier independent baseline is retained and current input/configuration hashes govern the new per-file pick cache; association and subsequent stages still run. Both modes rebuild the scientific outputs and both documents. A passing build does not mean every scientific stage or panel is reproduced.

The frozen input manifests are `docs/rebuild_inputs.json`, `docs/continuation_rebuild_inputs.json`, and `docs/continuation_processed_inputs.json`. The latter records the exact files and time cores used for the new inference and hybrid exposure. Large waveform/model/software inputs stay ignored under `inputs/`; each has its source URL, byte count and SHA-256. An endpoint returning different bytes causes a hash failure. Preserve or supply the recorded snapshot, or explicitly audit a new version and regenerate the affected analyses; do not silently accept a different catalog or input.

`sources/continuation_context_inputs.zip` preserves the small permitted observations, metadata and written source files: routine-catalog HTML, daily GNSS text/format notes, station/availability metadata, the published alternative-model article, and Natural Earth coastline. Its members are classified in `docs/continuation_source_bundle.json`, and restoration validates the member list, CRC, hash and destination paths. This is a project-created input snapshot, distinct from the two author-result ZIPs. No uploaded author ZIP is executed or used as analysis input.

If an implementation stage fails, the failure log and a dependency-hash checkpoint are saved. After fixing that stage, `.venv/bin/python scripts/rebuild_continuation.py --resume` verifies the unchanged successful-stage inputs, outputs and invoked sources, then reruns the failed stage and all remaining stages. It refuses resumption if a completed dependency changed. The failed attempt remains in `data/continuation/rebuild_failed_attempt.json`. A current development run required replacing forked amplitude workers with spawned workers after `BrokenProcessPool`; that failure is an implementation issue, not a missing observation or a prompt restriction.

Fresh inference for all 147 new files is recorded in `data/continuation/fresh_inference_log.json`. A first rebuild was restarted during association after adding explicit study-boundary clipping; fresh picks were preserved. The final build record states whether it resumed or reused those verified picks, rather than claiming an uninterrupted fresh run.

The expanded VELEST solve first exceeded the upstream 658-event capacity. The build now declares 1,024 events and checks array bounds. A subsequent 32-bit Cholesky solve stopped at its positive-definiteness check. The current build uses 64-bit arithmetic with the same equations/damping; nine runs completed and 122 events passed the stated quality filters. Calibration changes by up to 0.48 km/s in Vp and 0.60 km/s in Vs between arithmetic precisions, so this is an unvalidated, numerically sensitive pilot rather than a robust regional model. `velest_capacity_failed_attempt.json`, `velest_single_precision_failed_attempt.json`, the corresponding rebuild attempts, and compiler repair records preserve the failures. Compiler-stage replacement in the resumed log corresponds to the actual independent recompilation, not a fabricated earlier pass. Neither the capacity repair nor changing arithmetic validates the fitted Earth model. Larger input sets will trigger the explicit capacity guard; scalable fixed-model location batching is still unimplemented.

Build only the documents from saved results:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

Outputs and source roots:

- `report/report.pdf` — `report/report.tex`, with `main_paper.tex`, `reproduced_supplement.tex`, `reproduction_documentation.tex` and generated tables/fragments.
- `report/comparison.pdf` — `report/comparison.tex` and generated `comparison_pages.tex`.
- `report/figure_layout.json` maps all original figures to partial results or placeholders; published images are confined to the comparison PDF.
- `report/document_build.json` verifies section order, 1–4 then S1–S15, nineteen comparison pages, and that the document builder does not mutate scientific files.
- `data/continuation/rebuild_log.json` records actual commands, return codes, elapsed times and output. `rebuild_status.json` distinguishes build success from scientific completeness.

## What was obtained

- Zenodo 17132077: `RITE_daily.txt` and `RITE_Timeseries_Format.readme`; 8,664 daily observations, 2000-05-29–2024-12-31. Text observations are used, not the JPG.
- Zenodo 22259337 (released 2026-09-02): `RITE_2000_2025.txt` and `Time_Series_Format.txt`; 9,025 seven-column observations through 2025-12-31. Only 79 observations through 2025-03-20 extend the earlier file. MD5 and SHA-256 verified. The overlap RMS after datum shift is 0.000295 m.
- Original Del Gaudio leveling table: 128 entries, 1905–2009. Joining the benchmark and GNSS series requires an explicit datum/site assumption; no published figure was digitized.
- Routine catalog: every annual page 2005–2025 retrieved 2026-10-12. Historical selection has 26,425 total / 16,046 located records; the study period has 19,274 total / 12,503 located records. The latter differs by +420 from the paper's historical count. No tuning or substitution resolves that difference. Monthly bins include unlocated routine records as an explicit assumption: the caption specifies the magnitude cutoff only for the cumulative curve and does not state how unlocated events enter the bars. These records are permitted only for 1A, 1C, S5, final comparisons and documented post-detection Md regularization.
- EIDA: 144 new six-hour station requests completed, 1,874,296,832 bytes and 2,519.463 channel-hours after clipping and union; plus three successful January 2022 probes. The large new batch covers portions of 19–20 March 2025, not three years. The processed checkpoint also includes the earlier independent calendar/event-window observations, documented separately.
- Fresh response XML: 22 IV and four 2I stations. `response_epoch_details.csv`, `response_coverage.csv`, `coverage_audit.json`, `station_coverage.csv` and `unobserved_channel_intervals.csv` distinguish response epochs, real observed spans, and gaps in this retrieval. A missing retrieved interval is not proof that the archive has no data. `processed_channel_hours` measures read input, not fully usable three-component picker exposure.
- Local/temporary archive: accessible event-selected windows from the preceding run are preserved; no claim of continuous exposure follows. RAN's site is accessible, but waveform download requires unavailable registration credentials. IT response queries returned 204. Full-period availability checks for the eight IV identifiers missing from response XML (V0106, CDOV, CROS, CASE, V0102, V0105, V0104 and CMDP) also returned HTTP 204; receipts are in `docs/unreturned_station_checks.json`. This concerns the public EIDA service, not every possible local archive.

The source/access receipts retain actual URLs, status codes, filenames and hashes. The uploaded PDFs and ZIPs retain their original hashes (`docs/file_inventory.json`). The original archives contain Tan-derived catalogs/phases/mechanisms and an interactive result plot, not the required continuous raw observations.

## Resume acquisition

```bash
.venv/bin/python scripts/collect_continuous.py plan
.venv/bin/python scripts/collect_continuous.py run --workers 6 --max-jobs 144
.venv/bin/python scripts/collect_continuous.py summary
```

The queue is calendar/availability driven, without any earthquake-catalog selection. Six-hour cores have thirty-second request margins. `inputs/continuation/acquisition.sqlite` records completed, failed, no-data and pending requests and survives interruption. The current checkpoint is 144 completed / 74,301 pending out of 74,445. Remove `--max-jobs` to continue pending requests until the queue or space reserve is exhausted. Inspect failures before requeueing them; no failed request counts as coverage. Do not run two collectors against the same queue.

There is a 20 GiB free-space reserve. Extrapolating this batch gives approximately 970 GB for full raw retention, whereas about 152 GiB was free when inspected; this is an estimate, not a measured archive size or a remote-access failure. Completing the whole queue requires incremental processing with an explicit raw-retention policy or additional storage. The present implementation has not completed that workload and does not claim it is inaccessible.

After a deliberately completed new batch, freeze it and rebuild:

```bash
.venv/bin/python scripts/freeze_continuation.py
.venv/bin/python scripts/rebuild_continuation.py
```

Freezing changes the checkpoint, source bundle and receipts; review those changes and keep their Git history. Frozen rebuilds do not silently ingest later downloads. The earlier `scripts/rebuild.py` preserves the superseded workflow; use `rebuild_continuation.py` for the current deliverable.

## Velocity search and independent pilots

`docs/velocity_profile_search.json` records the publisher article/supplement, INGV Earth-prints inventory, method-artifact tree, and citing publications/datasets checked for the exact Calò–Tramelli (2018) profile. Its supplement gives a graphical profile and a depth-dependent Wadati-derived Vp/Vs, without a numerical table. Earth-prints contains only the article in its original bundle. Data availability directs requests to INGV.

The verified alternative is Tramelli et al. (2021), *Scientific Reports* 11, 7211, Table 1, DOI 10.1038/s41598-021-86506-6. Layer tops [0, 0.5, 1, 3, 10] km below sea level; Vp [1.7, 2.0, 3.0, 5.5, 5.7] km/s; Vs = Vp/1.78. The source explicitly labels depths as layer tops. Piecewise-constant interpolation and the above-sea-level extension are stated implementation choices. `prepare_continuation.py` regenerates the table from the hashed written source. This is not asserted to be the exact 2018 profile.

Exact request, if needed: the numerical layered and interpolated Vp and Vs/depth-dependent Vp/Vs profile underlying Calò–Tramelli Figure S1.2a/b; layer depths, units, depth datum and convention; and confirmation of the version used by Tan's GaMMA-1D. Request from INGV–Osservatorio Vesuviano / Anna Tramelli; corresponding author Marco Calò (`calo@igeofisica.unam.mx`) can identify the 2018 table. Nobody has been contacted.

The permitted fixed `3d_vmod` artifact is pinned to revision `f84c9c9dc6bb1501a95a833f6634199a63d4f3b3` and attributed to Battaglia et al. (2008). Original-release byte identity remains unverified. The Tan-fitted `1d_vmod_velest.mod` and station corrections are excluded. VELEST starts from independently calculated averages of the fixed external grid, using documented assumed regions. Pilot fits, quality filters, physical layer checks and failure logs are independent outputs; they do not establish a validated regional velocity model.

Magnitude processing independently measures amplitudes and correlations and solves anchored difference equations. Routine Md is an expressly allowed external regularizer after independent detections; the resulting S8A comparison is not independent validation. Initial rather than final relocated locations, finite exposure and selection limit S8A/B. Training demonstrations, TomoDD scientific relocation, regional SVD, focal mechanisms, final location checks and three-year reviewed hybrid families remain incomplete. Generic TomoDD compilation is recorded separately and is not a scientific relocation result.

The magnitude-frequency pilot uses 0.1-unit rounded bins, maximum-curvature Mc, and `b = log10(e) / (mean(M) - (Mc - 0.05))` for values at or above Mc. Its Shi–Bolt standard error is `2.30*b^2*sqrt(sum((M-mean(M))^2)/(n*(n-1)))`. Eight selected values give conditional `Mc=0.3`, `b=1.24 ± 0.61`; this error excludes selection, calibration and exposure bias. An earlier self-imposed 20-event reporting cutoff is removed because the paper does not require it. `data/continuation/magnitude_followup.json` records the executed statistics, plotting and document rebuild; upstream picks, locations and magnitudes retain their hashes. This is not a regional completeness or b-value result.

Project-specific intermediates and caches live under `tmp/`; dependencies are in `.venv`. Standard pip cache is `/home/mehffin/.cache/pip`. See `docs/REPLACEMENTS.md` for what changed and `docs/BLOCKERS.md` for missing inputs versus unfinished implementation.
