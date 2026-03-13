# SCHEMA RECONCILIATION DECISIONS V1

## Purpose

Record the first explicit Database-lane reconciliation decisions for proven mismatches between repository schema truth and staging schema truth.

## Decision Inputs

This document is grounded in:

- repository migrations under `supabase/migrations/`
- repository policy SQL under `supabase/policies/`
- `docs/database/SCHEMA_INVENTORY_V1.md`
- staging proof from `supabase_apply.yml` run `23061749612`
- verification SQL `supabase/verification/0001_schema_inventory_assertions.sql`

This document does not claim production truth or unproven object semantics.

## Decision Standard

Each mismatch area must resolve to one of:

- adopt repo truth as canonical
- adopt staging truth as canonical
- mark difference as temporarily tolerated and out-of-scope
- requires separate follow-up proof before decision

## Decisions

### 1. `public.asset_data_raw`

Decision:
- adopt staging truth as canonical

Why:
- staging proof shows `public.asset_data_raw` currently exposes `id`, `asset_id`, `source`, `payload_jsonb`, and `fetched_at`
- repository migrations conflict on this table shape, but only the older `payload_jsonb` / `fetched_at` shape is proven live in staging
- no staging proof supports the `0002`-era `organization_id`, `payload`, or `created_at` columns as current live truth

Decision consequence:
- future schema-changing DB work should treat the staging-proven `payload_jsonb` / `fetched_at` shape as the current canonical baseline to reconcile back into repository truth

Still not decided inside this area:
- runtime-expected `payload_sha256` and `source_record_id` remain outside this decision and need separate proof before they become canonical schema requirements

### 2. `public.assets.name`

Decision:
- adopt staging truth as canonical

Why:
- staging proof confirms `public.assets` includes `display_name` and `external_ids`
- staging proof did not show `public.assets.name`
- current runtime code writes `display_name`, not `name`

Decision consequence:
- for current operational truth, `display_name` is the canonical presentation field and repo references to `name` should not drive future DB changes without separate proof

### 3. `public.asset_specs_reconciled` extra live columns

Decision:
- mark difference as temporarily tolerated and out-of-scope

Why:
- staging proof confirms extra live columns beyond the repo-proven baseline: `organization_id`, `spec_version`, `id`, `specs`, `provenance`, `effective_at`, and `created_at`
- no current Database-lane contract in repo assigns authoritative application behavior to those extra columns
- no runtime handler in current scope was modified or proven to depend on those columns for the active DB autonomy path

Decision consequence:
- these extra live columns are acknowledged as real staging state, but they should not be normalized into canonical repo truth until a dedicated follow-up task proves their intended contract role

### 4. missing policy `public.assets.assets_org_isolation`

Decision:
- adopt staging truth as canonical

Why:
- staging proof did not show policy `assets_org_isolation`
- staging did prove the helper-function-driven `assets_select`, `assets_insert`, `assets_update`, and `assets_delete` policies are active
- the standalone repo policy file is therefore not currently proven as part of the active staging policy set

Decision consequence:
- the active canonical policy baseline for `public.assets` is the staging-proven helper-function policy suite, not the unproven standalone `assets_org_isolation` policy file

## Unresolved Mismatches After This Decision Pass

- `asset_data_raw.payload_sha256` and `asset_data_raw.source_record_id` remain unresolved because they are runtime expectations not proven by staging or migrations
- `asset_links` remains unresolved because neither the inventory run nor this decision pass queried it directly
- `public.asset_specs_reconciled` extra live columns are acknowledged but intentionally not normalized into canonical repo truth yet
- the semantic intent of `external_ids` in `public.assets` remains only partially documented

## Sufficient For Schema-Changing Work?

No.

Reason:
- this decision pass is enough to define the current canonical baseline for some mismatches, but not enough to safely begin schema-changing DB work while `asset_links`, runtime-only `asset_data_raw` fields, and `asset_specs_reconciled` live-column semantics remain unresolved.

## Required Follow-on DB Work

1. Open a schema-changing reconciliation PR that updates repo migrations and schema docs so `public.assets` and `public.asset_data_raw` reflect the staging-canonical baseline now chosen here.
2. Run a dedicated non-destructive staging proof for `asset_links` and any related policies.
3. Open a separate proof task for whether `payload_sha256` and `source_record_id` are real schema requirements or runtime drift.
4. Open a separate contract task for whether `public.asset_specs_reconciled` extra live columns should become canonical or remain tolerated legacy state.
