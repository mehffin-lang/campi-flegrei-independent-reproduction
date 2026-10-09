# Independent assessment and method checks for Tan et al.

**Written-source access is verified. Scientific reproduction remains incomplete: no empirical manuscript or supplementary panel is reproduced.**

[Compiled report](report/report.pdf) · [LaTeX](report/report.tex) · [Panel record](docs/panel_record.json) · [File inventory](docs/file_inventory.json) · [Replacements](docs/REPLACEMENTS.md)

The sources are the user-uploaded `tanmodel.pdf` (7 pages) and `tanmodelsupp.pdf` (35 pages), preserved from main. Both are readable. The study develops an observational earthquake catalog using retrained PhaseNet, GaMMA, VELEST/TomoDD relocation, magnitude estimation, focal mechanisms, and hybrid-event analysis. It does not specify a coupled physical forward model.

The two uploaded ZIPs are readable and pass integrity checks. The Data S1–S3 ZIP contains the authors' catalog, associated picks, and focal solutions. The other ZIP contains an interactive HTML seismicity plot. They were listed and checked, not extracted or executed. Neither their CSV values nor their HTML/code/embedded data are used in the analysis. Both uploads are preserved unchanged because they were already committed by the user.

## What is implemented

`src/method_checks.cpp` independently implements the relative amplitude/magnitude ratios (S2/S5), power SNR (S3), and frequency index (S4). It also tests an explicitly assumed regularized least-squares magnitude problem, including its offset ambiguity. Parameters are in `config/method_checks.cfg`; all numerical inputs are analytic test fixtures. Plots M1a–d are **method consistency checks**, not reproductions of S8 or S14/S15. They replace the previous unrelated location example.

The full detection/training/association/relocation pipeline is not implemented. Its empirical inputs are excluded, and several numerical settings are incomplete in the written description. Every paper figure and caption-defined panel/view is accounted for in the report and JSON record. A stopped attempt is recorded where permitted inputs are unavailable; no fabricated earthquake sequence is substituted.

## Rebuild

Requirements: C++17 compiler, Python 3.6+, NumPy, Matplotlib, Poppler (`pdftotext`, `pdfinfo`), and pdfLaTeX with standard packages. This workspace already has them.

```sh
python3 scripts/rebuild.py
```

The offline procedure verifies the four uploaded files, confirms text/caption extraction, recompiles C++, regenerates its CSV outputs and method plots, creates report tables from those saved outputs and the panel record, compiles the report twice, checks numerical assertions and PDF layout, and records versions, commands, outputs, and hashes. `data/build_status.json` distinguishes a successful build from **zero reproduced publication panels**. It does not execute anything from a ZIP or import original observational results.

For a clean rebuild, remove only generated build products (preserves all source files and uploads):

```sh
python3 scripts/rebuild.py --clean
```

All intermediates stay in `tmp/`, `build/`, `data/`, `figures/`, and `report/` inside this repository. `TMPDIR` and the Matplotlib cache are explicitly local. Existing system libraries and user Git/SSH configuration remain outside; no dependencies were installed or external project cache created. Exact versions are in the build status. No paper retrieval from a URL is required.
