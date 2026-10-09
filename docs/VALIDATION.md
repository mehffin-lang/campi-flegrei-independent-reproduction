# Validation and failed attempts

Source gate: both local PDFs extracted, all main and supplementary captions identified, source checksums unchanged; both supplied ZIPs directory-listed and CRC-checked without execution. Retrieved inputs verified by SHA256 before processing.

The first observational rebuild completed calculations and PDF compilation but failed the explicit layout check on two overfull boxes (0.15923 and 6.35725 points). The text and panel-label wrapping were corrected.

Review also found that the initial template scan rejected every hourly file because it required exactly 360000 samples starting at the requested boundary. Actual miniSEED blocks can begin later. The corrected scan uses the intersection of the two stations' actual recorded intervals, verifies equal sample counts, records every searched interval, and requires all 24 hourly intervals to be represented. The initial zero-candidate result was discarded. No archive-derived event was used to debug this logic.

Post-generation visual comparison with the published S15 reference showed that the method-defined E1/E2 templates differ from the examples in published S15A/B. Those panels were downgraded to not reproduced. Their generated plots remain related observational examples. S15C remains partial because its processing/display settings are not fully specified. No times or numerical values were extracted from the image to revise analytical inputs.

Final computational outcomes are in data/build_status.json and data/build_log.json. The final rebuild includes source checks, 27 C++ equation checks, observational normalization/Parseval/probability checks, template self-correlation/gain checks, actual template-scan coverage checks and PDF/layout validation. These are consistency checks, not ground-truth validation of detections or event locations. Full scientific reproduction remains incomplete.
