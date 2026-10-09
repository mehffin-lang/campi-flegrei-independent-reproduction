# Independent reproduction attempt: Campi Flegrei

**Status: scientifically blocked; no manuscript or supplementary panel reproduced.**

Target: Tan et al. (2025), [A clearer view of the current phase of unrest at Campi Flegrei caldera](https://doi.org/10.1126/science.adw9038), *Science* 390, 70–75. The user confirmed this DOI after the empirical/catalog nature of the paper was identified.

[Compiled report](report/report.pdf) · [LaTeX source](report/report.tex) · [Blockers](docs/BLOCKERS.md) · [Panel record](docs/panel_record.json) · [Provenance](docs/PROVENANCE.md)

The full manuscript and supplement could not be accessed. The available abstract specifies an observational machine-learning study, not a complete coupled physical model. The requested prohibition on original source data prevents reconstruction of the actual earthquakes from written descriptions alone. Individual publication panel identities remain unresolved: the record covers main and supplement scopes without inventing panel numbers.

The included C++ implementation is **only a synthetic homogeneous-medium travel-time/location validation example**. Its four plotted panels V1a–d are independently generated consistency checks, not partial or complete reproductions of any publication panel. The coupled model and complete detection/association/relocation pipeline requested by the user have not been implemented. No original code, weights, catalogs, waveforms, simulation outputs, or figure files are inputs.

## Rebuild

From the repository root, using a C++17 compiler, Python 3 with NumPy and Matplotlib, and pdfLaTeX:

```sh
python3 scripts/rebuild.py
```

This command recompiles C++, regenerates saved synthetic data and figures, checks numerical invariants, records unresolved panel attempts, and compiles the LaTeX report twice. It exits nonzero on a failed check or compilation. A successful build **does not mean scientific reproduction succeeded**. Exact commands, outputs, runtime versions and hashes are in `data/build_log.json`, `data/build_status.json`, and `data/manifest.sha256` after execution.

Individual steps:

```sh
mkdir -p build data figures tmp
TMPDIR="$PWD/tmp" g++ -std=c++17 -O3 -Wall -Wextra -pedantic src/validation.cpp -o build/validation
./build/validation config/validation.txt data
python3 scripts/plot.py
python3 scripts/audit.py
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=report report/report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=report report/report.tex
```

All project inputs, outputs, logs, and temporary files remain within this root. The rebuild sets `TMPDIR` and `MPLCONFIGDIR` locally. Existing system Python/TeX/compiler installations are used; no new dependency caches are needed outside the repository. See the report for equations, assumptions, numerical limitations, validation, and the remaining scientific work.
