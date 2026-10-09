# Provenance for the source-verified run

The four user-uploaded files were read from main at commit `ee3f774`. The local branch was fast-forwarded to that commit, retaining all history. Each upload's bytes were compared with its Git blob before any previous outputs were replaced. File sizes, SHA-256, PDF metadata, text extraction results, ZIP members and CRC results are in `file_inventory.json`.

`tanmodel.pdf` is the 7-page Science article including its publication end page. `tanmodelsupp.pdf` is the 35-page matching supplement whose title, authors, publication identifier, methods, S1–S15 captions, Tables S1–S2, and archive captions match the paper. The main PDF emits two nonfatal font-weight warnings; text, methods, and captions are readable. The supplement extracts without warnings. Both are unencrypted. Written sources were local; no URL was used to retrieve the paper in this run.

ZIP inspection was limited to directory metadata and CRC integrity. Neither ZIP was extracted. No CSV event/pick/focal rows were consulted. The interactive HTML was neither opened in a browser nor executed, and its source was not used. Archive classifications come from the supplement's written Data/HTML captions (S28). Resource-fork files under `__MACOSX` are metadata, not additional methods. All four uploads remain unchanged and tracked as supplied by the user.

Published spatial figures S5–S7 and S9 were viewed locally as references to check how the written captions correspond to panel layouts and to resolve conflicting S7 letter references. No coordinates, values, dates, or parameters were digitized from any plot. No published image is included in the generated report or read by the computational or plotting programs.

Only `config/method_checks.cfg` and hard-coded analytic fixtures feed the C++ calculations. Python plotting reads only our CSVs. The report quotes no numerical agreement with the actual Campi Flegrei catalog. Published counts and thresholds are documentary comparison targets, not generated catalog data. The two permitted guidance files are preserved unchanged and followed; no authors' code repositories were consulted in this run.

Project intermediates and plotting/font cache reside inside `tmp/`; compiler temporaries use that directory. Existing `/usr/bin` tools, system Python libraries, and `/usr/share/texlive` resources are used. No dependency installation or new user-level cache is required. GitHub authentication and SSH keys remain in existing user configuration and are never copied into the repository.
