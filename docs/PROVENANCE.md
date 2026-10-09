# Provenance and source boundaries

Access date: 2026-10-09. The two explicitly permitted guidance files were fetched individually from the requested repository; no other files in that repository were consulted.

Scientific evidence used: the Tan et al. abstract as returned by Crossref and the PubMed web tool; Crossref bibliographic metadata; OpenAlex full-text availability metadata; the IRIS institutional landing-page access description. URLs and retrieval results are in `sources/retrieval.json` and `sources/README.md`. These are specifications/metadata, not observational inputs. Broad publication searches returned an incidental authors' repository README snippet and a waveform-dataset landing-page snippet. Neither repository nor dataset was opened or downloaded, and neither snippet supplied implementation choices or parameter values. Search was subsequently restricted to exclude GitHub. No clean-room claim of zero incidental search exposure is made.

The initial direct PubMed download was an HTTP 203 browser challenge, not the article; it is ignored by the build. The web tool supplied the abstract, and Crossref independently returned it. No full paper or supplement was obtained. All input numbers in the C++ validation are deliberately synthetic and documented; they are not values inferred from figures or the authors' repository.

`AGENTS.md` and `brad-lipovsky-academic-style-guide.md` retain their original guidance text. No notebook is used. The report follows mechanics-first reasoning and distinguishes calculated checks from observational results. Third-party metadata and failed response bodies are excluded from git; the short access manifest and paraphrased source notes are included.

The rebuild does not use the network. Project temporary files and the Matplotlib font cache reside in `tmp/`. Python packages, C++ toolchain, TeX packages, Git configuration and SSH credentials are existing system/user installations outside the repository. No dependencies were installed, and no external dependency cache was created. GitHub credentials and private SSH keys are never copied into the repository. Exact runtime versions are recorded in `data/build_status.json`.

Build troubleshooting: the first full rebuild stopped because system Python 3.6 does not accept the newer subprocess `text` keyword. This was replaced with `universal_newlines`; plotting uses the installed Matplotlib-compatible layout API. The final rebuild logs record the corrected run.
