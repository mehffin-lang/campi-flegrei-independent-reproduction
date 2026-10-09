# Current blockers: permitted inputs, not PDF access

Both uploaded PDFs are now readable. Their identity and checksums are recorded in `file_inventory.json`; all main captions and S1–S15 captions were read. The two ZIPs can be listed and pass CRC checks. The old HTTP-access failure is superseded and is not the current blocker.

The task prohibits use of the authors' original source data and derived products as analysis inputs. Consequently:

- Main 1A/1C and S5 need the routine catalog used in the study; 1B needs the observed deformation series.
- Main 2/3 and S6–S13 need waveforms, station metadata, picks, catalogs, covariance estimates, or derived event locations.
- Main 4 needs polarities, amplitude ratios, observed waveforms, and focal solutions.
- S1/S2 need the actual station metadata and availability records. S3/S4 need the authors' training/validation traces and original/retrained network outputs.
- S8 needs matched observed magnitudes and the full event-magnitude sample.
- S14/S15 need actual hybrid waveforms, template events, station responses, observed times, and cluster membership.

Data S1, S2, and S3 are exactly the kinds of excluded catalog/pick/focal-solution inputs. Interactive Plot S1 is an authored plot with embedded output and code; it was not run or mined. No numerical archive rows were read. Metadata and CRC inspection are not scientific input use.

The permitted written equations support method checks on independently generated analytic fixtures. Those do not recreate the observations. Implementing a full neural-network workflow without its admissible training observations would not reproduce this study. No physical pressure/fault model is substituted.

Additional specification limits: regularization strength and cross-correlation weight mapping for magnitude inversion; exact training splits/seeds and close-overlap rejection rule; complete relocation damping/iteration/cross-correlation settings; time bins and geographic polygons; spectral taper/PSD conventions; event-dependent gCAP bands; and KDE bandwidths are not fully given in the descriptions read. Table S1 is a documented parameter model; Table S2 contains observed event results and is not used as numerical fixture data.

The report and panel record separate these specification limits from the stronger prohibited-input blocker. All manuscript and supplementary panels are marked not reproduced, not partially reproduced. The four M1 panels validate implemented equations only.
