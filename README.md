# Independent Campi Flegrei reproduction

<!-- holdout-review -->
The latest [training review and PDF synchronization](docs/SYNC_VELOCITY_REVIEW.md) adds 36 continuous channel-hours and 1,085 picks, but no new association. Six ambiguous training arrivals and one uncertain coda association are excluded; the unchanged event screen leaves **51 events/816 arrivals**. All 18 fits ran before evaluating the unchanged 2025 arrivals. The zero-delay trial changes holdout RMS **0.2432 → 0.2271 s**, but depth sensitivity is **1.09 km**, with **0.56 km** change under additional training iterations. **No profile is validated.** CSOC/CUMA P/S remain absent; seven other target pairs retain one observation each. Both PDFs use the same current figure files and 63 panel statuses, with hashes and timestamps in `report/document_build.json`. Rebuild the [report](report/report.pdf) and [comparison](report/comparison.pdf) from saved results with `.venv/bin/python scripts/present_velocity_sync_review.py` followed by `.venv/bin/python scripts/build_documents.py --clean`.

The preceding [53-event training extension](docs/TARGETED_VELOCITY_TRAINING.md), earlier [52-event tests](docs/VELOCITY_HOLDOUT_REVIEW.md), and empirical panel checkpoints are preserved.
<!-- /holdout-review -->

<!-- availability-current -->
The following is the **preserved catalog-generation checkpoint**. Its fitted model remains the disclosed input behind Figure S6; the later velocity tests above do not promote a replacement.
It processes **1,327 eligible files, 14,080.521 channel-hours,
256,720 picks and 3,296 associations**.
The new independent 1D velocity fit uses 46 balanced pre-2025 training
events and 62 separate 2025 holdout events. Training RMS decreases
from 0.2082 to 0.1759 s;
holdout RMS changes from 0.2406 to
0.2778 s. **The model is not accepted.**
Figure S1 shows expanded coverage; Figure S6 and Table S1 show the new provisional fit/location experiment;
the other relocated, magnitude and mechanism panels retain their older checkpoint.

Public retrieval continues separately with a fixed 40 GiB free-space reserve.
At the recorded snapshot, 71 new files add
1,059.305 raw union channel-hours. Later receipts and picking
are not automatically counted as associated or calibrated observations. Remaining
advertised coverage is approximately 1,210,260
channel-hours (0.96 TB at the measured compression rate).
No full-period coverage or accepted structural result is claimed.

- [Current input/model pointer](data/availability_extension/current_analysis.json),
  [source and resume procedure](docs/AVAILABILITY_EXTENSION.md),
  [coverage and gaps](data/availability_extension/coverage_summary.json).
- Current verified-output rebuild: `.venv/bin/python scripts/rebuild_availability_extension.py`.
- For a new cohort and complete numerical rerun, use that command with
  `--run-analysis --catalog NEW_PATH --profile NEW_PATH`; preserve earlier versions.

The following paragraphs describe the **preserved earlier EIDA checkpoint**.
<!-- /availability-current -->

The preserved 14 October EIDA checkpoint contains **1,285 eligible continuous files, 26 station names, 13,467.933 union channel-hours, 246,668 picks and 3,271 provisional GaMMA associations**. All 14 known event-selected snippets are excluded from detection and exposure. The continuation made 276 new requests: **275 downloads (3.481 GB), one HTTP 204, and no new failures or duplicate requests**. There are **73,641 pending requests**; full-period retrieval is unfinished, not demonstrated inaccessible. RAN and the exact Calò–Tramelli profile remain deferred as instructed.

Independent calibration selected 552 events; 1,435 whole-catalog locations pass the numerical filters. Both fixed-grid TomoDD rounds ran and retain **1,050 provisional events**, compared with 123 previously. There are **352 conditional regional SVD estimates and 868 provisional amplitude-inversion magnitudes**. No calibrated structural result is scientifically accepted: identical-input precision paths differ by up to 0.85 km in depth, regional starts by 1.52 km, and the iteration-stability gate fails. Held-out RMS falls from 0.2403 to 0.2081 s, but this same-swarm check does not validate absolute depths. The new trial has 16 events deeper than 5 km; none is hidden by fixed plot colors. Numerical growth is not demonstrated improvement in location accuracy.

The Figure 4 continuation reviewed 303 station-event records for 14 own candidates. **99 AI-reviewed polarities and 108 S/P measurements** yield **two quality-D SKHASH solutions** and **12 FK/gCAP trials in each frequency band**. There are zero human reviews and zero accepted scientific mechanisms. Low/high-band variance reduction is 1.3–14.4% / 1.4–9.1%; orientations change by 45–95°. The four own SKHASH–gCAP comparisons are 35.6–79.1°, above the paper's 30° agreement criterion. Eight additional AI arrival marks are downstream-only and never enter the detection catalog. Every candidate's unmet requirements are saved.

The CAAM/COLB scan covers 140.656 common hours and returns 1,843 unconfirmed threshold crossings. AI inspection of the 36 displayed candidates does not establish confirmed hybrid families. The catalog-wide spectral screen measures 3,270 of 3,271 provisional events; negative frequency indices are not source classifications. A newly generated S15D analogue uses an independently associated waveform example, with source type and shallow depth explicitly unvalidated.

**The paper is not fully reproduced. Both PDFs remain provisional.** Current counterparts update Figures 2–4, S1, S6–S8, S10–S14 and S15D. S11 has three nonempty sampled windows; its fourth remains unavailable. S9 has no event with at least 100 correlated phases. Other context and training gaps are unchanged. S15A–C retain their numerical observations with corrected common amplitude axes. Routine events in 1A/1C/S5 remain external context; routine duration magnitudes enter only the documented downstream calibration role. Published images occur only in the separate comparison PDF.

- [Scientific report](report/report.pdf), [LaTeX source](report/report.tex).
- [Figure comparisons only](report/comparison.pdf), [LaTeX source](report/comparison.tex).
- [Current numerical summary](data/eida_continuation/result_summary.json), [executed stages](data/eida_continuation/pipeline_execution.json), [panel inventory](docs/panel_record.json).
- [Mechanism requirements](data/mechanism_eida/candidate_requirements.csv), [AI review evidence](data/mechanism_eida/new_visual_review.json), [mechanism validation](data/mechanism_eida/validation.json).
- [Current procedure and limitations](docs/EIDA_CONTINUATION.md), [replacement record](docs/REPLACEMENTS.md), [request outcomes](data/eida_continuation/request_station_month.csv).

Previous numerical cohorts, figures and assessment remain preserved. Their counts are not additive. The current starting grid is the explicitly authorized Tan-distributed, Battaglia-attributed resource; its original bytes, source and dimensional discrepancy are recorded. It is not Tan's fitted model. The failed negative-bulk-modulus calibration and generic solver failures are preserved in hashed archives.

## Rebuild the preserved 14 October checkpoint

Use the repository's Python environments and generic method dependencies described in [EIDA_CONTINUATION.md](docs/EIDA_CONTINUATION.md), [CONTINUATION.md](docs/CONTINUATION.md) and [GRID_WORKFLOW.md](docs/GRID_WORKFLOW.md). From the project root:

```bash
# Verify original local observations; --download restores missing public files.
.venv/bin/python scripts/restore_eida_observations.py

# Verify executed numerical outputs, regenerate figures, and compile both PDFs.
.venv/bin/python scripts/rebuild_eida_followup.py

# Explicitly rerun the frozen numerical workflow, then figures and both PDFs.
.venv/bin/python scripts/rebuild_eida_followup.py --analysis
```

The default build checks original observation, configuration, processing and numerical-output hashes. It does not rerun the full scientific calculation. The numerical stages were actually executed in this continuation, including recorded failures and resumptions; their receipts are distinct from the presentation rebuild. The `--analysis` path reuses inference/association only after exact input/configuration checks, and refuses to reuse visual decisions if numerical waveform windows change. It neither downloads waveforms nor performs human review. Large original inputs stay under ignored `inputs/`, with public URLs and SHA-256 receipts.

For a document-only rebuild from saved figures:

```bash
.venv/bin/python scripts/build_documents.py --clean
```

Do not build documents while scientific outputs are changing. The manuscript follows main paper → reproduced supplement → supporting documentation. The comparison PDF contains 19 ordered figure comparisons only. Missing results are explicit notices, never fabricated empirical plots. Build results and file/order checks are saved in `data/eida_continuation/rebuild_result.json` and `report/document_build.json`.

## Input boundaries

Permitted resources include original waveform/GNSS observations, public metadata, trained PhaseNet weights with pinned attribution, and generic method software. Routine INGV duration magnitudes are external calibration priors, not independent magnitude observations. Tan-derived catalogs, phases, fitted models and focal mechanisms are not current analysis inputs. The current rebuild does not compute statistics from Tan result tables. Superseded comparisons are archived only as an audit trail.

Synthetic and analytic fixtures are kept in [tests/results](tests/results), never empirical catalogs or paper figures. Rejected numerical experiments are under [data/exploratory](data/exploratory), with explicit acceptance flags. The old grid-dependent entry points are disabled; Git preserves their history.

Project caches and intermediates are in `tmp/`; dependencies are in `.venv/` and the isolated `.venv-skhash/`. Standard pip cache: `/home/mehffin/.cache/pip`. An early import created `/home/mehffin/.seisbench`; current runs redirect that cache into the project. Nobody has been contacted on the user's behalf.
