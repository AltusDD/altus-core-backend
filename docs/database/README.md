# Database Docs

This folder defines the reusable DB autonomy baseline.

- `DB_AUTONOMY_EXECUTION_MODEL_V1.md` explains issue intake, GitHub-native execution, PR proof, and future engine extension points.
- `DB_CHANGE_SOP_V1.md` defines the migration, verification, apply, rollback-note, and documentation workflow.
- `DB_PROOF_REQUIREMENTS_V1.md` defines mandatory PR metadata and proof artifacts.
- `SCHEMA_INVENTORY_V1.md` captures the current repository-grounded and staging-reconciled schema inventory, including the proven absence of `asset_links` in staging, the current canonical link authority in `asset_data_raw` fallback evidence, the proven live staging shape of `public.assets.external_ids`, and the current proven hash equivalence between absent `asset_data_raw.payload_sha256` and `public.assets.external_ids.payload_hash`, and the proven absence of `asset_data_raw.source_record_id` with no equivalent source-record identity field currently proven elsewhere.
- `SCHEMA_RECONCILIATION_DECISIONS_V1.md` records object-by-object canonical decisions for proven repo-versus-staging mismatches.
- `NEXT_UNKNOWN_SET_ASSET_SPECS_RECONCILED_V1.md` frames the final unresolved Database-lane unknown set and the proof required before any canonical decision about extra live `asset_specs_reconciled` columns.




