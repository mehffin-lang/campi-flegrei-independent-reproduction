# Authorized reference-grid continuation

This is the current calibration, relocation and presentation procedure. Earlier follow-up files are historical checkpoints. No publication panel is fully reproduced, and no scientifically accepted calibrated/relocated catalog is claimed.

## Reference input

`data/grid_calibration/reference_grid.original` preserves the original 122,853 bytes, SHA-256 `dc36fe2a542fc7a3b6c473c48ec109c53ddd77a1721f509b920fea97fb0166f3`. Source: [Tan distribution, pinned revision](https://github.com/iamharrison2000/Campi-Flegrei-Earthquake-Monitoring/blob/f84c9c9dc6bb1501a95a833f6634199a63d4f3b3/models/3d_vmod); citation: Tan et al. (2025), Science, doi:10.1126/science.adw9038; Battaglia et al. (2008), doi:10.1111/j.1365-2478.2007.00687.x.

The current user explicitly authorizes this starting/reference input. It is not asserted to be a separately retrieved original Battaglia array. The 23×14×27 longitude/latitude/depth grid differs from the original written 18×18×9 km, 0.5 km geometry. Its historical transformation remains unverified. `grid_provenance.json` records all axes, units, ordering and regional masks. The grid is not regridded. No Tan-fitted velocity model, station delay or event solution is read.

`prepare_grid_calibration.py` interprets Vp in km/s and the second volume as Vp/Vs; Vs is their pointwise quotient. Longitude varies fastest. Positive depth is below sea level. Regional profiles exclude horizontal padding and exact 0.1 km/s air/nonsolid nodes; the first fully solid plane at 0.1 km extends upward. Box masks, node weights and depth averaging are explicitly assumed where written methods are incomplete. Original and derived files remain separate.

## What actually ran

The expanded independent checkpoint contains 868 files, 26 station names, 8,511.520 union channel-hours, 132,733 merged picks and 1,015 provisional associations. These span the study dates sparsely; no full-period coverage claim is made. Exact input hashes and actual date bounds are in `input_inventory.json`. The older 1,003-event cohort has different identifiers and is never used to fill this cohort's windows or picks.

The new causal screen supplies 916 events for the catalog inversion and 38 calibration candidates with at least four P, two S, more than ten picks, gap <180°, and no initial depth-bound hit. This is an automatic necessary-quality screen, not Tan's manual 373-event selection. Eight-layer fits became nonphysical. Following generic VELEST guidance, the next trial disables low-velocity-layer inversion initially, prelocates for 14 iterations, merges weakly resolved layers to tops −0.5, 1, 3, 5 km, and damps the deepest velocity. A damping-1000 serialization overflow is preserved; damping 100 is representable. Both regional four-layer branches pass final local iteration gates after two calibration rounds and three additional checks. The lower converged residual fit, rather than its earlier moving second-round state, drives five fixed-model catalog passes. The paper's residual and final filters retain 216 trial locations.

Full 32/64-bit paths still differ by 558 m horizontally and 0.89 km vertically, up to 0.32 km/s in velocity and 0.25 s in station delay. Common-converged-start runs agree to printed precision, indicating path dependence rather than establishing a unique solution. Regional starts differ by about 655 m horizontally and 1.04 km vertically. Held-out refitting for this grid-derived model and manual phase review remain undone. No fit is accepted as absolute location truth.

Fresh response-corrected observed windows supply 1,464 neighboring-event pairs, 5,802 picked-phase differences, 9,794 waveform comparisons and 546 accepted station/phase delays (767 channel measurements); 13 window failures are preserved. Generic TomoDD with JOINT=0 runs both rounds with the unchanged reference grid. Its absolute-arrival reader lacked a close at EOF; this prevented the second cluster from reopening the file. The build applies that explicit file-handling correction and enables bounds checks, without changing equations. A second output correction appends residuals for every cluster instead of overwriting all but the last. Final azimuthal gaps use only stations with positive-weight retained residuals. Earlier 126/125 gap counts used the initial observation set and are superseded; the last-cluster residual diagnostics are explicitly archived. Round 1 returns 132 events, 124 after gap filtering; round 2 returns 124, 123 after filtering. Final depth range is 0.111–7.965 km. These remain unvalidated exploratory locations. Per-observation residual RMS is recalculated from residual tables; the solver's event columns use a different denominator and are not silently interpreted as observational RMS.

`merged4/summary.json`, `validation.json`, `tomodd/summary.json` and `verification.json` are the numerical authority if a future run changes these counts. `run_records.zip` preserves own serialized inputs, controls, logs and outputs, including failed attempts. Generic source receipts are separate from observations.

## Plotting

`scripts/publication_plots.py` regenerates every current figure group from saved numerical products. Published images are never read by this script. `style/plot_inventory.json` identifies every file's numerical inputs and hashes. Diagnostics remain outside the scientific paper/supplement figure sequence.

- S5 uses printed 0–5 km depth limits and ticks 0,1,2,3,4,5. 1A has printed ticks 0,2,4 but unlabeled endpoints; its 0–5 normalization is explicitly approximate. Under-range is white and over-range is magenta, with extension marks and counts in `data/continuation/routine_plot_style.json`. No depth or magnitude is clipped, jittered or changed.
- Dark maps/context panels use serif labels, white axes, red-to-blue depth and the original layout. The magnitude-to-area display law remains an explicit assumption. External routine events retain that label.
- S1 uses blue actual intervals on white; missing intervals remain gaps. S2 uses red/yellow/white instrument classes, verified local coordinates and leader labels. No copied relief or artificial elevation colorbar is added.
- S4 uses its four-row waveform/spectrum/probability layout, blue P/orange S traces. S15 uses four component columns and log-frequency spectra. Their numerical spectral color limits are not printed in the publication; an explicit normalized-PSD −80–0 dB display uses white/black under/over colors. `spectral_scales.json` records actual ranges/counts. Threshold marks are derived display indicators, not reference annotations.
- S8 uses small blue points, blue counts and an orange conditional relation from this project's saved statistics. It remains a sparse, provisional magnitude pilot, not full-catalog completeness.
- Figures 3 and 4A–B lack validated independent locations/magnitudes/mechanisms. No stylistic counterpart is manufactured. Readable reference depth scales are 0–5 km; 4B elevation ticks are 0–360 m by 40 m, but no independent elevation/mechanism panel is generated.

## Rebuild

From the existing checkout:

```bash
.venv/bin/python scripts/rebuild_grid_workflow.py
```

This validates the saved independent expanded picking/association checkpoint, rebuilds VELEST and TomoDD, derives regional profiles, reruns calibration and precision checks, verifies and reuses this cohort's own differential measurements, executes both TomoDD rounds, regenerates all current figures, updates evidence records and compiles both PDFs. `--remeasure` rereads original waveforms and recomputes the differential measurements; those measurements were computed afresh in this continuation before the rebuild. No old-cohort cache is eligible. Software completion and scientific acceptance are distinct fields in `data/grid_calibration/rebuild_status.json`.

The existing environment is `.venv` (Python 3.11). Generic VELEST source/setup is retained by `build_velest.py`. Generic TomoDD source is under ignored `inputs/external/tomodd`; the build restores a missing archive from the pinned authorized URL, verifies its SHA-256, lists/filter-extracts only method source and headers, and verifies any existing source against that archive; its authorized upstream receipt is `docs/tomodd_source_receipt.json`, which pins the 56,350,720-byte archive and checksum. Only method source, manuals, AK135 reference and global layer tables are used; example observations/results/scripts are excluded. `build_grid_tomodd.py` records every compiled source hash and the EOF-close change. gfortran/gcc, pdflatex and Poppler are required.

Large waveform inputs, response XML, permitted trained weights and compatible inference caches remain local with source receipts in the existing manifests. The source grid is committed byte-for-byte, so a rebuild need not refetch it. `scripts/restore_inputs.py --continuation` and the acquisition/inference procedures documented in `CONTINUATION.md` describe upstream restoration; they do not assert that pending downloads were completed here. Project intermediates are in `tmp/grid_calibration`; dependencies in `.venv`; the standard pip cache remains `/home/mehffin/.cache/pip`. Do not run acquisition or numerical updates concurrently with the document build, which verifies scientific-file hashes.

Document-only rebuild: `.venv/bin/python scripts/build_documents.py --clean`. Current scientific report: `report/report.pdf` (`report/report.tex` and included sources). Comparison only: `report/comparison.pdf` (`report/comparison.tex`). Original figures occur only in the comparison PDF.

## Remaining scientific limits

Grid use is no longer blocked by permission or dimensions. Its exact historical transformation and Tan's regional masks remain unspecified. Sparse observations, unreviewed associations and inversion path dependence limit reliable geometry; numerical filter passage is insufficient. S7 uncertainty, accepted-location magnitude calibration/completeness, focal mechanisms, sector/depth checks and complete hybrid histories remain unfinished. Exact Calò–Tramelli association layers remain missing but did not block these trials. No contact or draft request was made. RAN waveform credentials remain unavailable. Unfinished processing is not described as an access failure.

The full procedure executed the scientific stages and plot generation, then the first document check rejected an overfull revision identifier. The identifier was shortened in the prose while preserving the full source receipt; presentation was rebuilt. Subsequent residual-scope validation prompted the documented output-only TomoDD correction and a relocation/presentation rerun with `--resume-relocation`. Both failures and their repairs are retained in `data/grid_calibration/rebuild_status.json` and the preceding-attempt records; successful earlier calibration was not repeated solely for formatting. Final global second-round RMS is approximately 0.0430 s for waveform differences and 0.1086 s for phase constraints, after confirming residual coverage of all 124 output events.
