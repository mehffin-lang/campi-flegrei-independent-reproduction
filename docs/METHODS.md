# Scientific specification and implementation limits

## Actual study

Main pp.70–75 and supplementary S2–S11 describe an empirical seismic-monitoring pipeline, not a coupled physical forward model. Speculative physical interpretations in the discussion are not evolution equations with initial/boundary conditions.

## Written workflow (not claimed fully implemented)

| Stage | Written specification | Source |
|---|---|---|
| Observations | 2022-01-21 to 2025-03-20; 23 broadband + 9 short-period + 16 accelerometers | S2 |
| PhaseNet retraining | final pools: 24547 local earthquake, 145292 noise, 102620 STEAD traces; 30-s windows; 60 epochs; learning rate 0.001; MSE | S2–S3 |
| Sampling | local earthquakes train/validate 0.8/0.2, other pools 0.95/0.05; per iteration 12000 noise, 4400 single-event, about8000 overlapping examples | S3 |
| Picking | score threshold 0.3; exclude S picks at CASE, CFB1, CFB3; reported P3252660/S5790284 | S3 |
| Association | GaMMA-1D; minimum6 picks; reported105944 events | S3–S4 |
| Initial location | 373 calibration events; two joint velocity/location/correction runs, three fixed-model runs; residual removal0.4 then0.3s; >=6 picks, RMS<=0.25s, gap<=300deg;61809 events | S4 |
| Relocation | fixed3D model; picked and coherency-weighted differential times; two TomoDD rounds; final54319 | S4–S5 |
| Uncertainty | HypoDD SVD on four subsets: central174/north165/southwest175/east166 | S5 |
| Magnitudes | SNR>=5dB from 5s signal,2s noise; >=2 common stations; separation<one-fifth hypocentral distance; amplitude ratios, correlation weights, Md regularization | S5–S6 |
| Focal mechanisms | SKHASH polarities and S/P, gCAP waveform inversion; high quality A or Kagan<30deg; TableS1 velocities | S6–S7 |
| Best locations | methods remove NCCP+NCCS<100; FigS9 caption says sum>100; reported38103 | S7–S8, S20 |
| Hybrid templates | three master events; CAAM/COLB;8s windows;0.2–6Hz; average correlation>0.25, manual review;70 events, clusters36/23/7 plus4unclustered | S9 |
| Frequency index | CAAM8s; low2–5Hz, high8–15Hz; log10 power ratio; reportedrange-3.32to1.09 | S10 |
| Hybrid magnitudes | maximum horizontal CAAM amplitude ratio to largest within-cluster event | S10 |

Table S1 documents interfaces at -0.30,0.50,1.00,1.50,2.00,3.00km; Vp=1.81,2.33,2.71,3.76,3.89,4.51km/s and Vs=1.02,1.02,1.46,2.21,2.49,2.96km/s. They are not used to invent a replacement location model. TableS2 event results and all archive data are excluded from numerical fixtures.

## Retained C++ equation consistency tests

Equations S2/S5: `delta_m=log10(A_i/A_j)`, valid for positive amplitudes with comparable propagation. Common gain cancels; absolute magnitude remains undetermined by pairwise differences.

Equation S3: `SNR=10log10(P_signal/P_noise)`. Mean-square powers, not window-integrated energies, are used for unequal 5s/2s windows. Analytic pure tones test the normalization.

Equation S4: `FI=log10(P_8–15Hz/P_2–5Hz)`. Implementation assumptions not specified by the paper:100Hz sampling, a rectangular8s window, removal of the mean, one-sided DFT powers normalized by N^2 and doubled except DC/Nyquist; inclusive band endpoints. The DFT is evaluated directly in double precision for these small tests. Validation tones3Hz and10Hz fall exactly on Fourier bins. For `sin(2π3t)+r sin(2π10t)`, the exact FI is `2log10(r)`. No seismic event or observed waveform is synthesized from a plot. Display filtering at1–10Hz in S14 is not applied before calculating FI's8–15Hz band.

Magnitude least squares: minimize sum w_ij*(m_i-m_j-delta_ij)^2 + lambda*sum(m_i-prior_i)^2. Solve the small graph-Laplacian normal system by Gaussian elimination with partial pivoting. This objective and weight convention explicitly resolve missing implementation details; they are not claimed to be the authors' exact regularizer or gradient-descent optimizer. Test magnitudes[0,.3,-.2,.8], amplitudes10^m, weights1/(j-i). Lambda1 gives exact recovery when priors equal truth. All-zero lambda is rejected as gauge-singular. A common prior shift must shift every solution equally. Sensitivity uses prior errors[.2,-.1,.1,-.2] with lambda0.001–100. Such assumed priors do not estimate the publication's magnitude errors.

No physical initial/boundary conditions apply: this is finite-window signal analysis and finite-dimensional estimation. Source terms, material dynamics, fault geometry, and earthquake occurrence times are not modeled.

## Internal discrepancies retained

- S7 uncertainty discussion cites panelsC/E/H andD/F/I, while the figure/caption uses B/D/F for count-versus-error andC/E/G for densities. Inventory follows the figure and its caption.
- FigS9 methods retain exactly100 differential correlations; its caption implies rejection at100. Both predicates are saved in `data/thresholds.csv`. No arbitrary choice is applied to a catalog.
- HTMLS1 describes a distinct quality filter summing NCCP+NCCS+NCTP+NCTS>1000. It is not the S9 filter.
- Methods discuss74 focal solutions; DataS3 caption describes55. The archive was not used to reconcile that difference.
- S15 spells a station CCAM once, whereas its normalization and methods identify CAAM. The record retains that discrepancy.

## Validation scope

Analytic ratios, spectral orthogonality, Parseval power conservation, invariance to common amplitude gain and circular time shift, unequal-window SNR, magnitude pair reversal, absolute-offset gauge freedom, and singular/invalid-input rejection are checked. These are independent consistency tests of implemented formulas. They do not validate event detection, relocation errors, empirical b values, or volcanic interpretation. All main-manuscript panels remain not reproduced; S1, S2 and S15C now have partial observational reconstructions.

## Current observational implementation

Original observations and trained PhaseNet weights are permitted under the latest instruction. Own retrieval and processing scripts use official FDSN waveform/response metadata and the permitted model artifact. The calendar-selected validation day is independent of all catalogs. See report/report.tex and config/observations.json for exact operational settings.

The template displays use CAAM/COLB HHE/HHZ, mean removal and sensitivity correction, a -2/+18-second display, component-specific CAAM normalization and Hann-window spectral density. FI uses an 800-sample unfiltered CAAM vertical window with the same band/Parseval conventions as the analytic checks. Observational computations use NumPy FFTs; analytic C++ checks retain their direct DFT implementation.

PhaseNet inference uses ENZ, 100 Hz, 1 Hz highpass (four-pole causal), 1500-sample overlap, 250-sample blinding and probability threshold 0.3. SeisBench's architecture has 3001 samples (30.01 seconds); the paper describes nominal 30-second windows. Tensor loading is strict and weights-only. No missing waveform data are interpolated. Hourly-boundary blinding and the limited network/time coverage preclude completeness claims.

The separate calendar-day template scan uses the three written templates, CAAM/COLB vertical channels, a 0.2–6 Hz four-pole causal filter, normalized sliding correlations averaged across stations, score >0.25 and 8-second peak spacing. Ten-second chunk edges are excluded. These spacing/filter details are implementation assumptions; unreviewed matches are not the paper's hybrid catalog. Current empirical products reside in data/observations/. Former synthetic method-check figures were removed.
