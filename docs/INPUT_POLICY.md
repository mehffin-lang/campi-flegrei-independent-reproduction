# Current input policy and classifications

The newest instruction permits original waveform observations, station metadata, general PhaseNet/GaMMA tools and the retrained model artifact. This supersedes the previous prohibition on all original source data. It does not permit derived catalogs, picks, associations, velocity estimates, location products or plotting code.

Both local PDFs were re-extracted successfully before analysis. All main captions 1–4 and supplementary captions S1–S15 remain readable. The ZIPs were listed and CRC-checked without extraction or execution. Their exact members and checksums remain in file_inventory.json. Data S1 is the derived event catalog, S2 associated phases, S3 focal mechanisms; the HTML is a derived interactive seismicity plot. None enters the analysis.

The model repository tree at f84c9c9dc6bb1501a95a833f6634199a63d4f3b3 was classified before downloads:
- models/phasenet_retrained.pt and .json: expressly permitted pretrained model weights/configuration; downloaded, tensor-only loading.
- models/stations.csv: permitted station metadata; downloaded.
- README.md: written model usage documentation; inspected. It specifies a 1 Hz highpass before inference.
- code/*: study-specific picking/association scripts and notebooks; not downloaded or read.
- output/*: derived catalog, phases, polarities, mechanisms and plot; not downloaded or read.
- models/1d_vmod_velest.mod and models/3d_vmod: velocity estimates; excluded.
- models/stations_velest.dat: includes fitted station corrections; excluded.

Independent code uses the permitted SeisBench implementation of PhaseNet to execute the supplied model. This is independent processing, not independent network training. The general AI4EPS tool repositories were accessible; GaMMA was not run because a compliant, validated velocity specification and complete relocation workflow have not been established. No catalog entries are used to seed any stage or select the validation day.

The INGV-OV temporary/local archive is reachable and advertises 3,293,243,207 bytes. Its landing page explicitly describes waveforms cut from -5 to +55 s around the authors' detected origin times. Those are observational samples with author-derived selection. They are excluded from independent discovery, rather than silently treating that selection as a continuous record. The full archive was not downloaded. Listed stations: V0105, V0102, CRUS, CROS, CMDP, CFB1, CFB3, CREM, CSOC, CLAC, CGAU. A continuous version would be needed for unbiased discovery with these stations.

The RAN login page explicitly requires registration/login to download SAC/ASCII waveforms. No account credentials were available or created. The INGV landing page failed local TLS issuer verification, but the official webservices.ingv.it FDSN endpoints succeeded with normal certificate verification. No certificate checks were disabled.

Calendar-selected 2024-01-01 at CAAM, COLB, CSOB and CSTH is a bounded validation run, not the full three-year catalog. The three short template windows use times explicitly given in supplementary methods S9, not times mined from author result files. Templates do not seed the PhaseNet validation-day analysis. Every actual retrieved channel segment and gap is recorded; metadata validity intervals are not described as continuous data coverage.
