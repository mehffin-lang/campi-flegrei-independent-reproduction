# Current provenance

Primary scientific sources: unchanged local tanmodel.pdf and tanmodelsupp.pdf. Exact sizes/hashes and ZIP directories: file_inventory.json. ZIP numerical products and interactive plot are excluded.

Raw observations and station metadata: official INGV FDSN endpoints, every request and SHA256 in observation_inputs.json. Selection: one calendar day chosen without a catalog; six CAAM/COLB windows around method-specified template times. Independent outputs: data/observations; own scripts: retrieve_observations.py, analyze_observations.py, plot_observations.py. Generic ObsPy/SeisBench packages and permitted trained tensors implement data reading/model inference; versions pinned.

Model artifact: iamharrison2000/Campi-Flegrei-Earthquake-Monitoring commit f84c9c9dc6bb1501a95a833f6634199a63d4f3b3. Tree classified before selectively downloading permitted weights, configuration, coordinate-only station metadata and written README. No study code or derived outputs read. Full classifications in INPUT_POLICY.md.

Paper figure images do not enter calculations or plotting. No digitization; any post-generation visual comparison supplies no input values. No model training or catalog-derived tuning performed. RAN credentials absent; local-station event-selected archive not used for independent discovery.

Retained C++ fixture outputs are independently chosen analytic tests only. No fixture value is used to manufacture an empirical figure. Build and science statuses are separate in data/build_status.json.

A published S15 page was inspected only after our waveform/spectral figures had been generated. It was used to assess correspondence, not to select new data windows, extract plot values or change processing. The comparison led to downgrading A/B rather than substituting their published example times as inputs. The reference image remains an ignored local intermediate and is not embedded in the report.
