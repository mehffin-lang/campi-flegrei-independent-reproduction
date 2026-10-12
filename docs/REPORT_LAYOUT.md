# Presentation revision, 12 October 2026

The original presentation revision preserved all scientific results. The subsequent authorized observational continuation extends the analysis while retaining this section and figure order. The baseline hashes in `report/layout_baseline.json` preserve the earlier snapshot; `matches_pre_edit_snapshot` may therefore be false. The document-only builder verifies every current data, figure, script and configuration file is unchanged during its own execution, and records the obsolete figures removed since the earlier baseline. Current scientific status is in `data/continuation/panel_status.json`.

## Paper and reproduced supplement

`report/report.tex` includes three source files in order:

1. `report/main_paper.tex`: introductory context followed by the publication's five named sections: The current phase of unrest; Improving the earthquake catalog; A clearer view of the current phase of unrest; Implications for the physical process driving the unrest; New perspectives for improved seismic risk assessment. Figures 1–4 occur in order in their corresponding scientific sections.
2. `report/reproduced_supplement.tex`: catalog construction, location validation, hybrid-event template matching, Figures S1–S15, and explicit missing-result entries for Tables S1–S2 and the supplementary data products. The topic and figure order follows the local supplement. Brief outcome statements retain the scientific sequence; full implementation and audit details follow this supplement.
3. `report/reproduction_documentation.tex`: the previous report's scientific specification, input inventory, access/coverage results, methods and equations, assumptions, validation, final numerical comparisons, stage and panel records, numerical tables, remaining work, rebuild instructions and sources.

Useful template-FI and analytic consistency tables remain after the supplement. Current velocity-pilot values are explicitly unvalidated supporting evidence. Non-original diagnostics remain in the repository and are not inserted as paper/supplement counterparts. New Figures 1A/1C/S5 use expressly permitted routine-catalog data, labeled as such; 1B uses original leveling/GNSS observations through March 2025. Partial S6 and S8 show limited independent pilot outputs, not the completed multiyear catalog.

The current exact partial/missing panel lists are generated from `docs/panel_record.json` and recorded in `report/document_build.json`. Different E1/E2 templates are not used as S15A/B, and generic picker examples are not used as S4. No panel is upgraded solely because code exists.

## Comparison PDF

`report/comparison.tex` includes the generated `report/comparison_pages.tex`: one page each for Figures 1–4 and S1–S15, in that order. There is no title/narrative/audit page. Each page has a left **Published reference** and a right **Independent result** column. The right column contains the saved partial figure where available, together with its limitation, or a missing-result placeholder. The original figure's remaining panels are not filled from external context or other diagnostics.

References are rendered only from `tanmodel.pdf` (PDF pages 2–5) and `tanmodelsupp.pdf` (PDF pages 12–26). `report/figure_layout.json` records display crop rectangles in PDF page coordinates; these rectangles are not geophysical coordinates or digitized plot values. `report/reference_crops.json` records source and crop checksums, page numbers and display resolution. Crops exclude surrounding paper narrative and captions and are used only in the comparison PDF. Sources are credited on every comparison page. Cropped reference assets are generated locally, ignored by Git, and have no connection to the analysis pipeline.

## Build and checks

Run `.venv/bin/python scripts/build_documents.py --clean` from the repository root. It uses existing numerical outputs, the local publication PDFs, Pillow and installed Poppler/LaTeX tools. It renders references, regenerates the shared figure fragments and comparison pages, compiles both documents twice, checks their final order and labels, checks for LaTeX overflow/warnings, verifies that published images are absent from the paper, and verifies that protected files do not change during the build. The build does not retrieve observations or run scientific scripts.

`report/document_build.json` records the actual outcome, page positions, partial and missing panels, and source/output hashes. `report/document_build_log.json` contains executed commands and tool output. The current scientific `scripts/rebuild_continuation.py` invokes this builder after analysis; the document builder itself does not change numerical results. Scientific rebuild instructions are in `docs/CONTINUATION.md`; replacements are in `docs/REPLACEMENTS.md`.
