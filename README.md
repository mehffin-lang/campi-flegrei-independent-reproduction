# Campi Flegrei: independent observational reproduction

The scientific reproduction remains **incomplete**. The current continuation reconstructs Figures 1A--C and S5 from expressly permitted routine-catalog and displacement observations, extends daily RITE GNSS through 20 March 2025, and expands independent waveform inference. It does not claim a completed multiyear relocated catalog or focal-mechanism set.

Read the [current report](report/report.pdf), [comparison-only PDF](report/comparison.pdf), [continuation and rebuild instructions](docs/CONTINUATION.md), [panel record](docs/panel_record.json), [velocity-profile search](docs/velocity_profile_search.json), and [replacement record](docs/REPLACEMENTS.md). Current executed counts are in [analysis](data/continuation/analysis_summary.json), [retrieval checkpoint](data/continuation/acquisition_checkpoint.json), [downstream attempts](data/continuation/downstream_summary.json), and [rebuild outcome](data/continuation/rebuild_status.json).

**Partial panels:** 1A--C, S1, S2, S5 and S6 (all three views), S8A--B, S15C. Remaining panels are explicitly unreproduced. The routine-catalog reconstructions are external routine records, not independent event detections. Failed or pending waveform requests never count as coverage.

## Build both PDFs from the saved results

The paper follows Tan et al.'s main section sequence and Figures 1–4, then the original supplementary topics and Figures S1–S15. Full methods, access/provenance records, supporting numerical tables, diagnostics, limitations, panel status and rebuild details follow the reproduced supplement. Missing results remain labeled placeholders. The separate comparison PDF contains only 19 figure comparisons, in publication order, labeled **Published reference** and **Independent result**.

From the repository root, with the existing environment and committed source documents/results:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

This **presentation-only build** runs no scientific analysis and preserves the saved data, figures and analytical scripts. It requires Python with Pillow (already pinned), `pdftoppm`, `pdftotext`, and `pdflatex`; it uses no network access. It renders figure crops from the local supplied PDFs strictly for display in the comparison PDF, generates figure placeholders, compiles each PDF twice, and checks the final section/figure order, reference-image isolation and unchanged analysis-file hashes. `--clean` removes only document products. Generated reference crops remain ignored in `report/reference_assets/` and are recreated from the supplied PDFs.

Sources: [report/report.tex](report/report.tex), [main paper](report/main_paper.tex), [reproduced supplement](report/reproduced_supplement.tex), [post-supplement documentation](report/reproduction_documentation.tex), and [report/comparison.tex](report/comparison.tex). The shared [figure layout](report/figure_layout.json) records the exact mapping. Generated LaTeX fragments are retained alongside the sources. See [layout/replacement details](docs/REPORT_LAYOUT.md), [document build result](report/document_build.json), and [build commands/log](report/document_build_log.json).

## Rebuild the current scientific checkpoint

Requirements: Python 3.11, g++, gfortran, curl, Git, antiword, Poppler and pdflatex. Run from this repository:

```bash
mkdir -p tmp
python3.11 -m venv .venv
TMPDIR="$PWD/tmp" .venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu -r config/requirements-resume.txt
.venv/bin/python scripts/restore_inputs.py --continuation
.venv/bin/python scripts/rebuild_continuation.py --fresh
```

The frozen source snapshot preserves routine-catalog HTML, GNSS observations/notes and metadata in `sources/continuation_context_inputs.zip`. Large waveform observations are restored using exact URLs and hashes. Existing inputs are verified before any outputs are replaced. This rebuild covers the actual downloaded checkpoint, not the full unprocessed three-year queue. A live endpoint returning different bytes causes an explicit hash failure rather than silent substitution.

Continue the calendar-driven full-period retrieval, independent of every event catalog:

```bash
.venv/bin/python scripts/collect_continuous.py plan
.venv/bin/python scripts/collect_continuous.py run --workers 6
.venv/bin/python scripts/collect_continuous.py summary
```

Collection is resumable and leaves a 20 GiB free-space reserve. The 74,445-request plan is not completed coverage. See `docs/CONTINUATION.md` before extending the frozen checkpoint or processing further inputs. The old `scripts/rebuild.py` and `data/extended` preserve the previous workflow; use the continuation command above for the current deliverable.

The exact numerical Calò--Tramelli (2018) profile remains unavailable in the sources inspected. A verified published alternative from Tramelli et al. (2021), Table 1, is labeled explicitly; it is not the Tan-fitted model. The velocity search record specifies the precise INGV table to request and identifies its authors. Nobody was contacted. RAN waveform access still requires unavailable registration credentials.

## Integrity and provenance

Neither science.adw9038 ZIP was executed. Data S1--S3 do not seed analysis. A final Data S3 row-count audit found **74 rows and 58 gCAP entries**, resolving the difference between the methods and the erroneous 55-event caption. No author solution values were inputs. No Tan analysis/plotting script or digitized published figure was used.

After independent processing, `scripts/final_comparison.py` reads Data S1 solely for final time-match and horizontal-difference assessment. Its separate `data/comparison/` outputs never feed back into analysis; reference matching does not change the generated catalog or panels. The current downstream VELEST comparison is saved separately in `data/comparison_continuation/`; the historical nine-event conclusions are not reused.

Generic GaMMA is pinned to `80394dd4a4c29450da599f507916ecf1db6203dd`; the trained-artifact/background release is pinned in the input receipts. VELEST's generic upstream source is downloaded, inspected and built with documented platform repairs, increased event capacity, bounds checks and 64-bit arithmetic. Compiler warnings, numerical failures and outcomes are recorded separately from scientific execution.

Project intermediates and SeisBench, matplotlib and numba caches live in `tmp/`; the environment is `.venv/`. Standard pip cache: `/home/mehffin/.cache/pip`. An earlier initial SeisBench import created `/home/mehffin/.seisbench`; current runs redirect its cache into the repository. The repository, Git history, uploaded source files and unrelated work are preserved.
