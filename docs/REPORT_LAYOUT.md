# Presentation revision, 12 October 2026

This revision changes document organization and display only. It does not rerun, extend or alter an analysis, scientific data file, existing plot, or panel-status record. The baseline hashes in `report/layout_baseline.json` identify the preserved snapshot and original commit; document-build verification records both in-build preservation and equality to that snapshot.

## Paper and reproduced supplement

`report/report.tex` includes three source files in order:

1. `report/main_paper.tex`: introductory context followed by the publication's five named sections: The current phase of unrest; Improving the earthquake catalog; A clearer view of the current phase of unrest; Implications for the physical process driving the unrest; New perspectives for improved seismic risk assessment. Figures 1–4 occur in order in their corresponding scientific sections.
2. `report/reproduced_supplement.tex`: catalog construction, location validation, hybrid-event template matching, Figures S1–S15, and explicit missing-result entries for Tables S1–S2 and the supplementary data products. The topic and figure order follows the local supplement. Brief outcome statements retain the scientific sequence; full implementation and audit details follow this supplement.
3. `report/reproduction_documentation.tex`: the previous report's scientific specification, input inventory, access/coverage results, methods and equations, assumptions, validation, final numerical comparisons, stage and panel records, numerical tables, remaining work, rebuild instructions and sources.

The original saved result/table fragments remain unchanged. The useful template-FI table is included with the consistency-check table. Provisional location/background, unconfirmed hybrid-candidate, and unlabeled CMIS picker plots are labeled **Reproduction diagnostic** and appear only in the documentation, where they explain specific methodological limits. External routine-catalog plots are labeled **External context** there. The independent-pick, CSOB picker, internal S–P, and E1/E2 template figures remain in the repository; their numerical evidence and relevant caveats remain in the text, without unnecessary diagnostic figures in either paper section.

Only 1B, S1, S2 and S15C have partial independent figure counterparts. The other 59 panel/view records have placeholders. No status is upgraded. In particular, different E1/E2 templates are not used as S15A/B, and generic picker examples are not used as S4.

## Comparison PDF

`report/comparison.tex` includes the generated `report/comparison_pages.tex`: one page each for Figures 1–4 and S1–S15, in that order. There is no title/narrative/audit page. Each page has a left **Published reference** and a right **Independent result** column. The right column contains the saved partial figure where available, together with its limitation, or a missing-result placeholder. The original figure's remaining panels are not filled from external context or other diagnostics.

References are rendered only from `tanmodel.pdf` (PDF pages 2–5) and `tanmodelsupp.pdf` (PDF pages 12–26). `report/figure_layout.json` records display crop rectangles in PDF page coordinates; these rectangles are not geophysical coordinates or digitized plot values. `report/reference_crops.json` records source and crop checksums, page numbers and display resolution. Crops exclude surrounding paper narrative and captions and are used only in the comparison PDF. Sources are credited on every comparison page. Cropped reference assets are generated locally, ignored by Git, and have no connection to the analysis pipeline.

## Build and checks

Run `.venv/bin/python scripts/build_documents.py --clean` from the repository root. It uses existing numerical outputs, the local publication PDFs, Pillow and installed Poppler/LaTeX tools. It renders references, regenerates the shared figure fragments and comparison pages, compiles both documents twice, checks their final order and labels, checks for LaTeX overflow/warnings, verifies that published images are absent from the paper, and verifies that protected files do not change during the build. The build does not retrieve observations or run scientific scripts.

`report/document_build.json` records the outcome, page positions, all 59 panels without a valid independent comparison, the four partial counterparts, and document-source/output hashes. `report/document_build_log.json` contains executed commands and tool output. The existing full-analysis `scripts/rebuild.py` now calls this document builder at its final publishing stage; its numerical processing sequence is unchanged. The full scientific rebuild was deliberately not rerun for this presentation-only request.

Replaced: `report/report.tex` and `report/report.pdf`. Added: the separated LaTeX sources, comparison PDF/source, shared figure layout/fragments, display-reference receipts and document builder/check records. Updated: README, `.gitignore`, the final document-build invocation in `scripts/rebuild.py`, and replacement documentation. Preserved: numerical data, existing generated figures, analytical code/configuration, original report tables, source PDFs/ZIPs, all panel classifications, useful setup, unrelated work and Git history. Previous report versions remain in Git history.
