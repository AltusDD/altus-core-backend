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
- `supabase/migrations/0004_reconcile_assets_asset_data_raw_canonical_baseline.sql`

Repo truth notes:
- `0001` and `0002` define different shapes for `public.assets`.
- `0004` is the forward reconciliation migration that aligns repo truth toward the approved staging-canonical baseline for the decided object area.
- Repository truth now treats `display_name` as the canonical presentation field for future applies while leaving legacy `name` untouched until a later cleanup decision.

Columns provable somewhere in repo migrations:
- `id`
- `organization_id`
- `address_canonical`
- `apn`
- `clip`
- `asset_type`
- `name`
- `display_name`
- `status`
- `created_at`
- `updated_at`

Live staging field not yet proven by migrations on this branch:
- `external_ids`
  - proven staging type: `jsonb`
  - nullability: `NOT NULL`
  - default: `'{}'::jsonb`
  - observed live shape: object in populated rows
  - observed top-level key usage: `payload_hash`
  - semantic expansion or redesign remains deferred to a later decision task

Current role:
- authoritative current-state table for asset ingest and the asset-centric API surfaces in `docs/architecture/DATA_MAP_V1.md`

### `public.asset_data_raw`

Sources:
- `supabase/migrations/0001_enterprise_asset_master.sql`
- `supabase/migrations/0002_altus_core_identity.sql`
- `supabase/migrations/0004_reconcile_assets_asset_data_raw_canonical_baseline.sql`

Repo truth notes:
- `0001` and `0002` define different shapes for `public.asset_data_raw`.
- `0004` is the forward reconciliation migration that aligns repo truth toward the approved staging-canonical `payload_jsonb` / `fetched_at` baseline for future applies.
- This branch intentionally does not resolve runtime-only `source_record_id`, and staging proof later confirmed `payload_sha256` is absent from the live `asset_data_raw` schema.

Columns provable somewhere in repo migrations:
- `id`
- `organization_id`
- `asset_id`
- `source`
- `payload_jsonb`
- `payload`
- `fetched_at`
- `created_at`

Canonical columns for the approved baseline on this branch:
- `id`
- `asset_id`
- `source`
- `payload_jsonb`
- `fetched_at`

Unresolved / intentionally not normalized in this branch:
- `organization_id`
- `payload`
- `created_at`
- `payload_sha256` (runtime expectation only; proven absent in staging, with current equivalent hash representation observed in `public.assets.external_ids.payload_hash`)
- `source_record_id` (runtime expectation only; proven absent in staging, with no equivalent source-record identity field currently proven elsewhere)

Current role:
- authoritative raw evidence stream for ingest, audit, timeline, and fallback evidence flows per `DATA_MAP_V1`

### `public.asset_specs_reconciled`

Sources:
- `supabase/migrations/0001_enterprise_asset_master.sql`
- `supabase/migrations/0002_altus_core_identity.sql`

Repo truth notes:
- `0001` and `0002` define different shapes for `public.asset_specs_reconciled`.
- Repo evidence proves the table exists conceptually, but not one fully canonical final column set.
- Staging proof run `23090151849` structurally proved the extra live column set and supporting indexes/policies, but live semantic usage remains unproven because staging currently has zero rows.

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

Structurally proven extra live staging columns:
- `spec_version`
  - proven staging type: `integer`
  - nullability: `NOT NULL`
  - default: `1`
- `id`
  - proven staging type: `uuid`
  - nullability: nullable
  - default: `gen_random_uuid()`
- `provenance`
  - proven staging type: `jsonb`
  - nullability: `NOT NULL`
  - default: `'{}'::jsonb`
- `effective_at`
  - proven staging type: `timestamptz`
  - nullability: `NOT NULL`
  - default: `now()`
- `created_at`
  - proven staging type: `timestamptz`
  - nullability: `NOT NULL`
  - default: `now()`

Structurally proven supporting staging context:
- `organization_id` is present in staging as `uuid`, nullable, and indexed by `idx_asset_specs_org`
- primary key remains `asset_id`
- foreign key remains `asset_id -> public.assets(id)` with `ON DELETE CASCADE`
- unique versioning-oriented index `uq_asset_specs_asset_version` is present on `(organization_id, asset_id, spec_version)`
- temporal index `idx_asset_specs_effective` is present on `effective_at desc`
- RLS is enabled with active policies `asr_select`, `asr_insert`, `asr_update`, and `asr_delete`

Structural intent note:
- the live schema structurally suggests row identity, versioning, provenance tracking, and effective-dating support
- staging row count is currently `0`, so live semantic usage is not proven

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

### Active canonical `public.assets` policy baseline on this branch

Source:
- `supabase/migrations/0002_altus_core_identity.sql`

Policies:
- `assets_select`
- `assets_insert`
- `assets_update`
- `assets_delete`

### Legacy non-authoritative policy reference

Source:
- `supabase/policies/rls_enterprise_asset_master.sql`

Repo truth notes:
- This file is now explicitly documented as a legacy, non-authoritative reference.
- Policy `assets_org_isolation` is intentionally not treated as active canonical repo truth on this branch.

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
- this branch reconciles repo truth toward `assets.display_name` and the `asset_data_raw.payload_jsonb` / `fetched_at` baseline
- `external_ids` is proven live in staging as a `jsonb` object field with default `{}` and observed `payload_hash` key usage; `payload_sha256` is proven absent from live `asset_data_raw` and currently represented equivalently through `external_ids.payload_hash`; semantic redesign remains intentionally deferred, and `source_record_id` remains intentionally unresolved

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
- `display_name` is now part of the reconciled repo baseline on this branch.

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

- `asset_links` is not proven by repo migrations on `main`, and staging proof run `23066495260` confirmed `public.asset_links` is not present in staging.
- `external_ids` is proven live in staging as `jsonb not null default '{}'::jsonb`, but its canonical repo semantics remain documentation-only until a later decision task.
- `payload_sha256` is a runtime-only expectation proven absent in staging, with current equivalent hash representation observed in `public.assets.external_ids.payload_hash`.
- `source_record_id` is a runtime-only expectation proven absent in staging, with no equivalent source-record identity field currently proven elsewhere.
- `asset_specs_reconciled` extra live columns are now structurally proven in staging, but live semantic usage remains unproven because staging currently has zero rows.
- No repo migration on this branch proves any critical view for ECC or price-engine persistence.

## Staging Reconciliation Proof (2026-03-13)

Proof source:
- `supabase_apply.yml` staging run `23061749612`
- verification file: `supabase/verification/0001_schema_inventory_assertions.sql`

Confirmed matches from staging proof:
- tables present: `public.organizations`, `public.profiles`, `public.organization_members`, `public.assets`, `public.asset_data_raw`, `public.asset_specs_reconciled`
- functions present: `public._touch_updated_at()`, `public.altus_current_org_id()`, `public.altus_is_org_member(uuid)`, `public.altus_login(text)`, `public.altus_me()`, `public.altus_logout()`
- policy objects present: `org_select`, `profiles_select_self`, `profiles_update_self`, `org_members_select`, `assets_select`, `assets_insert`, `assets_update`, `assets_delete`, `adr_select`, `adr_insert`, `adr_update`, `adr_delete`, `asr_select`, `asr_insert`, `asr_update`, `asr_delete`
- staging `public.assets` includes `display_name` and `external_ids`; later proof run `23067744047` established that `external_ids` is `jsonb not null default '{}'::jsonb` and object-shaped in populated rows, even though the field is still not proven by repository migrations on `main`

Confirmed mismatches from staging proof:
- staging `public.asset_data_raw` exposes `id`, `asset_id`, `source`, `payload_jsonb`, and `fetched_at`, but does not expose the `0002`-era `organization_id`, `payload`, or `created_at` fields that repository migrations also describe
- staging does not expose runtime-expected `asset_data_raw.payload_sha256` or `asset_data_raw.source_record_id`; later proof run `23069329492` confirmed no equivalent hash key exists in `asset_data_raw.payload_jsonb` and that the current proven equivalent hash representation lives in `public.assets.external_ids.payload_hash`, while proof run `23073428262` confirmed no equivalent source-record identity field is currently proven in `asset_data_raw.payload_jsonb` or `public.assets.external_ids`
- staging `public.asset_specs_reconciled` includes a broader shape than either single migration alone proves, including structurally proven columns `organization_id`, `spec_version`, `id`, `specs`, `provenance`, `effective_at`, and `created_at`; later proof run `23090151849` confirmed supporting indexes and policies, but live semantic usage remains unproven because staging currently has zero rows
- staging proof did not show policy `assets_org_isolation`, so the standalone policy file under `supabase/policies/` is not currently proven as active in staging

## Payload SHA256 Discovery Proof (2026-03-13)

Proof source:
- `supabase_apply.yml` staging run `23069329492`
- verification file: `supabase/verification/0006_payload_sha256_discovery.sql`

Confirmed results:
- `public.asset_data_raw.payload_sha256` is not present in staging
- no column-specific indexes or constraints were returned for `payload_sha256`
- no equivalent hash key was found in `public.asset_data_raw.payload_jsonb`
- current proven equivalent hash representation exists in `public.assets.external_ids.payload_hash`
- `public.assets.external_ids.payload_hash` was observed in `6` of `16` asset rows

Decision note:
- no schema change is justified from this proof alone; the current staging truth is absence in `public.asset_data_raw` plus equivalent representation in `public.assets.external_ids.payload_hash`

## Asset Links Discovery Proof (2026-03-13)

Proof source:
- `supabase_apply.yml` staging run `23066495260`
- verification file: `supabase/verification/0004_asset_links_discovery.sql`

Confirmed results:
- `public.asset_links` is not present in staging
- no columns, constraints, indexes, or policies were returned for `public.asset_links`
- `asset_data_raw` contains `2` proven fallback link evidence rows for `ASSET_LINK::` / `ASSET_LINK_DELETE::` and `record_type` values `asset_link` / `asset_link_delete`
- current canonical link authority is therefore `asset_data_raw` fallback evidence, not a dedicated `asset_links` table

Decision note:
- introducing `asset_links` now would require a future explicit schema proposal rather than a documentation-only normalization pass

Objects still unknown after staging proof:
- `asset_links` no longer remains unknown: staging proof run `23066495260` confirmed the table is absent, exposed no columns, constraints, indexes, or policies, and showed `asset_data_raw` fallback link evidence remains the only proven link authority
- no critical views were queried because none are proven by repository migrations on `main`
- no price-engine persistence object is proven by repository artifacts or this staging proof run

## Recommended Follow-on DB Tasks

1. Run the focused verification file `supabase/verification/0003_canonical_baseline_assertions.sql` after this branch merges so the reconciled repo baseline is re-proven against staging.
2. Treat `asset_data_raw` fallback evidence as the canonical link authority until a future explicit schema proposal decides whether `asset_links` should be introduced as a governed table.
3. Define whether ECC and price-engine surfaces will remain stub-only or receive explicit persistence contracts.
4. Open a later decision task only if semantic expansion, redesign, or repo-migration canonicalization for `external_ids` or its current `payload_hash` equivalence becomes necessary after these documented staging proofs.






## Source Record ID Discovery Proof (2026-03-14)

Proof source:
- `supabase_apply.yml` staging run `23073428262`
- verification file: `supabase/verification/0007_source_record_id_discovery.sql`

Confirmed results:
- `public.asset_data_raw.source_record_id` is not present in staging
- no column-specific indexes or constraints were returned for `source_record_id`
- no equivalent source-record identity key was found in `public.asset_data_raw.payload_jsonb`
- no equivalent source-record identity key was found in `public.assets.external_ids`

Decision note:
- no schema change is justified from this proof alone; the current staging truth is absence in `public.asset_data_raw` with no equivalent source-record identity field currently proven elsewhere

## Asset Specs Reconciled Discovery Proof (2026-03-14)

Proof source:
- `supabase_apply.yml` staging run `23090151849`
- verification file: `supabase/verification/0008_asset_specs_reconciled_discovery.sql`

Confirmed results:
- `public.asset_specs_reconciled` exists in staging with `16` columns and `0` rows
- structurally proven extra live columns are `spec_version`, `id`, `provenance`, `effective_at`, and `created_at`
- `organization_id` is also present in staging and indexed by `idx_asset_specs_org`
- primary key remains `asset_id`
- foreign key remains `asset_id -> public.assets(id)` with `ON DELETE CASCADE`
- unique versioning-oriented index `uq_asset_specs_asset_version` is present on `(organization_id, asset_id, spec_version)`
- temporal index `idx_asset_specs_effective` is present on `effective_at desc`
- RLS is enabled with active policies `asr_select`, `asr_insert`, `asr_update`, and `asr_delete`

Decision note:
- no schema change is justified from this proof alone; structural intent is proven, but live semantic usage remains unproven because staging currently has zero rows


