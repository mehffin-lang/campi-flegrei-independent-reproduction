# Current limits

The PDFs and both supplied ZIPs are readable. Original observations are now permitted and INGV FDSN retrieval succeeds. Previous blanket statements that raw observations are prohibited are superseded by docs/INPUT_POLICY.md.

External access:
- INGV landing page: curl TLS issuer verification error. Official webservices.ingv.it works with normal verification.
- RAN: public pages accessible, waveform download requires registration/login; no credentials available.
- Temporary/local archive: available, but contains -5/+55-second cuts around authors' event origins. Those windows encode prohibited derived event selection; no continuous counterpart established.

Scientific and implementation limits:
- Only a calendar-selected day at four stations and written-method template windows processed. Other public channels and times are not assumed inaccessible.
- Full association/VELEST/TomoDD and focal inversion not implemented. No permitted validated initial/fixed velocity inputs established; author fitted products excluded.
- The documented magnitude inversion uses routine-catalog Md priors; comparison-only permission forbids this use. Relative magnitudes require another absolute anchor.
- Unspecified iteration/damping, correlation weights, exact templates/onset alignment, spectral display choices, time bins and geographic polygons prevent an exact workflow specification.
- Historic displacement observations for Fig.1B were not retrieved.

Do not describe a successful bounded build as successful full reproduction. S1, S2 and S15C are partial; all other publication groups are not reproduced. Model scores are not event counts or location estimates.
