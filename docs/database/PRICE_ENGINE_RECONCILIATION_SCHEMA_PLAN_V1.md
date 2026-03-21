# Price Engine Reconciliation Schema Plan V1

## Purpose

Define a PostgreSQL / Supabase-ready storage plan for property-source imports, canonical property records, field-level reconciliation, manual overrides, repeatable MLS child records, evidence and document workflows, and import freshness before additional Price Engine UI work continues.

This document is a schema plan only. It does not claim live database implementation on `main`, does not activate any runtime behavior, and does not replace the current staging-proven schema inventory.

## Design Goals

- Database first for durable import storage and reconciliation state
- API fallback only when canonical DB-backed values are absent or stale
- Calculation last after canonical property state is resolved
- Support `corelogic`, `mls`, `field`, `dropbox`, `zipforms`, and `manual` source types
- Preserve raw source provenance, field-level comparison, and operator override history
- Preserve full MLS payload snapshots plus normalized repeatable child records such as rooms and media
- Preserve evidence, storage references, explicit version supersession, and checklist completeness state as first-class database records
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
- `canonical_document_state jsonb not null default '{}'::jsonb`
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
- `source_path text null`
- `source_locator jsonb not null default '{}'::jsonb`
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

### `public.property_file_storage_refs`

Canonical storage reference table for Dropbox paths, Supabase storage objects, direct provider file URLs, or other external file pointers.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `storage_provider text not null`
- `storage_bucket text null`
- `storage_path text null`
- `provider_file_key text null`
- `external_url text null`
- `canonical_pointer jsonb not null default '{}'::jsonb`
- `file_name text null`
- `mime_type text null`
- `byte_size bigint null`
- `checksum_sha256 text null`
- `checksum_md5 text null`
- `captured_from_source_type text not null`
- `source_import_id uuid null references public.property_source_imports(id)`
- `import_run_id uuid null references public.property_import_runs(id)`
- `fetched_at timestamptz null`
- `last_verified_at timestamptz null`
- `created_by_user_id uuid null`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `storage_provider in ('dropbox', 'supabase_storage', 'external_url', 'zipforms', 'manual')`
- check `captured_from_source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')`
- index `(property_id, storage_provider)`
- index `(provider_file_key)`

### `public.property_file_versions`

Version ledger for any stored or referenced file, with explicit supersession links and audit retention.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `storage_ref_id uuid not null references public.property_file_storage_refs(id) on delete restrict`
- `file_class text not null`
- `version_number integer not null`
- `version_label text null`
- `review_state text not null default 'received'`
- `verification_state text not null default 'unverified'`
- `supersedes_file_version_id uuid null references public.property_file_versions(id)`
- `superseded_by_file_version_id uuid null references public.property_file_versions(id)`
- `is_latest boolean not null default true`
- `is_approved boolean not null default false`
- `client_visibility_state text not null default 'internal_only'`
- `uploaded_by_user_id uuid null`
- `captured_by_user_id uuid null`
- `source_type text not null`
- `source_import_id uuid null references public.property_source_imports(id)`
- `import_run_id uuid null references public.property_import_runs(id)`
- `version_metadata jsonb not null default '{}'::jsonb`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')`
- check `file_class in ('listing_photo', 'field_photo', 'floor_plan', 'inspection_report', 'construction_proposal', 'appraisal', 'loi', 'contract_executed', 'contract_amendment', 'disclosure', 'due_diligence_doc', 'title_doc', 'closing_doc', 'correspondence', 'client_artifact')`
- check `review_state in ('received', 'under_review', 'approved', 'rejected', 'archived')`
- check `verification_state in ('unverified', 'verified', 'mismatch', 'expired')`
- check `client_visibility_state in ('internal_only', 'client_visible', 'client_hidden', 'client_expired')`
- unique `(property_id, file_class, version_number)`
- unique partial index on `(property_id, file_class)` where `is_latest = true`

### `public.property_evidence_assets`

Canonical evidence registry that links property-level media, reports, field captures, and imported file versions to property workflows.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `source_type text not null`
- `evidence_class text not null`
- `source_import_id uuid null references public.property_source_imports(id)`
- `import_run_id uuid null references public.property_import_runs(id)`
- `source_media_id uuid null references public.property_source_media(id)`
- `file_version_id uuid null references public.property_file_versions(id)`
- `storage_ref_id uuid null references public.property_file_storage_refs(id)`
- `caption text null`
- `description text null`
- `captured_at timestamptz null`
- `captured_by_user_id uuid null`
- `review_state text not null default 'received'`
- `client_visibility_state text not null default 'internal_only'`
- `is_primary boolean not null default false`
- `sort_order integer null`
- `metadata jsonb not null default '{}'::jsonb`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')`
- check `evidence_class in ('listing_photo', 'field_photo', 'floor_plan', 'inspection_report', 'construction_proposal', 'appraisal', 'loi', 'contract_executed', 'contract_amendment', 'disclosure', 'due_diligence_doc', 'title_doc', 'closing_doc', 'correspondence', 'client_artifact')`
- index `(property_id, evidence_class)`
- index `(transaction_id, evidence_class)`

### `public.property_document_packets`

Logical document bundles for a property or transaction, such as acquisition packet, diligence packet, title packet, or closing packet.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `packet_type text not null`
- `packet_status text not null default 'open'`
- `deal_stage text null`
- `packet_label text null`
- `metadata jsonb not null default '{}'::jsonb`
- `created_by_user_id uuid null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Recommended constraints:
- check `packet_status in ('open', 'in_review', 'complete', 'archived')`
- index `(property_id, packet_type, deal_stage)`

### `public.property_document_requirements`

Checklist definition and current requirement state for documents expected at a property or transaction stage.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `document_packet_id uuid null references public.property_document_packets(id) on delete set null`
- `requirement_key text not null`
- `file_class text not null`
- `checklist_group text not null`
- `deal_stage text null`
- `required_flag boolean not null default true`
- `requirement_status text not null default 'missing'`
- `review_state text not null default 'pending'`
- `latest_approved_file_version_id uuid null references public.property_file_versions(id)`
- `current_submission_id uuid null`
- `latest_received_at timestamptz null`
- `notes text null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Recommended constraints:
- check `file_class in ('listing_photo', 'field_photo', 'floor_plan', 'inspection_report', 'construction_proposal', 'appraisal', 'loi', 'contract_executed', 'contract_amendment', 'disclosure', 'due_diligence_doc', 'title_doc', 'closing_doc', 'correspondence', 'client_artifact')`
- check `requirement_status in ('missing', 'received', 'under_review', 'approved', 'rejected', 'waived', 'superseded')`
- check `review_state in ('pending', 'under_review', 'approved', 'rejected')`
- unique `(property_id, transaction_id, requirement_key)`
- index `(property_id, deal_stage, checklist_group)`

### `public.property_document_submissions`

Submission ledger connecting requirements to received file versions, including supersession and approval outcomes.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `document_requirement_id uuid not null references public.property_document_requirements(id) on delete cascade`
- `file_version_id uuid not null references public.property_file_versions(id) on delete restrict`
- `submitted_by_user_id uuid null`
- `submitted_at timestamptz not null default now()`
- `submission_source_type text not null`
- `review_state text not null default 'pending'`
- `reviewed_by_user_id uuid null`
- `reviewed_at timestamptz null`
- `approval_notes text null`
- `supersedes_submission_id uuid null references public.property_document_submissions(id)`
- `superseded_by_submission_id uuid null references public.property_document_submissions(id)`
- `is_latest boolean not null default true`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `submission_source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')`
- check `review_state in ('pending', 'under_review', 'approved', 'rejected', 'superseded')`
- index `(document_requirement_id, is_latest)`

### `public.property_client_access_links`

Visibility and share-control table for client-facing file access without treating Dropbox or any storage provider as the database of record.

Key columns:
- `id uuid primary key default gen_random_uuid()`
- `organization_id uuid null references public.organizations(id)`
- `property_id uuid not null references public.properties(id) on delete cascade`
- `asset_id uuid null references public.assets(id)`
- `transaction_id uuid null`
- `file_version_id uuid not null references public.property_file_versions(id) on delete cascade`
- `storage_ref_id uuid not null references public.property_file_storage_refs(id) on delete restrict`
- `visibility_state text not null default 'client_hidden'`
- `share_token text null`
- `share_url text null`
- `expires_at timestamptz null`
- `last_accessed_at timestamptz null`
- `access_metadata jsonb not null default '{}'::jsonb`
- `created_by_user_id uuid null`
- `created_at timestamptz not null default now()`

Recommended constraints:
- check `visibility_state in ('client_hidden', 'client_visible', 'client_revoked', 'client_expired')`
- unique partial index on `(file_version_id)` where `visibility_state = 'client_visible'`

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
- check `source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')`

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
- `public.property_file_storage_refs` stores canonical storage-provider pointers for evidence and documents.
- `public.property_file_versions` stores explicit version and supersession lineage for files.
- `public.property_evidence_assets` registers evidence/media assets linked to property workflows.
- `public.property_document_packets` groups property or transaction document workflows.
- `public.property_document_requirements` stores checklist requirements by stage and file class.
- `public.property_document_submissions` stores received versions against requirements.
- `public.property_client_access_links` controls client-visible access without making the storage provider authoritative.
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

## File And Versioning Model

### Storage references

- `public.property_file_storage_refs` is the canonical database record for a file pointer.
- Dropbox paths, ZipForms export links, Supabase storage object paths, and direct external URLs are stored here.
- The storage provider is never the database of record; the durable Altus reference row is.

### Versioning

- `public.property_file_versions` is the immutable file-version ledger.
- Every new upload, import, or returned ZipForms document creates a new file version row.
- `version_number`, `supersedes_file_version_id`, and `superseded_by_file_version_id` make replacement explicit.
- Superseded rows remain queryable for audit.
- `is_latest` marks the newest version per property and file class, while `is_approved` identifies the currently approved version.

### Evidence linkage

- `public.property_evidence_assets` links media or document evidence to the property workflow.
- Media imported from MLS may have both a `property_source_media` row and an evidence row when the asset becomes workflow-relevant.
- Field captures, Dropbox-sourced reports, and ZipForms contract documents can all be represented through `property_evidence_assets` plus `property_file_versions`.

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

## Completeness And Checklist Model

### Requirement matrix

- `public.property_document_requirements` defines the required-document matrix by property, optional transaction, deal stage, checklist group, and file class.
- `required_flag` allows optional versus mandatory artifacts to be modeled in the same table.

### Current receipt state

- `requirement_status` stores whether a required item is missing, received, under review, approved, rejected, waived, or superseded.
- `latest_approved_file_version_id` points to the currently approved version when one exists.
- `current_submission_id` tracks the most recent submission under review or recently received.

### Submission flow

- Each received artifact creates a `property_file_versions` row.
- Each requirement-linked delivery creates a `property_document_submissions` row.
- If a newer version replaces the prior one, submission supersession and file-version supersession are both recorded explicitly.
- Missing items are queryable directly from requirements whose `required_flag = true` and `requirement_status in ('missing', 'rejected')`.

### Property-level completeness summary

- `properties.canonical_document_state` stores an optional denormalized summary for fast reads.
- The authoritative source remains the requirements and submissions tables.

## Client Visibility And Access Model

- `public.property_file_versions.client_visibility_state` stores the version-level visibility intent.
- `public.property_client_access_links` stores the actual share-control record, including tokenized URL, expiry, and last access timestamp.
- Client-visible files should always reference a durable `property_file_versions` row and a durable `property_file_storage_refs` row.
- Revoking client access should update the visibility row, not delete historical file or submission records.

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
- `public.property_file_storage_refs`
- `public.property_file_versions`
- `public.property_evidence_assets`
- `public.property_document_packets`
- `public.property_document_requirements`
- `public.property_document_submissions`
- `public.property_client_access_links`

These tables preserve full source lineage, raw payload snapshots, repeatable child records, and normalized field evidence without deciding final authority by themselves.

### Canonical records

- `public.properties`
- `public.property_reconciliation_status`
- `public.property_manual_overrides`

These tables represent the current chosen property truth, the decision state behind each field, and any operator override history.

## PostgreSQL / Supabase Readiness Notes

- Prefer `jsonb` for flexible structured fields like address components, rent indicators, valuation metadata, tax metadata, and canonical source summaries.
- Prefer `jsonb` for storage pointers, checklist metadata, access metadata, document state summaries, and evidence metadata where provider-specific structures vary.
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
8. Create `public.property_file_storage_refs`
9. Create `public.property_file_versions`
10. Create `public.property_evidence_assets`
11. Create `public.property_document_packets`
12. Create `public.property_document_requirements`
13. Create `public.property_document_submissions`
14. Create `public.property_client_access_links`
15. Create `public.property_reconciliation_status`
16. Create `public.property_manual_overrides`
17. Add indexes and foreign keys
18. Add non-destructive verification SQL for table existence, key constraints, source-type checks, child-record relationships, and supersession links

## Out Of Scope For This Slice

- UI workflows
- runtime handler changes
- source-specific parser implementation
- background jobs and scheduling semantics
- calculated price-engine outputs
- final identity derivation rule for `property_key`
- policy / RLS implementation details
