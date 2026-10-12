The unchanged local `tanmodel.pdf` and `tanmodelsupp.pdf` are the scientific specifications. Both uploaded science.adw9038 ZIPs are author-derived result/reference material, not independent observations.

The current frozen inputs are recorded in `docs/rebuild_inputs.json` (baseline) and `docs/continuation_rebuild_inputs.json` (expanded subset). Run `.venv/bin/python scripts/restore_inputs.py --continuation` to populate and hash-check ignored `inputs/`. `continuation_context_inputs.zip` contains permitted contextual observations, metadata and format notes. `revision_written_sources.zip` contains written-source/access evidence. `acquisition_checkpoint.sqlite.gz` preserves administrative pending/success/no-data states; pending requests are not observations.

The quarantined unverified background grid is excluded from these rebuild requirements. Source classifications and restrictions are in `docs/INPUT_POLICY.md`; current source investigations and limitations are in `docs/CONTINUATION.md` and `docs/revision_access.json`.

The independently retrieved Battaglia (2008) article PDF stays in ignored local inputs. Its source URL and checksum are recorded as an external written source in `docs/revision_source_bundle.json`; restoration retrieves it from the institutional repository instead of redistributing it in the source bundle. The user's four original uploads remain unchanged.
