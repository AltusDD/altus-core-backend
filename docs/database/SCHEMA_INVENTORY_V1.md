# SCHEMA INVENTORY V1

## Purpose

Document the current authoritative Supabase schema surfaces that are provable from repository artifacts on `main` and identify contract-critical gaps that future autonomous DB work must address explicitly.

## Authority Rule

This inventory is grounded in:

- repository migrations under `supabase/migrations/`
- repository policy SQL under `supabase/policies/`
- current runtime code in `azure/functions/asset_ingest/function_app.py`
- non-destructive verification SQL under `supabase/verification/`

This inventory does not claim live dashboard state, production state, or unverified staging state.

## Repo-Proven Critical Tables

### `public.organizations`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Proven columns:
- `id`
- `name`
- `created_at`

Current role:
- identity and org-scoping anchor for DB-backed asset surfaces

### `public.profiles`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Proven columns:
- `user_id`
- `organization_id`
- `display_name`
- `created_at`
- `updated_at`

Current role:
- user-to-organization attachment used by helper functions and auth bootstrap RPCs

### `public.organization_members`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Proven columns:
- `organization_id`
- `user_id`
- `role`
- `created_at`

Current role:
- authoritative org membership table used by RLS helper functions

### `public.assets`

Sources:
- `supabase/migrations/0001_enterprise_asset_master.sql`
- `supabase/migrations/0002_altus_core_identity.sql`

Repo truth notes:
- `0001` and `0002` define different shapes for `public.assets`.
- Because both use `create table if not exists`, the final live shape depends on historical apply order and any later manual/schema edits.
- Repo evidence proves the table exists conceptually, but does not fully prove one canonical column set from migrations alone.

Columns provable somewhere in repo migrations:
- `id`
- `organization_id`
- `address_canonical`
- `apn`
- `clip`
- `asset_type`
- `name`
- `status`
- `created_at`
- `updated_at`

Columns expected by current runtime code but not proven by migrations on `main`:
- `display_name`
- `external_ids`

Current role:
- authoritative current-state table for asset ingest and the asset-centric API surfaces in `docs/architecture/DATA_MAP_V1.md`

### `public.asset_data_raw`

Sources:
- `supabase/migrations/0001_enterprise_asset_master.sql`
- `supabase/migrations/0002_altus_core_identity.sql`

Repo truth notes:
- `0001` and `0002` define different shapes for `public.asset_data_raw`.
- Repo evidence proves the table exists conceptually, but not one fully canonical final column set.

Columns provable somewhere in repo migrations:
- `id`
- `organization_id`
- `asset_id`
- `source`
- `payload_jsonb`
- `payload`
- `fetched_at`
- `created_at`

Columns expected by current runtime code but not proven by migrations on `main`:
- `payload_sha256`
- `source_record_id`

Current role:
- authoritative raw evidence stream for ingest, audit, timeline, and fallback evidence flows per `DATA_MAP_V1`

### `public.asset_specs_reconciled`

Sources:
- `supabase/migrations/0001_enterprise_asset_master.sql`
- `supabase/migrations/0002_altus_core_identity.sql`

Repo truth notes:
- `0001` and `0002` define different shapes for `public.asset_specs_reconciled`.
- Repo evidence proves the table exists conceptually, but not one fully canonical final column set.

Columns provable somewhere in repo migrations:
- `asset_id`
- `organization_id`
- `beds`
- `baths`
- `sqft`
- `year_built`
- `property_type`
- `units_count`
- `updated_at`
- `updated_by_user_id`
- `specs`

Current role:
- optional reconciled/specification surface for asset enrichment data

## Repo-Proven Critical Views

None are currently proven by repository migrations on `main`.

## Repo-Proven Critical Functions / RPCs

### `public._touch_updated_at()`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Current role:
- trigger helper for `profiles.updated_at` and `assets.updated_at`

### `public.altus_current_org_id()`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Current role:
- helper function to resolve the caller's organization from `profiles`

### `public.altus_is_org_member(uuid)`

Sources:
- `supabase/migrations/0002_altus_core_identity.sql`
- `supabase/migrations/0003_altus_is_org_member_service_role.sql`

Repo truth notes:
- `0003` intentionally replaces the earlier version so `service_role` returns `true`.
- This is a contract-critical RLS helper for org-scoped access checks.

### `public.altus_login(text)`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Current role:
- auth bootstrap RPC that ensures profile, organization, and organization membership exist

### `public.altus_me()`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Current role:
- authenticated identity/org summary RPC

### `public.altus_logout()`

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Current role:
- no-op placeholder RPC for client-side sign-out flow symmetry

## Repo-Proven Critical Policy / RLS Objects

### RLS-enabled tables from repo migrations

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Tables:
- `public.organizations`
- `public.profiles`
- `public.organization_members`
- `public.assets`
- `public.asset_data_raw`
- `public.asset_specs_reconciled`

### Policy objects from `0002_altus_core_identity.sql`

- `org_select`
- `profiles_select_self`
- `profiles_update_self`
- `org_members_select`
- `assets_select`
- `assets_insert`
- `assets_update`
- `assets_delete`
- `adr_select`
- `adr_insert`
- `adr_update`
- `adr_delete`
- `asr_select`
- `asr_insert`
- `asr_update`
- `asr_delete`

### Additional repo policy SQL

Source:
- `supabase/policies/rls_enterprise_asset_master.sql`

Repo truth notes:
- This file enables RLS on `assets`, `asset_data_raw`, and `asset_specs_reconciled` and creates policy `assets_org_isolation` only on `public.assets`.
- The policy uses `request.jwt.claim.organization_id`, which differs from the helper-function approach in `0002`.
- Repo evidence does not prove whether this policy file is currently applied in staging or whether it supersedes or coexists with the migration-defined policies.

## Authoritative Surface Mapping

### Asset ingest

Authoritative DB objects, grounded in repo evidence:
- `public.assets`
- `public.asset_data_raw`

Supporting objects:
- `public.organizations`
- `public.organization_members`
- `public.altus_is_org_member(uuid)`

Repo/code gap notes:
- `function_app.py` writes `display_name` and `external_ids` to `assets`, and `payload_sha256` plus `source_record_id` to `asset_data_raw`.
- Those fields are not proven by repo migrations on `main`.

### ECC portfolio summary surfaces

Repo-proven authoritative DB objects:
- none

Grounding notes:
- `azure/functions/asset_ingest/ecc_portfolio_summary_service.py` is currently deterministic stub logic with no proven Supabase persistence calls.

### Asset search

Repo-proven authoritative DB objects:
- `public.assets` as intended authority in `DATA_MAP_V1`

Grounding notes:
- `DATA_MAP_V1` maps search to `assets`.
- `ecc_asset_search_service.py` is currently deterministic stub logic and does not prove live DB reads.
- `display_name` and `address_canonical` are referenced in `DATA_MAP_V1`, but only `address_canonical` is proven by repo migrations on `main`.

### Asset metrics

Repo-proven authoritative DB objects:
- `public.assets`
- `public.asset_data_raw`

Grounding notes:
- `DATA_MAP_V1` maps metrics to `assets` with `asset_data_raw` fallback evidence.
- `ecc_asset_metrics_service.py` is currently deterministic stub logic and does not prove live DB reads.

### Price-engine persistence

Repo-proven authoritative DB objects:
- none

Grounding notes:
- `price_engine_service.py` is a pure calculation module.
- No repo-proven Supabase table, view, function, or policy currently serves as price-engine persistence.

## Unknowns / Gaps

- The final live staging column sets for `assets`, `asset_data_raw`, and `asset_specs_reconciled` are not fully provable from migrations alone because `0001` and `0002` define different table shapes.
- `docs/architecture/DATA_MAP_V1.md` references `asset_links`, but no repo migration on `main` proves that table exists.
- `docs/contracts/README.md` currently references `docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md`, but that file is not present on `main`.
- No repo migration on `main` proves any critical view for ECC or price-engine persistence.
- No safe staging inspection output is committed yet for this inventory; this document is repository-grounded first.

## Recommended Follow-on DB Tasks

1. Add a non-destructive schema inventory verification run for staging and capture results in PR proof.
2. Reconcile migration truth for `assets`, `asset_data_raw`, and `asset_specs_reconciled` into one unambiguous canonical schema path.
3. Either add repo truth for `asset_links` and the runtime-expected columns, or remove those references from contracts and data maps until proven.
4. Define whether ECC and price-engine surfaces will remain stub-only or receive explicit persistence contracts.
