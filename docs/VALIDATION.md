# Current validation and execution records

The current scientific checkpoint remains provisional. Authoritative outcomes are `data/continuation/rebuild_status.json`, `rebuild_log.json`, `provenance_validation.json`, and `report/document_build.json`; these distinguish executed checks from scientific completion. Earlier results below are superseded historical records, not the current CPOZ, displacement, magnitude or coverage findings.

The continuation procedure checks both readable PDFs and ZIP integrity, frozen input hashes, probability bounds and prescribed S exclusions, unique associations with at least six picks, actual interval unions, and response-epoch coverage. It runs 27 C++ equation assertions, layered vertical-ray refinement checks, a known-event homogeneous association test, and 60 observed-window read-equivalence checks. Synthetic and analytic inputs/results stay in `tests/`; they are not empirical detections or figures.

Current saved-result checks verify partial-panel file/command chains, exclusion of quarantined and comparison/test material from those chains, weighted magnitude normal equations, and agreement between station frequency indices and their saved event means. Document checks verify section/figure order, all 19 comparison pages, and comparison-only use of published images. These checks do not prove that unexamined or hidden inputs were never used, or establish observational event accuracy.

Both VELEST real precisions are tested separately under `data/exploratory/velest_stability`. Numerical agreement is not physical validation; no experimental fit is accepted for S6 or relocation. CPOZ gathers and low-frequency screening remain unreviewed diagnostics. Counts come from the current saved summaries, not the historical values below.

The current fresh build required repairs to SQLite ledger compatibility and null handling. An amplitude attempt was intentionally interrupted for bounded file caching. A later completed measurement pass failed while serializing a NumPy Boolean in the inversion-check record; the explicit Boolean conversion was repaired and the stage rerun with sixteen spawned workers; it was not an access failure. Failed/interrupted attempts and hash-verified resumption are retained in `data/continuation/rebuild_attempts.json`.

## Historical validation records (superseded)

Source gate: both local PDFs extracted, all main and supplementary captions identified, source checksums unchanged; both supplied ZIPs directory-listed and CRC-checked without execution. Retrieved inputs verified by SHA256 before processing.

The first observational rebuild completed calculations and PDF compilation but failed the explicit layout check on two overfull boxes (0.15923 and 6.35725 points). The text and panel-label wrapping were corrected.

Review also found that the initial template scan rejected every hourly file because it required exactly 360000 samples starting at the requested boundary. Actual miniSEED blocks can begin later. The corrected scan uses the intersection of the two stations' actual recorded intervals, verifies equal sample counts, records every searched interval, and requires all 24 hourly intervals to be represented. The initial zero-candidate result was discarded. No archive-derived event was used to debug this logic.

Post-generation visual comparison with the published S15 reference showed that the method-defined E1/E2 templates differ from the examples in published S15A/B. Those panels were downgraded to not reproduced. Their generated plots remain related observational examples. S15C remains partial because its processing/display settings are not fully specified. No times or numerical values were extracted from the image to revise analytical inputs.

Final computational outcomes are in data/build_status.json and data/build_log.json. The final rebuild includes source checks, 27 C++ equation checks, observational normalization/Parseval/probability checks, template self-correlation/gain checks, actual template-scan coverage checks and PDF/layout validation. These are consistency checks, not ground-truth validation of detections or event locations. Full scientific reproduction remains incomplete.

## Resumed-run validation

`scripts/validate_association.py` recovers a known analytic homogeneous-medium event from 16 P/S arrivals without using author data. `extended_analysis.py` checks probability bounds, prescribed S exclusions, minimum event pick counts, unique assignment and valid indices. `resume_inventory.py` unions actual channel intervals in explicit seconds and checks against sample-derived durations, avoiding pandas microsecond/nanosecond ambiguity. These tests do not establish observational detection accuracy or validate the alternative starting profile.

Actual location residuals and azimuthal gaps are saved in `data/extended/location_quality.csv`; actual amplitude/SNR measurements and failed pair formation are saved separately. Candidate waveforms are plotted and remain unconfirmed. Counts and method-stage status are generated from executed outputs, not code availability. The bounded rebuild's outcome is in `data/build_status.json`.

The original/retrained inference diagnostic verifies finite probability ranges and saves both models' outputs for independent CSOB/CMIS windows; no accuracy claim is possible without reference annotations. S–P diagnostics yield 17 independently assigned phase pairs, all with positive S–P, and a 0.634 s residual RMS against the same provisional model. This is internal consistency, not an independent location-accuracy validation. Zero associated CPOZ P picks means no eligible common-receiver gather can be made from this sample.

The original RITE observations align to 23 overlapping leveling epochs with a median datum offset of 1.78960 m and offset median absolute deviation of 0.00228 m. This checks datum consistency at overlapping epochs, not the accuracy of extrapolated observations; the daily series ends in 2019 and is not extrapolated.
