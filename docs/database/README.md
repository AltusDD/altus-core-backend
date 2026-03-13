# Database Docs

This folder defines the reusable DB autonomy baseline.

- `DB_AUTONOMY_EXECUTION_MODEL_V1.md` explains issue intake, GitHub-native execution, PR proof, and future engine extension points.
- `DB_CHANGE_SOP_V1.md` defines the migration, verification, apply, rollback-note, and documentation workflow.
- `DB_PROOF_REQUIREMENTS_V1.md` defines mandatory PR metadata and proof artifacts.
- `SCHEMA_INVENTORY_V1.md` captures the current repository-grounded and staging-reconciled schema inventory, including the proven absence of `asset_links` in staging and the current canonical link authority in `asset_data_raw` fallback evidence.
- `SCHEMA_RECONCILIATION_DECISIONS_V1.md` records object-by-object canonical decisions for proven repo-versus-staging mismatches.
