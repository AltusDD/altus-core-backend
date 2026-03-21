begin;

create extension if not exists "pgcrypto";

create table if not exists public.properties (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  asset_id uuid references public.assets(id) on delete set null,
  property_key text not null unique,
  status text not null default 'active',
  canonical_address jsonb not null default '{}'::jsonb,
  canonical_apn text,
  canonical_beds numeric(8,2),
  canonical_baths numeric(8,2),
  canonical_sqft integer,
  canonical_lot_size_sqft numeric(14,2),
  canonical_year_built integer,
  canonical_property_type text,
  canonical_unit_count integer,
  canonical_rent_indicators jsonb not null default '{}'::jsonb,
  canonical_valuation jsonb not null default '{}'::jsonb,
  canonical_tax_metadata jsonb not null default '{}'::jsonb,
  canonical_source_summary jsonb not null default '{}'::jsonb,
  canonical_listing_lifecycle jsonb not null default '{}'::jsonb,
  canonical_geo jsonb not null default '{}'::jsonb,
  canonical_systems_features jsonb not null default '{}'::jsonb,
  canonical_association_terms jsonb not null default '{}'::jsonb,
  canonical_remarks jsonb not null default '{}'::jsonb,
  canonical_document_state jsonb not null default '{}'::jsonb,
  last_reconciled_at timestamptz,
  last_imported_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint properties_status_check check (
    status in ('draft', 'active', 'inactive', 'archived')
  )
);

create index if not exists idx_properties_org on public.properties (organization_id);
create index if not exists idx_properties_asset on public.properties (asset_id);

create table if not exists public.property_import_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  source_type text not null,
  provider_name text not null,
  run_status text not null default 'started',
  trigger_type text not null default 'manual',
  source_started_at timestamptz,
  source_completed_at timestamptz,
  ingested_at timestamptz not null default now(),
  source_snapshot_at timestamptz,
  record_count integer not null default 0,
  success_count integer not null default 0,
  error_count integer not null default 0,
  metadata jsonb not null default '{}'::jsonb,
  created_by_user_id uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  constraint property_import_runs_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_import_runs_status_check check (
    run_status in ('started', 'running', 'completed', 'failed', 'partial', 'cancelled')
  )
);

create index if not exists idx_property_import_runs_source_ingested
  on public.property_import_runs (source_type, ingested_at desc);
create index if not exists idx_property_import_runs_org
  on public.property_import_runs (organization_id, created_at desc);

create table if not exists public.property_source_imports (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.properties(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  import_run_id uuid not null references public.property_import_runs(id) on delete restrict,
  source_type text not null,
  provider_record_id text,
  provider_record_key text,
  source_record_version text,
  source_timestamp timestamptz,
  source_effective_at timestamptz,
  listing_timestamp timestamptz,
  listing_status text,
  listing_event jsonb not null default '{}'::jsonb,
  source_path text,
  source_locator jsonb not null default '{}'::jsonb,
  is_latest boolean not null default true,
  raw_payload jsonb not null default '{}'::jsonb,
  raw_payload_hash text,
  ingested_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  constraint property_source_imports_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  )
);

create unique index if not exists uq_property_source_imports_latest
  on public.property_source_imports (property_id, source_type)
  where is_latest = true;
create index if not exists idx_property_source_imports_run
  on public.property_source_imports (import_run_id);
create index if not exists idx_property_source_imports_provider_key
  on public.property_source_imports (provider_record_key);
create index if not exists idx_property_source_imports_property_source
  on public.property_source_imports (property_id, source_type, created_at desc);

create table if not exists public.property_source_field_values (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.properties(id) on delete cascade,
  source_import_id uuid not null references public.property_source_imports(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  field_name text not null,
  value_text text,
  value_number numeric(18,4),
  value_integer bigint,
  value_boolean boolean,
  value_jsonb jsonb,
  value_date date,
  value_timestamp timestamptz,
  normalized_value jsonb not null default '{}'::jsonb,
  comparison_hash text,
  source_timestamp timestamptz,
  is_present boolean not null default true,
  created_at timestamptz not null default now(),
  constraint uq_property_source_field_values unique (source_import_id, field_name),
  constraint property_source_field_values_payload_check check (
    is_present = false
    or value_text is not null
    or value_number is not null
    or value_integer is not null
    or value_boolean is not null
    or value_jsonb is not null
    or value_date is not null
    or value_timestamp is not null
    or normalized_value <> '{}'::jsonb
  )
);

create index if not exists idx_property_source_field_values_property_field
  on public.property_source_field_values (property_id, field_name);
create index if not exists idx_property_source_field_values_hash
  on public.property_source_field_values (comparison_hash);

create table if not exists public.property_source_rooms (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.properties(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  source_import_id uuid not null references public.property_source_imports(id) on delete cascade,
  source_type text not null,
  provider_room_key text,
  room_name text not null,
  room_level text,
  length_value numeric(10,2),
  length_unit text default 'ft',
  width_value numeric(10,2),
  width_unit text default 'ft',
  area_sqft numeric(14,2),
  remarks text,
  features jsonb not null default '{}'::jsonb,
  sort_order integer,
  source_timestamp timestamptz,
  created_at timestamptz not null default now(),
  constraint property_source_rooms_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  )
);

create index if not exists idx_property_source_rooms_sort
  on public.property_source_rooms (property_id, source_import_id, sort_order);
create index if not exists idx_property_source_rooms_name
  on public.property_source_rooms (property_id, room_name);

create table if not exists public.property_file_storage_references (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  property_id uuid references public.properties(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete set null,
  transaction_id uuid,
  storage_provider text not null,
  storage_bucket text,
  storage_path text,
  provider_file_key text,
  external_url text,
  canonical_pointer jsonb not null default '{}'::jsonb,
  file_name text,
  mime_type text,
  byte_size bigint,
  checksum_sha256 text,
  checksum_md5 text,
  captured_from_source_type text not null,
  source_import_id uuid references public.property_source_imports(id) on delete set null,
  import_run_id uuid references public.property_import_runs(id) on delete set null,
  fetched_at timestamptz,
  last_verified_at timestamptz,
  created_by_user_id uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  constraint property_file_storage_references_provider_check check (
    storage_provider in ('dropbox', 'supabase_storage', 'external_url', 'zipforms', 'manual')
  ),
  constraint property_file_storage_references_source_type_check check (
    captured_from_source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_file_storage_references_location_check check (
    storage_path is not null
    or external_url is not null
    or provider_file_key is not null
  )
);

create index if not exists idx_property_file_storage_refs_property
  on public.property_file_storage_references (property_id, storage_provider);
create index if not exists idx_property_file_storage_refs_provider_key
  on public.property_file_storage_references (provider_file_key);

create table if not exists public.property_file_versions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  property_id uuid not null references public.properties(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete set null,
  transaction_id uuid,
  storage_reference_id uuid not null references public.property_file_storage_references(id) on delete restrict,
  file_class text not null,
  version_number integer not null,
  version_label text,
  review_state text not null default 'received',
  verification_state text not null default 'unverified',
  supersedes_file_version_id uuid references public.property_file_versions(id) on delete set null,
  superseded_by_file_version_id uuid references public.property_file_versions(id) on delete set null,
  is_latest boolean not null default true,
  is_approved boolean not null default false,
  client_visibility_state text not null default 'internal_only',
  uploaded_by_user_id uuid references auth.users(id) on delete set null,
  captured_by_user_id uuid references auth.users(id) on delete set null,
  source_type text not null,
  source_import_id uuid references public.property_source_imports(id) on delete set null,
  import_run_id uuid references public.property_import_runs(id) on delete set null,
  version_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint property_file_versions_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_file_versions_file_class_check check (
    file_class in (
      'listing_photo',
      'field_photo',
      'floor_plan',
      'inspection_report',
      'construction_proposal',
      'appraisal',
      'loi',
      'contract_executed',
      'contract_amendment',
      'disclosure',
      'due_diligence_doc',
      'title_doc',
      'closing_doc',
      'correspondence',
      'client_artifact'
    )
  ),
  constraint property_file_versions_review_state_check check (
    review_state in ('received', 'under_review', 'approved', 'rejected', 'archived')
  ),
  constraint property_file_versions_verification_state_check check (
    verification_state in ('unverified', 'verified', 'mismatch', 'expired')
  ),
  constraint property_file_versions_client_visibility_check check (
    client_visibility_state in ('internal_only', 'client_visible', 'client_hidden', 'client_expired')
  ),
  constraint uq_property_file_versions unique (property_id, file_class, version_number)
);

create unique index if not exists uq_property_file_versions_latest
  on public.property_file_versions (property_id, file_class)
  where is_latest = true;
create index if not exists idx_property_file_versions_transaction
  on public.property_file_versions (transaction_id, file_class, created_at desc);

create table if not exists public.property_source_media (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.properties(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  source_import_id uuid not null references public.property_source_imports(id) on delete cascade,
  source_type text not null,
  provider_media_key text,
  storage_reference_id uuid references public.property_file_storage_references(id) on delete set null,
  file_version_id uuid references public.property_file_versions(id) on delete set null,
  media_url text,
  storage_pointer text,
  sort_order integer,
  media_type text not null,
  caption text,
  description text,
  mime_type text,
  width_px integer,
  height_px integer,
  fetched_at timestamptz not null default now(),
  source_timestamp timestamptz,
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  constraint property_source_media_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_source_media_location_check check (
    media_url is not null
    or storage_pointer is not null
    or storage_reference_id is not null
    or file_version_id is not null
  )
);

create index if not exists idx_property_source_media_sort
  on public.property_source_media (property_id, source_import_id, sort_order);
create index if not exists idx_property_source_media_provider_key
  on public.property_source_media (provider_media_key);

create table if not exists public.property_reconciliation_status (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.properties(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  field_name text not null,
  resolution_status text not null default 'pending',
  conflict_flag boolean not null default false,
  override_flag boolean not null default false,
  selected_source_type text,
  selected_source_import_id uuid references public.property_source_imports(id) on delete set null,
  selected_field_value_id uuid references public.property_source_field_values(id) on delete set null,
  selected_canonical_value jsonb not null default '{}'::jsonb,
  selected_source_timestamp timestamptz,
  conflict_sources jsonb not null default '[]'::jsonb,
  decision_reason text,
  reviewed_by_user_id uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_property_reconciliation_status unique (property_id, field_name),
  constraint property_reconciliation_status_source_type_check check (
    selected_source_type is null
    or selected_source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_reconciliation_status_resolution_check check (
    resolution_status in ('pending', 'matched', 'conflicted', 'overridden', 'fallback', 'unresolved')
  )
);

create index if not exists idx_property_reconciliation_status_property
  on public.property_reconciliation_status (property_id, resolution_status);

create table if not exists public.property_manual_overrides (
  id uuid primary key default gen_random_uuid(),
  property_id uuid not null references public.properties(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  field_name text not null,
  override_value jsonb not null,
  override_reason text,
  override_user_id uuid not null references auth.users(id) on delete restrict,
  override_created_at timestamptz not null default now(),
  override_expires_at timestamptz,
  is_active boolean not null default true,
  superseded_by_override_id uuid references public.property_manual_overrides(id) on delete set null,
  source_context jsonb not null default '{}'::jsonb
);

create index if not exists idx_property_manual_overrides_active
  on public.property_manual_overrides (property_id, field_name, is_active);

create table if not exists public.property_evidence_records (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  property_id uuid not null references public.properties(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete set null,
  transaction_id uuid,
  source_type text not null,
  evidence_class text not null,
  file_version_id uuid references public.property_file_versions(id) on delete set null,
  storage_reference_id uuid references public.property_file_storage_references(id) on delete set null,
  source_media_id uuid references public.property_source_media(id) on delete set null,
  import_run_id uuid references public.property_import_runs(id) on delete set null,
  review_state text not null default 'received',
  verification_state text not null default 'unverified',
  client_visibility_state text not null default 'internal_only',
  is_primary boolean not null default false,
  sort_order integer,
  captured_at timestamptz,
  captured_by_user_id uuid references auth.users(id) on delete set null,
  caption text,
  description text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint property_evidence_records_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_evidence_records_class_check check (
    evidence_class in (
      'listing_photo',
      'field_photo',
      'floor_plan',
      'inspection_report',
      'construction_proposal',
      'appraisal',
      'loi',
      'contract_executed',
      'contract_amendment',
      'disclosure',
      'due_diligence_doc',
      'title_doc',
      'closing_doc',
      'correspondence',
      'client_artifact'
    )
  ),
  constraint property_evidence_records_review_state_check check (
    review_state in ('received', 'under_review', 'approved', 'rejected', 'archived')
  ),
  constraint property_evidence_records_verification_state_check check (
    verification_state in ('unverified', 'verified', 'mismatch', 'expired')
  ),
  constraint property_evidence_records_client_visibility_check check (
    client_visibility_state in ('internal_only', 'client_visible', 'client_hidden', 'client_expired')
  )
);

create index if not exists idx_property_evidence_records_property
  on public.property_evidence_records (property_id, evidence_class);
create index if not exists idx_property_evidence_records_transaction
  on public.property_evidence_records (transaction_id, evidence_class);

create table if not exists public.property_evidence_source_links (
  id uuid primary key default gen_random_uuid(),
  evidence_record_id uuid not null references public.property_evidence_records(id) on delete cascade,
  source_type text not null,
  source_import_id uuid references public.property_source_imports(id) on delete set null,
  source_field_value_id uuid references public.property_source_field_values(id) on delete set null,
  source_room_id uuid references public.property_source_rooms(id) on delete set null,
  source_media_id uuid references public.property_source_media(id) on delete set null,
  file_version_id uuid references public.property_file_versions(id) on delete set null,
  storage_reference_id uuid references public.property_file_storage_references(id) on delete set null,
  link_role text not null default 'supporting',
  created_at timestamptz not null default now(),
  constraint property_evidence_source_links_source_type_check check (
    source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_evidence_source_links_role_check check (
    link_role in ('primary', 'supporting', 'derived_from', 'exported_to')
  ),
  constraint property_evidence_source_links_target_check check (
    source_import_id is not null
    or source_field_value_id is not null
    or source_room_id is not null
    or source_media_id is not null
    or file_version_id is not null
    or storage_reference_id is not null
  )
);

create index if not exists idx_property_evidence_source_links_evidence
  on public.property_evidence_source_links (evidence_record_id, link_role);

create table if not exists public.property_transaction_document_checklists (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  property_id uuid not null references public.properties(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete set null,
  transaction_id uuid,
  checklist_key text not null,
  checklist_group text not null,
  deal_stage text,
  file_class text not null,
  required_flag boolean not null default true,
  checklist_status text not null default 'missing',
  review_state text not null default 'pending',
  latest_approved_file_version_id uuid references public.property_file_versions(id) on delete set null,
  current_checklist_item_id uuid,
  latest_received_at timestamptz,
  unresolved_missing_count integer not null default 1,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_property_transaction_document_checklists unique (property_id, transaction_id, checklist_key),
  constraint property_transaction_document_checklists_file_class_check check (
    file_class in (
      'listing_photo',
      'field_photo',
      'floor_plan',
      'inspection_report',
      'construction_proposal',
      'appraisal',
      'loi',
      'contract_executed',
      'contract_amendment',
      'disclosure',
      'due_diligence_doc',
      'title_doc',
      'closing_doc',
      'correspondence',
      'client_artifact'
    )
  ),
  constraint property_transaction_document_checklists_status_check check (
    checklist_status in ('missing', 'received', 'under_review', 'approved', 'rejected', 'waived', 'superseded')
  ),
  constraint property_transaction_document_checklists_review_check check (
    review_state in ('pending', 'under_review', 'approved', 'rejected')
  )
);

create index if not exists idx_property_transaction_document_checklists_stage
  on public.property_transaction_document_checklists (property_id, deal_stage, checklist_group);

create table if not exists public.property_transaction_checklist_items (
  id uuid primary key default gen_random_uuid(),
  checklist_id uuid not null references public.property_transaction_document_checklists(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  property_id uuid not null references public.properties(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete set null,
  transaction_id uuid,
  file_version_id uuid references public.property_file_versions(id) on delete restrict,
  storage_reference_id uuid references public.property_file_storage_references(id) on delete set null,
  evidence_record_id uuid references public.property_evidence_records(id) on delete set null,
  submission_source_type text not null,
  item_status text not null default 'received',
  review_state text not null default 'pending',
  uploaded_by_user_id uuid references auth.users(id) on delete set null,
  captured_by_user_id uuid references auth.users(id) on delete set null,
  submitted_at timestamptz not null default now(),
  reviewed_at timestamptz,
  approved_at timestamptz,
  supersedes_checklist_item_id uuid references public.property_transaction_checklist_items(id) on delete set null,
  superseded_by_checklist_item_id uuid references public.property_transaction_checklist_items(id) on delete set null,
  is_latest boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  constraint property_transaction_checklist_items_source_type_check check (
    submission_source_type in ('corelogic', 'mls', 'field', 'dropbox', 'zipforms', 'manual')
  ),
  constraint property_transaction_checklist_items_status_check check (
    item_status in ('received', 'under_review', 'approved', 'rejected', 'superseded')
  ),
  constraint property_transaction_checklist_items_review_check check (
    review_state in ('pending', 'under_review', 'approved', 'rejected', 'superseded')
  )
);

create unique index if not exists uq_property_transaction_checklist_items_latest
  on public.property_transaction_checklist_items (checklist_id)
  where is_latest = true;
create index if not exists idx_property_transaction_checklist_items_checklist
  on public.property_transaction_checklist_items (checklist_id, submitted_at desc);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'property_transaction_document_checklists_current_item_fk'
  ) then
    alter table public.property_transaction_document_checklists
      add constraint property_transaction_document_checklists_current_item_fk
      foreign key (current_checklist_item_id)
      references public.property_transaction_checklist_items(id)
      on delete set null;
  end if;
end
$$;

create table if not exists public.property_client_visible_artifacts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  property_id uuid not null references public.properties(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete set null,
  transaction_id uuid,
  file_version_id uuid not null references public.property_file_versions(id) on delete cascade,
  storage_reference_id uuid not null references public.property_file_storage_references(id) on delete restrict,
  evidence_record_id uuid references public.property_evidence_records(id) on delete set null,
  visibility_state text not null default 'client_hidden',
  share_token text,
  share_url text,
  expires_at timestamptz,
  last_accessed_at timestamptz,
  created_by_user_id uuid references auth.users(id) on delete set null,
  access_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint property_client_visible_artifacts_visibility_check check (
    visibility_state in ('client_hidden', 'client_visible', 'client_revoked', 'client_expired')
  )
);

create unique index if not exists uq_property_client_visible_artifacts_active
  on public.property_client_visible_artifacts (file_version_id)
  where visibility_state = 'client_visible';
create index if not exists idx_property_client_visible_artifacts_property
  on public.property_client_visible_artifacts (property_id, visibility_state);

do $$
begin
  if exists (
    select 1
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and p.proname = '_touch_updated_at'
  ) then
    execute 'drop trigger if exists trg_properties_touch on public.properties';
    execute 'create trigger trg_properties_touch before update on public.properties for each row execute function public._touch_updated_at()';

    execute 'drop trigger if exists trg_property_reconciliation_status_touch on public.property_reconciliation_status';
    execute 'create trigger trg_property_reconciliation_status_touch before update on public.property_reconciliation_status for each row execute function public._touch_updated_at()';

    execute 'drop trigger if exists trg_property_transaction_document_checklists_touch on public.property_transaction_document_checklists';
    execute 'create trigger trg_property_transaction_document_checklists_touch before update on public.property_transaction_document_checklists for each row execute function public._touch_updated_at()';
  end if;
end
$$;

commit;
