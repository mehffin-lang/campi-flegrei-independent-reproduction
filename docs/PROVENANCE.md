> Historical baseline record. The current continuation updates are in [CONTINUATION.md](CONTINUATION.md), the post-supplement report documentation, and `data/continuation/`. Preserve the settings below as provenance for the earlier independent subset; they are not the current completion record.

# Current provenance

Primary specifications are the unchanged local `tanmodel.pdf` and `tanmodelsupp.pdf`. The source gate verified text, methods, captions, sizes and hashes before replacing outputs. Both uploaded ZIPs were listed and CRC-tested without execution. `docs/resumed_source_check.json` records the inventory. Data S3 was read only for a final count audit: 74 rows and 58 gCAP entries. No supplied solution is an analysis input.

The exact rebuild snapshot is `docs/rebuild_inputs.json`, with source URLs, paths, byte counts and SHA-256 hashes. `scripts/restore_inputs.py` restores or verifies it. Large files remain ignored in `inputs/`; project intermediates stay inside the repository. Live source pages can change, and a mismatch requires an explicit new provenance audit.

Original IV/2I waveforms and responses come from official INGV FDSN services. The retained four-station calendar day is supplemented by four calendar-selected half-hour network windows and two complete daily station files. Dates do not come from author catalogs. `docs/extended_*.json` records actual success, no-data responses, server errors and timeouts. All 26 full-period requests were tried and exceeded the server's sample limit; multiyear chunked acquisition remains unfinished. Actual segment unions are in `data/extended/coverage_summary.csv`.

Permitted model release: `iamharrison2000/Campi-Flegrei-Earthquake-Monitoring`, revision `f84c9c9dc6bb1501a95a833f6634199a63d4f3b3`. Its tree and README were classified before downloading retrained tensors/configuration, coordinate-only station metadata and a candidate fixed external 3D background. The paper attributes the fixed background to Battaglia et al. (2008); original-release byte provenance is unverified. Regional averages are an alternative association profile, not Tan's fitted model or a verified copy of Calo--Tramelli's initial profile. No Tan study analysis/plotting script was used.

Generic GaMMA is pinned to `80394dd4a4c29450da599f507916ecf1db6203dd`; installed core files were compared with that checkout. Generic original PhaseNet weights are the SeisBench conversion of Zhu et al.'s original artifact (`docs/baseline_model_inputs.json`). An unlabeled inference comparison is not a training reproduction. Generic VELEST builds with documented platform-only changes; compilation is not a scientific inversion.

Historical leveling is parsed from Del Gaudio et al.'s original publisher DOC table. Original RITE GNSS observations come from De Martino et al.'s publisher ZIP. The December 2023 official monitoring bulletin supplies a separate written approximate uplift estimate. A later interpolated displacement compilation was inspected for provenance and excluded from plotting. Source receipts and the GNSS archive listing are committed.

Routine INGV catalog pages are isolated as historical context/final comparison and as the documented potential Md regularization reference after independent association. They do not seed, filter or tune picking/association. No calibrated magnitude is copied from them without measured amplitude-difference equations.

Paper figure images do not enter calculations or plotting. No digitization; any post-generation visual comparison supplies no input values. No model training or catalog-derived tuning performed. RAN credentials absent; local-station event-selected archive not used for independent discovery.

Retained C++ fixture outputs are independently chosen analytic tests only. No fixture value is used to manufacture an empirical figure. Build and science statuses are separate in data/build_status.json.

The final Data S1 comparison reads only event ID, time, latitude and longitude after independent outputs exist. A fixed two-second temporal window identifies unique candidate matches; geodesic horizontal differences quantify initial-location disagreement. The reference never changes an event, parameter, filter or panel. A hash assertion checks the independent catalog before and after comparison. Outputs are isolated under `data/comparison/`, and reporting invokes this comparison only after independent processing.

A published S15 page was inspected only after our waveform/spectral figures had been generated. It was used to assess correspondence, not to select new data windows, extract plot values or change processing. The comparison led to downgrading A/B rather than substituting their published example times as inputs. The reference image remains an ignored local intermediate and is not embedded in the report.

Published Figure 1B was visually inspected after the historical plot existed. It supports a qualitative comparison of episode timing and shape. The numerical datum offset of 3.464 m comes from the original leveling table, not the figure. No source data or plotted values changed as a result of that inspection.
