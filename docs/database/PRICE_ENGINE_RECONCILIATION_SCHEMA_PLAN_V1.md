# Price Engine Reconciliation Schema Plan V1

## Purpose

Define a PostgreSQL / Supabase-ready storage plan for property-source imports, canonical property records, field-level reconciliation, manual overrides, repeatable MLS child records, and import freshness before additional Price Engine UI work continues.

This document is a schema plan only. It does not claim live database implementation on `main`, does not activate any runtime behavior, and does not replace the current staging-proven schema inventory.

## Design Goals

- Database first for durable import storage and reconciliation state
- API fallback only when canonical DB-backed values are absent or stale
- Calculation last after canonical property state is resolved
- Support `corelogic`, `mls`, and `manual` source types
- Preserve raw source provenance, field-level comparison, and operator override history
- Preserve full MLS payload snapshots plus normalized repeatable child records such as rooms and media
- Stay additive to the current Supabase / PostgreSQL model

## Proposed Tables

### `public.properties`

Canonical property record used by downstream read models and calculations after reconciliation chooses field-level winners.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `asset_id uuid null references public.assets(id)`
- `property_key text not null unique`
- `status text not null default 'active'`
- `canonical_address jsonb not null default '{}'::jsonb`
- `canonical_apn text null`
- `canonical_beds numeric(8,2) null`
- `canonical_baths numeric(8,2) null`
- `canonical_sqft integer null`
- `canonical_lot_size_sqft numeric(14,2) null`
- `canonical_year_built integer null`
- `canonical_property_type text null`
- `canonical_unit_count integer null`
- `canonical_rent_indicators jsonb not null default '{}'::jsonb`
- `canonical_valuation jsonb not null default '{}'::jsonb`
- `canonical_tax_metadata jsonb not null default '{}'::jsonb`
- `canonical_source_summary jsonb not null default '{}'::jsonb`
- `canonical_listing_lifecycle jsonb not null default '{}'::jsonb`
- `canonical_geo jsonb not null default '{}'::jsonb`
- `canonical_systems_features jsonb not null default '{}'::jsonb`
- `canonical_association_terms jsonb not null default '{}'::jsonb`
- `canonical_remarks jsonb not null default '{}'::jsonb`
- `last_reconciled_at timestamptz null`
- `last_imported_at timestamptz null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Notes:
- `property_key` is the stable canonical identity for imports and reconciliation. It may be derived from asset linkage, normalized address, APN, or another governed identity rule in a later implementation slice.
- Canonical columns intentionally keep the final chosen value easy to read without traversing source tables for every calculation request.
- Canonical JSON columns allow the first implementation to carry large MLS surface areas without forcing unstable early column explosion for every feature-specific subfield.

### `public.property_import_runs`

Tracks each import batch or fetch execution so freshness and replay lineage are queryable.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `source_type text not null`
- `provider_name text not null`
- `run_status text not null default 'started'`
- `trigger_type text not null default 'manual'`
- `source_started_at timestamptz null`
- `source_completed_at timestamptz null`
- `ingested_at timestamptz not null default now()`
- `source_snapshot_at timestamptz null`
- `record_count integer not null default 0`
- `success_count integer not null default 0`
- `error_count integer not null default 0`
- `metadata jsonb not null default '{}'::jsonb`
- `created_by_user_id uuid null`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `source_type in ('corelogic', 'mls', 'manual')`
- index on `(source_type, ingested_at desc)`

### `public.property_source_imports`

One row per property-level source snapshot imported from CoreLogic, MLS, or manual entry.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `import_run_id uuid not null references public.property_import_runs(id) on delete restrict`
- `source_type text not null`
- `provider_record_id text null`
- `provider_record_key text null`
- `source_record_version text null`
- `source_timestamp timestamptz null`
- `source_effective_at timestamptz null`
- `listing_timestamp timestamptz null`
- `listing_status text null`
- `listing_event jsonb not null default '{}'::jsonb`
- `is_latest boolean not null default true`
- `raw_payload jsonb not null default '{}'::jsonb`
- `raw_payload_hash text null`
- `ingested_at timestamptz not null default now()`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `source_type in ('corelogic', 'mls', 'manual')`
- unique partial index on `(property_id, source_type)` where `is_latest = true`
- index on `(import_run_id)`
- index on `(provider_record_key)`
- index on `(source_type, listing_status)`

### `public.property_source_field_values`

Normalized field-level values extracted from each source import for comparison and reconciliation.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `source_import_id uuid not null references public.property_source_imports(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `field_name text not null`
- `value_text text null`
- `value_number numeric(18,4) null`
- `value_integer bigint null`
- `value_boolean boolean null`
- `value_jsonb jsonb null`
- `value_date date null`
- `value_timestamp timestamptz null`
- `normalized_value jsonb not null default '{}'::jsonb`
- `comparison_hash text null`
- `source_timestamp timestamptz null`
- `is_present boolean not null default true`
- `created_at timestamptz not null default now()`

Required `field_name` support in the first implementation:
- `address`
- `apn`
- `beds`
- `baths`
- `sqft`
- `lot_size`
- `year_built`
- `property_type`
- `unit_count`
- `rent_indicators`
- `valuation`
- `tax_metadata`

Expanded MLS-oriented `field_name` coverage:
- `listing_status`
- `listing_sub_status`
- `listing_type`
- `listing_contract_date`
- `listing_price`
- `listing_price_per_sqft`
- `days_on_market`
- `cumulative_days_on_market`
- `mls_number`
- `source_system_key`
- `parcel_number`
- `legal_description`
- `subdivision`
- `county`
- `state`
- `postal_code`
- `latitude`
- `longitude`
- `cooling`
- `heating`
- `parking`
- `garage_spaces`
- `construction_materials`
- `roof`
- `foundation`
- `pool`
- `water`
- `sewer`
- `hoa`
- `hoa_fee`
- `tax_year`
- `tax_amount`
- `possession`
- `financing_terms`
- `public_remarks`
- `private_remarks`
- `directions`

Recommended constraints:
- unique `(source_import_id, field_name)`
- index `(property_id, field_name)`
- check that at least one typed value column or `normalized_value` is populated when `is_present = true`

### `public.property_reconciliation_status`

Field-level decision table that records the current winner, conflict state, and source basis for each canonical field.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `field_name text not null`
- `resolution_status text not null default 'pending'`
- `conflict_flag boolean not null default false`
- `override_flag boolean not null default false`
- `selected_source_type text null`
- `selected_source_import_id uuid null references public.property_source_imports(id)`
- `selected_field_value_id uuid null references public.property_source_field_values(id)`
- `selected_canonical_value jsonb not null default '{}'::jsonb`
- `selected_source_timestamp timestamptz null`
- `decision_reason text null`
- `reviewed_by_user_id uuid null`
- `reviewed_at timestamptz null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Recommended constraints:
- unique `(property_id, field_name)`
- check `selected_source_type in ('corelogic', 'mls', 'manual')` when not null
- check `resolution_status in ('pending', 'matched', 'conflicted', 'overridden', 'fallback', 'unresolved')`

### `public.property_manual_overrides`

Immutable operator-entered override log for fields that intentionally differ from current imported source values.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `field_name text not null`
- `override_value jsonb not null`
- `override_reason text null`
- `override_user_id uuid not null`
- `override_created_at timestamptz not null default now()`
- `override_expires_at timestamptz null`
- `is_active boolean not null default true`
- `superseded_by_override_id uuid null references public.property_manual_overrides(id)`
- `source_context jsonb not null default '{}'::jsonb`

Recommended constraints:
- index `(property_id, field_name, is_active)`
- optional unique partial index on `(property_id, field_name)` where `is_active = true`

### `public.property_source_rooms`

Repeatable normalized room records extracted from MLS or other source payloads.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `source_import_id uuid not null references public.property_source_imports(id) on delete cascade`
- `source_type text not null`
- `provider_room_key text null`
- `room_name text not null`
- `room_level text null`
- `length_value numeric(10,2) null`
- `length_unit text null default 'ft'`
- `width_value numeric(10,2) null`
- `width_unit text null default 'ft'`
- `area_sqft numeric(14,2) null`
- `remarks text null`
- `features jsonb not null default '{}'::jsonb`
- `sort_order integer null`
- `source_timestamp timestamptz null`
- `created_at timestamptz not null default now()`

Recommended constraints:
- index `(property_id, source_import_id, sort_order nulls last)`
- index `(property_id, room_name)`

### `public.property_source_media`

Repeatable normalized media and photo records extracted from MLS or other source payloads.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `source_import_id uuid not null references public.property_source_imports(id) on delete cascade`
- `media_id uuid not null default gen_random_uuid()`
- `source_type text not null`
- `provider_media_key text null`
- `media_url text null`
- `storage_pointer text null`
- `sort_order integer null`
- `media_type text not null`
- `caption text null`
- `description text null`
- `mime_type text null`
- `width_px integer null`
- `height_px integer null`
- `fetched_at timestamptz not null default now()`
- `source_timestamp timestamptz null`
- `is_primary boolean not null default false`
- `created_at timestamptz not null default now()`

Recommended constraints:
- index `(property_id, source_import_id, sort_order nulls last)`
- index `(provider_media_key)`
- check `(media_url is not null) or (storage_pointer is not null)`

### `public.property_source_association_facts`

Optional repeatable association, amenities, and terms records when the source exposes structured HOA or community detail.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `organization_id uuid null references public.organizations(id)`
- `source_import_id uuid not null references public.property_source_imports(id) on delete cascade`
- `source_type text not null`
- `association_name text null`
- `association_fee numeric(12,2) null`
- `association_fee_frequency text null`
- `association_phone text null`
- `amenities jsonb not null default '[]'::jsonb`
- `community_features jsonb not null default '[]'::jsonb`
- `terms jsonb not null default '{}'::jsonb`
- `source_timestamp timestamptz null`
- `created_at timestamptz not null default now()`

Recommended constraints:
- index `(property_id, source_import_id)`

## Relationships

- `public.properties` is the canonical parent record.
- `public.property_import_runs` records batch-level lineage.
- `public.property_source_imports` belongs to one `property_import_run` and one `property`.
- `public.property_source_field_values` belongs to one `property_source_import`.
- `public.property_reconciliation_status` stores one current decision row per `(property_id, field_name)`.
- `public.property_manual_overrides` stores immutable operator override history per property field.
- `public.property_source_rooms` stores repeatable room rows owned by one source import.
- `public.property_source_media` stores repeatable media rows owned by one source import.
- `public.property_source_association_facts` stores optional structured association and amenities detail owned by one source import.
- `public.properties.asset_id` provides optional linkage back to the existing `public.assets` surface when a property is tied to the current asset model.

## Conflict And Override Handling

### Conflict model

- Each source snapshot writes one `property_source_imports` row and one `property_source_field_values` row per tracked field.
- Reconciliation compares all current `property_source_field_values` for the same `(property_id, field_name)`.
- If source values normalize to the same semantic value, set:
  - `property_reconciliation_status.resolution_status = 'matched'`
  - `conflict_flag = false`
- If values disagree or one trusted source is missing while another is present, set:
  - `resolution_status = 'conflicted'` or `fallback`
  - `conflict_flag = true` when disagreement exists
- `selected_canonical_value` always stores the current chosen field value in normalized JSON form, regardless of source type.

### Override model

- Manual resolution does not mutate historical source imports.
- When an operator overrides a field:
  - insert an immutable row into `property_manual_overrides`
  - point `property_reconciliation_status.selected_source_type = 'manual'`
  - set `override_flag = true`
  - set `resolution_status = 'overridden'`
  - set `selected_canonical_value` from the override payload
  - stamp `reviewed_by_user_id` and `reviewed_at`
- Override provenance is preserved through `override_user_id`, `override_created_at`, and optional `source_context`.

## Freshness And Import Tracking Model

### Run tracking

- `property_import_runs` is the authoritative import batch ledger.
- One run may create many `property_source_imports`.
- `source_snapshot_at` captures the provider-side data currency when available.
- `ingested_at` captures when Altus stored the batch.

### Per-property freshness

- `property_source_imports.source_timestamp` records the provider timestamp for a specific property snapshot.
- `property_source_imports.is_latest` marks the current latest import per property and source type.
- `properties.last_imported_at` records the most recent successful source arrival across all sources.
- `properties.last_reconciled_at` records when canonical field selection was last recomputed.

### Staleness evaluation

Recommended future read rule:
- calculations should prefer canonical `properties.*` values only when the corresponding `property_reconciliation_status` row is not `unresolved` and the underlying selected source import is within the freshness window required by the consuming workflow
- otherwise the caller may fall back to a direct API fetch or surface the field as stale / unresolved

## Field Coverage Mapping

Minimum initial mapping:

- `address` -> `properties.canonical_address`
- `apn` -> `properties.canonical_apn`
- `beds` -> `properties.canonical_beds`
- `baths` -> `properties.canonical_baths`
- `sqft` -> `properties.canonical_sqft`
- `lot_size` -> `properties.canonical_lot_size_sqft`
- `year_built` -> `properties.canonical_year_built`
- `property_type` -> `properties.canonical_property_type`
- `unit_count` -> `properties.canonical_unit_count`
- `rent_indicators` -> `properties.canonical_rent_indicators`
- `valuation` / `AVM` -> `properties.canonical_valuation`
- `tax_metadata` -> `properties.canonical_tax_metadata`

Expanded canonical ownership buckets:

- Listing lifecycle -> `properties.canonical_listing_lifecycle`
  - example members: `listing_status`, `listing_sub_status`, `listing_type`, `listing_contract_date`, `listing_price`, `days_on_market`
- Property identity -> split between scalar canonical fields and `canonical_source_summary`
  - example members: `mls_number`, `source_system_key`, alternate parcel / provider identifiers
- Physical structure -> scalar canonical fields plus `properties.canonical_systems_features`
  - example members: `beds`, `baths`, `sqft`, `lot_size`, `year_built`, `property_type`, `unit_count`, systems/features
- Systems/features -> `properties.canonical_systems_features`
  - example members: heating, cooling, parking, garage spaces, roof, foundation, pool, water, sewer
- Taxes / association / terms -> `properties.canonical_tax_metadata` and `properties.canonical_association_terms`
  - example members: `tax_year`, `tax_amount`, HOA, HOA fee, possession, financing terms
- Geo fields -> `properties.canonical_geo`
  - example members: latitude, longitude, county, subdivision, postal details
- Remarks -> `properties.canonical_remarks`
  - example members: public remarks, private remarks, directions, marketing remarks

## Room And Media Storage Model

### Room records

- Full source room arrays remain inside `property_source_imports.raw_payload`
- Normalized repeatable room rows live in `public.property_source_rooms`
- Room-level canonicalization is deferred until a later explicit need is proven; the first schema plan treats rooms as source-owned repeatable evidence, not canonical scalar property state

### Media records

- Full source media arrays remain inside `property_source_imports.raw_payload`
- Normalized repeatable media rows live in `public.property_source_media`
- Media ownership remains source-scoped first; future curated or canonical media selection can be layered later without losing original ordering and provider references

### Association / amenities records

- Full source association payloads remain inside `property_source_imports.raw_payload`
- Structured repeatable or semi-structured association facts live in `public.property_source_association_facts`
- Canonical summary fields for cockpit and calculations live in `properties.canonical_association_terms`

## Canonical Vs Source Ownership Model

### Source-owned records

- `public.property_import_runs`
- `public.property_source_imports`
- `public.property_source_field_values`
- `public.property_source_rooms`
- `public.property_source_media`
- `public.property_source_association_facts`

These tables preserve full source lineage, raw payload snapshots, repeatable child records, and normalized field evidence without deciding final authority by themselves.

### Canonical records

- `public.properties`
- `public.property_reconciliation_status`
- `public.property_manual_overrides`

These tables represent the current chosen property truth, the decision state behind each field, and any operator override history.

## PostgreSQL / Supabase Readiness Notes

- Prefer `jsonb` for flexible structured fields like address components, rent indicators, valuation metadata, tax metadata, and canonical source summaries.
- Prefer `jsonb` for broad MLS surface buckets like listing lifecycle, geo bundles, systems/features, association terms, and remarks when the exact long-term column set is still evolving.
- Use ordinary tables first; analytical or materialized views can be added later after authority and refresh behavior are proven.
- Add RLS only after org-scoping and operator roles for manual overrides are explicitly defined.
- Add helper functions only after the baseline tables are agreed; this plan intentionally starts with explicit relational tables.

## Suggested First Migration Order

1. Create `public.properties`
2. Create `public.property_import_runs`
3. Create `public.property_source_imports`
4. Create `public.property_source_field_values`
5. Create `public.property_source_rooms`
6. Create `public.property_source_media`
7. Create `public.property_source_association_facts`
8. Create `public.property_reconciliation_status`
9. Create `public.property_manual_overrides`
10. Add indexes and foreign keys
11. Add non-destructive verification SQL for table existence, key constraints, source-type checks, and repeatable child-record relationships

## Out Of Scope For This Slice

- UI workflows
- runtime handler changes
- source-specific parser implementation
- background jobs and scheduling semantics
- calculated price-engine outputs
- final identity derivation rule for `property_key`
- policy / RLS implementation details
