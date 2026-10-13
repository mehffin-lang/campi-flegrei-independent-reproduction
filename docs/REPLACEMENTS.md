# Current provenance correction and observational expansion

This revision supersedes the provisional checkpoint at `ff7586a3bb8c8b24bbb06b47f167cce6bbc89d11`. Git history and useful source observations are retained. Earlier entries below describe earlier runs, not the current acceptance status.

- Replaced `figures/continuation_stations.pdf` and `data/continuation/figure_S2.csv`: audited every candidate identifier/epoch, corrected official coordinates, masked distant coastline vertices, applied a local projection and readable numbered labels. New per-identifier QA/epoch tables preserve unresolved metadata.
- Replaced `data/continuation/historical_leveling.csv`, Figure 1B and the combined Figure 1: added original date/uncertainty strings and separate survey, estimate and reconstruction classes. The numerical source elevations and GNSS observations are unchanged; no digitization was performed.
- Withdrew `figures/figure_S6_pilot.pdf`, `data/continuation/figure_S6.csv`, previous fitted regional models/corrections and locations. Moved the unverified grid, regional averages, old grid-dependent associations and downstream results to `quarantine/unverified_background`; its manifest records exact previous paths, sizes and SHA-256 hashes. Neither those data nor their PNG diagnostics remain current empirical results.
- Moved synthetic/analytic CSV/JSON/LaTeX fixtures to `tests/results`; moved injected-waveform assertions to `tests/template_assertions.py`. They remain software checks, not observations.
- Quarantined old `data/comparison*` products and their LaTeX text. Removed author-result-table statistics from the scientific report and disabled the old result-table comparison entry point. Published reference crops remain comparison-only.
- Regenerated the frozen input manifests, request/coverage ledgers, picks, initial associations, amplitude/magnitude calculations, statistical outputs and current figures after expanding observations. Pending/failed/no-data requests are never filled. Magnitude measurements now include available stations without associated picks and retain conditional formal uncertainties and rank checks.
- Added public RAN metadata for 17 station codes (860-member archive inventoried; selected XMLs/HTML frozen). S2 now has 42 exact metadata matches and nine unresolved identifiers; no RAN waveform credentials were supplied.
- Added separate alternative-profile VELEST precision/physical-validity experiments, CPOZ diagnostic gathers, template-candidate spectra and provisional catalog station-averaged frequency indices. These diagnostics do not complete S6/S7/S12/S14 or focal processing.
- Replaced `report/report.pdf`, `report/comparison.pdf`, their generated figure fragments, panel records and supporting tables. Removed placeholder figure boxes from the scientific paper, retaining text notices and original numbering. The 19-page comparison-only document retains explicit missing-result placeholders. Both PDFs remain provisional.
- Disabled superseded grid-dependent build/plot/table entry points. `scripts/rebuild_continuation.py` is the current clean procedure. Original PDFs, uploaded ZIPs, eligible waveforms/metadata, Git history and unrelated work are preserved.
- Replaced repeated amplitude-stage file decoding with bounded, unmodified waveform caches in sixteen spawned workers. A 60-window sample/time equivalence check precedes execution. The direct-read attempt was intentionally stopped for this performance change; its failed-stage record is retained, and passed inference/association hashes were checked before resumption.

The exact current changed-file inventory is `docs/revision_changes.json`. Access/source receipts, local ZIP waveform inspection and grid provenance are recorded separately in `docs/revision_access.json`, `local_waveform_receipts.json` and `background_grid_provenance.json`. Final build checks are `data/continuation/rebuild_status.json`, `provenance_validation.json` and `report/document_build.json`.

---

## Earlier replacement records (superseded)

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

Important corrections: the INGV Md calibration exception is now permitted; fixed external backgrounds are distinguished from Tan's fitted products; full-period HTTP 413 is a chunking limitation, not proof of inaccessible data. The historical Data S3 count assessment is now quarantined, not retained as a current scientific claim. A coverage-aggregation development bug caused by pandas' variable timestamp precision was corrected before delivery, with an explicit sample-duration consistency assertion.

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

## Current scientific resumption

The source-readability gate and author ZIP inventory were repeated before replacements. No author ZIP content was executed or used in analysis. Existing main/supplement PDFs, source uploads, guidance, useful observations, Git history and the separate `assessment/` deliverable are preserved.

This run supersedes the preceding 608-file, 908-provisional-event checkpoint. Its saved summaries/build log and selected waveform-review evidence are preserved under `data/resumption/`. The current frozen input set adds 217 successful segmented files from 240 requests; 23 additional HTTP 204 responses add no coverage. Actual current counts are generated by the rebuild, not inherited from those baseline numbers.

Replaced current `data/continuation/` picks, associations, coverage, amplitude/magnitude calculations, provisional-location checks, hybrid scan tables, generated panel files, report tables and both report PDFs through the documented rebuild. Added explicit finite PhaseNet-score coverage, causality flags and observed waveform examples, exploratory coherency-weighted differential times, and a partial S4A original/retrained inference comparison. No differential-time measurement is called a relocated event. Benchmark picks are separate from catalog picks.

The CPOZ diagnostic replaces the earlier single-component, 1–15 Hz display with both HHZ and HHN, eight seconds aligned on independent P picks and filtered above 4 Hz. It remains a diagnostic rather than a reproduced sector panel. The VELEST precision comparison now examines horizontal position, origin time and RMS as well as depth and velocity; the prior depth-only agreement claim was insufficient. Causality-failed associations no longer contribute magnitude equations, routine calibration priors or the exploratory VELEST calibration subset. Individual station scores are retained for hybrid crossings; six baseline examples are explicitly reviewed without claiming confirmed hybrids.

`figure_S4A.pdf` and its saved arrays/picks are added as a partial inference comparison; S4B and all training panels remain unavailable. All scientific figure captions and status records retain the partial labels. Diagnostic figures stay outside the main paper and reproduced supplement. The unverified 2008 grid and dependent earlier S6 outputs remain quarantined. Current figures never use authors' numerical results or test fixtures. Source receipts, model-artifact classification, restoration bundle, methods and blockers are updated. Full multiyear acquisition/processing and accepted location/relocation/mechanism analyses remain incomplete; the actual rebuild status is authoritative.

After the expanded frequency-index calculation, all nine negative-mean candidates received saved observational review windows and qualitative inspection notes. These additional diagnostic files do not replace publication panels or classify events automatically. The report records the observed noise/coda concerns. S2's identifier-key clipping was corrected without changing numerical station coordinates.

A current association attempt was deliberately stopped after inspecting the permitted GaMMA library's worker-level random initialization. `scripts/gamma_reproducibility.py` resets the numerical initialization seed to 42 plus the deterministic DBSCAN label for each cluster. This disclosed choice changes no observations or likelihood equations and uses no Tan analysis code. `tests/check_association_repeatability.py` compares serial and parallel association on two observation windows selected from this project's own baseline review, with different parent random states. It is a repeatability check, not labeled detection accuracy. Association and dependent products are rebuilt; compatible inference caches are retained. The interrupted stage is preserved as return code −15 in the rebuild-attempt history.


## 13 October 2026 calibration and plotting follow-up

Replaced `figures/figure_1A_routine.pdf`, `figure_1_combined.pdf` and `figure_S5_routine.pdf` with the same saved routine-catalog values using published-style depth colors, magnitude symbols and map/section layouts. Updated `data/continuation/routine_plot_scope.csv`, style receipts, panel records, generated report fragments, `report/report.pdf` and `report/comparison.pdf`. Updated live acquisition receipts and coverage after 43 additional successful requests and five no-data responses. Other eligible figure PDFs were rebuilt from their unchanged saved data.

Added independent exploratory outputs under `data/calibration_followup`, including rejected calibration/convergence trials and HypoDD diagnostics; these do not replace accepted catalogs because no calibrated catalog passed validation. New expanded picks/associations have a separate identifier space. Preserved the earlier `data/continuation` seismic cohort, its magnitudes and hybrid products, all useful original observations, prior quarantine evidence, and `assessment/`. No Figure 3, 4A--B, S6 or S7 scientific counterpart was manufactured. The HypoDD arithmetic fixture remains isolated in `tests/`; new diagnostic figures occur only after the supplement. Earlier versions remain in Git history.

Updated the S1 counterpart to `figures/followup_coverage.pdf`, generated from the expanded observed coverage table; the older `continuation_coverage.pdf` remains as a frozen-checkpoint artifact.

## Authorized-grid and complete plotting revision

Added `data/grid_calibration/` and the corresponding prepare/run/validate/rebuild scripts. Preserved the original reference-grid bytes, earlier rejected trials, source observations, independent pick/association checkpoints and Git history. Replaced all current files under `figures/` with renderings from their saved numerical inputs; added a separately labeled grid-trial diagnostic. Updated report/comparison PDFs and included sources, panel records and current documentation. Routine, displacement, magnitude and hybrid numerical source tables were not changed by styling. The initial unconverged-model whole-catalog trial was superseded by the converged-model handoff; its early provisional counts were not promoted. Failed eight-layer, fixed-width serialization and TomoDD unclosed-file attempts remain in the new audit trail. No old author-derived fit or comparison image was used to create a new empirical output.

The initial TomoDD residual file represented only the last cluster. Appending all cluster residuals and recomputing gaps from retained positive-weight observations supersedes the 126/125 gap-pass counts with 124/123. These own preliminary diagnostics are retained in `data/grid_calibration/superseded_last_cluster_diagnostics.json` and archived run files; none was promoted to a validated publication result.
