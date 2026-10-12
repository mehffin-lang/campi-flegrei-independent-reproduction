# Current input and result boundaries

The current procedure is `scripts/rebuild_continuation.py`. Earlier policy descriptions and outputs in Git do not establish current acceptance.

| Category | Current treatment |
| --- | --- |
| Original observations and public metadata | INGV IV/2I miniSEED and response epochs; public RAN station directory and selected response XMLs (waveform access remains credential-gated); daily RITE text observations and format notes from Zenodo 17132077 and 22259337; released station metadata, with official-coordinate QA; attributed Natural Earth coastlines. |
| External historical/contextual inputs | INGV routine snapshot for 1A, 1C and S5 only, and its documented post-detection duration-magnitude calibration role. Del Gaudio's numerical table retains 114 survey entries, 13 source estimates and one source reconstruction. These are not all raw observations. |
| Permitted methods | Released trained PhaseNet weights/configuration, generic SeisBench/GaMMA/VELEST and other method software, and published numerical Tramelli (2021) Table 1 as an explicitly exploratory alternative. Software examples and author study scripts are not analysis inputs. |
| Independently computed products | Our waveform picks, provisional associations, amplitude equations, conditional magnitude pilot, spectra and observational/contextual calculations. Their files and commands are recorded per panel; partial calculations are not accepted final locations or complete multiyear results. |
| Published references | Original paper/supplement as written specifications. Their figure images appear only in `report/comparison.pdf`, labeled Published reference. They are not digitized, used for tuning or placed in the scientific report. |
| Prohibited author results | Tan-derived phases, associations, catalogs, locations, fitted models, corrections, magnitudes, focal solutions, intermediate results and numerical figure data. No current empirical stage reads them. The uploaded ZIPs are listed and CRC-checked but never executed. |
| Quarantined results | The unverified 2008-attributed grid and all historical dependent products are under `quarantine/unverified_background`; old result-table comparisons are under `quarantine/superseded_comparisons`. Neither enters the current rebuild or scientific report. |
| Synthetic fixtures | Analytic arrays and injected test waveforms are isolated in `tests/`; they test software assertions only and never enter empirical catalogs, magnitudes or paper figures. |

The routine catalog never chooses waveform dates, seeds detections, filters the independent catalog or fills missing magnitudes. Unique time matches are considered only after independent association to provide the supplement's external Md regularization. This is calibration, not independent validation.

The local temporary archive was inspected without execution using bounded HTTP ranges, ZIP directory records, decompression and CRC checks. It contains 319,889 miniSEED members across seven station codes; seven observations were read for access/format inspection. Its author-event-selected windows cannot supply unbiased continuous exposure or independently seed discoveries. This does not prohibit every possible downstream use of the original traces, provided selection and metadata are resolved.

The author-distributed grid differs in geometry from the original 2008 written description. Its numerical equivalence, regridding and version are unverified. It is not in the current restoration manifest. The current VELEST precision experiment uses only the cited 2021 alternative and does not authorize S6 or downstream relocation; raw experimental results are separately labeled under `data/exploratory`.

No current stage computes statistics from Tan result tables. Earlier table-derived comparison statistics and their report fragments are quarantined solely to preserve the audit trail. The current comparison deliverable uses only visibly labeled published reference images alongside eligible outputs or missing-result notices.

Exact sources, versions and hashes are in `docs/rebuild_inputs.json`, `docs/continuation_rebuild_inputs.json`, `docs/file_inventory.json`, `docs/revision_access.json` and `docs/background_grid_provenance.json`. Local caches and large inputs are documented in `docs/CONTINUATION.md`.
