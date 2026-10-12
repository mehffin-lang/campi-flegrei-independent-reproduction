# Scientific progress assessment

`progress_assessment.pdf` contains a four-page scientific assessment followed by a seven-page panel inventory and evidence appendix. `progress_assessment.tex` is its source; `panel_inventory.tex` supplies the 63-panel inventory.

The assessment examines scientific commit `f115c20841779aac4c580327abe71e49499ae981`. No empirical processing, long downloads, parameter searches, new agents, or earlier-deliverable regeneration was performed. Only this folder is added. The user explicitly authorized this location after the requested `/data` directory was found unwritable.

From the repository root, using the existing environment:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B assessment/check_evidence.py
mkdir -p assessment/build
pdflatex -interaction=nonstopmode -halt-on-error -recorder \
  -output-directory=assessment/build assessment/progress_assessment.tex
pdflatex -interaction=nonstopmode -halt-on-error -recorder \
  -output-directory=assessment/build assessment/progress_assessment.tex
cp assessment/build/progress_assessment.pdf assessment/progress_assessment.pdf
```

The inexpensive check reads existing outputs, three GNSS/precision-related input sets, and declared panel file paths. It writes only `assessment/evidence.json`; it does not import or execute the scientific processing scripts. Large original inputs must already be present locally to repeat all checks. The LaTeX-only build uses the three existing tracked figure PDFs and does not require original waveforms or trained weights.

`build_verification.json` records the completed build, word/page and panel counts, reference checks, and preservation checks. Compilation logs and visual-inspection renders remain under ignored `build/`. Usage figures in the report are session counters, not an invoice or an audited project cost. Proposed next work is not authorized or executed.
