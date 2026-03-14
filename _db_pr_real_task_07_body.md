## Summary
- add a docs-only proof for REAL TASK-07 on normalized occupancy authority for the resolved portfolio cohort
- confirm no normalized read-only occupancy authority is currently repo-proven
- keep `occupiedUnits` fallback behavior unchanged

## Scope
- add `docs/contracts/ECC_PORTFOLIO_SUMMARY_NORMALIZED_OCCUPANCY_AUTHORITY_PROOF_V1.md`
- document inspected candidate tables, views, materialized views, and ingestion/ETL surfaces
- no runtime, migration, contract-shape, or schema changes

## Proof
- resolved cohort authority remains `public.assets.external_ids[<configured_key>] == portfolioId`
- `public.asset_specs_reconciled` safely backs `totalUnits` only through `units_count`
- no repo-proven table, view, materialized view, or ETL output explicitly defines occupied units for that cohort
- `public.asset_data_raw` remains raw evidence only and would require inferred semantics

## Boundaries Left Untouched
- no field activation
- no Supabase migration
- no Azure/deploy/runtime ownership changes
- no shared contract mutation

## Validation
- `rg -n "create( materialized)? view|materialized view|occupancy|occupied|vacan|lease|tenant" supabase docs azure tests`
- repo file review:
  - `docs/database/SCHEMA_INVENTORY_V1.md`
  - `docs/architecture/DATA_MAP_V1.md`
  - `docs/contracts/ECC_PORTFOLIO_SUMMARY_OCCUPIED_UNITS_PROOF_DECISION_V1.md`
  - `azure/functions/asset_ingest/ecc_portfolio_summary_service.py`
  - `supabase/migrations/0001_enterprise_asset_master.sql`
  - `supabase/migrations/0002_altus_core_identity.sql`

## Impact
- contract impact: none
- workflow impact: none
- runtime impact: none
- integration impact: none
- migration impact: none

## Rollback
- revert this PR to remove the docs-only proof artifact
