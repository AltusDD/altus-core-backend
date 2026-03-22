\pset format aligned
\pset tuples_only off

select
  'migration_0005_tables_present' as check_name,
  (
    to_regclass('public.properties') is not null
    and to_regclass('public.property_import_runs') is not null
    and to_regclass('public.property_source_imports') is not null
    and to_regclass('public.property_source_field_values') is not null
    and to_regclass('public.property_source_rooms') is not null
    and to_regclass('public.property_source_media') is not null
    and to_regclass('public.property_reconciliation_status') is not null
    and to_regclass('public.property_manual_overrides') is not null
    and to_regclass('public.property_evidence_records') is not null
    and to_regclass('public.property_evidence_source_links') is not null
    and to_regclass('public.property_transaction_document_checklists') is not null
    and to_regclass('public.property_transaction_checklist_items') is not null
    and to_regclass('public.property_file_storage_references') is not null
    and to_regclass('public.property_client_visible_artifacts') is not null
  ) as passed;

select
  'migration_history_entries' as check_name,
  version
from supabase_migrations.schema_migrations
where version in ('0005', '0006')
order by version;

select 'row_count.properties' as metric, count(*) as row_count
from public.properties
where property_key = 'cockpit-seed-property-v1'
union all
select 'row_count.property_import_runs', count(*)
from public.property_import_runs
where provider_name = 'seed_loader'
union all
select 'row_count.property_source_imports', count(*)
from public.property_source_imports
where provider_record_key = 'MLS:SEED:001'
union all
select 'row_count.property_source_field_values', count(*)
from public.property_source_field_values
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_reconciliation_status', count(*)
from public.property_reconciliation_status
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_evidence_records', count(*)
from public.property_evidence_records
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_transaction_document_checklists', count(*)
from public.property_transaction_document_checklists
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_transaction_checklist_items', count(*)
from public.property_transaction_checklist_items
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_file_storage_references', count(*)
from public.property_file_storage_references
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_file_versions', count(*)
from public.property_file_versions
where property_id = '11111111-1111-4111-8111-111111111111'
union all
select 'row_count.property_client_visible_artifacts', count(*)
from public.property_client_visible_artifacts
where property_id = '11111111-1111-4111-8111-111111111111'
order by metric;

select
  'fk_integrity.property_source_imports_to_runs' as check_name,
  count(*) as broken_rows
from public.property_source_imports psi
left join public.property_import_runs pir on pir.id = psi.import_run_id
where psi.property_id = '11111111-1111-4111-8111-111111111111'
  and pir.id is null
union all
select
  'fk_integrity.field_values_to_source_imports',
  count(*)
from public.property_source_field_values psfv
left join public.property_source_imports psi on psi.id = psfv.source_import_id
where psfv.property_id = '11111111-1111-4111-8111-111111111111'
  and psi.id is null
union all
select
  'fk_integrity.reconciliation_to_field_values',
  count(*)
from public.property_reconciliation_status prs
left join public.property_source_field_values psfv on psfv.id = prs.selected_field_value_id
where prs.property_id = '11111111-1111-4111-8111-111111111111'
  and prs.selected_field_value_id is not null
  and psfv.id is null
union all
select
  'fk_integrity.evidence_to_file_versions',
  count(*)
from public.property_evidence_records per
left join public.property_file_versions pfv on pfv.id = per.file_version_id
where per.property_id = '11111111-1111-4111-8111-111111111111'
  and per.file_version_id is not null
  and pfv.id is null
union all
select
  'fk_integrity.checklist_items_to_checklists',
  count(*)
from public.property_transaction_checklist_items ptci
left join public.property_transaction_document_checklists ptdc on ptdc.id = ptci.checklist_id
where ptci.property_id = '11111111-1111-4111-8111-111111111111'
  and ptdc.id is null
union all
select
  'fk_integrity.client_visible_to_file_versions',
  count(*)
from public.property_client_visible_artifacts pcva
left join public.property_file_versions pfv on pfv.id = pcva.file_version_id
where pcva.property_id = '11111111-1111-4111-8111-111111111111'
  and pfv.id is null
order by check_name;

select
  p.id,
  p.property_key,
  p.status,
  p.canonical_address,
  p.canonical_property_type,
  p.canonical_valuation,
  p.canonical_document_state
from public.properties p
where p.id = '11111111-1111-4111-8111-111111111111';

select
  prs.field_name,
  prs.resolution_status,
  prs.selected_source_type,
  prs.selected_canonical_value,
  psfv.normalized_value as source_normalized_value
from public.property_reconciliation_status prs
left join public.property_source_field_values psfv on psfv.id = prs.selected_field_value_id
where prs.property_id = '11111111-1111-4111-8111-111111111111'
order by prs.field_name;

select
  per.evidence_class,
  per.review_state,
  per.client_visibility_state,
  pfsr.storage_provider,
  pfsr.storage_path,
  pfv.file_class,
  pfv.is_approved
from public.property_evidence_records per
left join public.property_file_versions pfv on pfv.id = per.file_version_id
left join public.property_file_storage_references pfsr on pfsr.id = per.storage_reference_id
where per.property_id = '11111111-1111-4111-8111-111111111111'
order by per.evidence_class;

select
  ptdc.checklist_key,
  ptdc.checklist_status,
  ptdc.review_state,
  ptdc.unresolved_missing_count,
  ptci.item_status,
  ptci.review_state as item_review_state,
  pfv.file_class,
  pfv.is_approved
from public.property_transaction_document_checklists ptdc
left join public.property_transaction_checklist_items ptci on ptci.id = ptdc.current_checklist_item_id
left join public.property_file_versions pfv on pfv.id = ptci.file_version_id
where ptdc.property_id = '11111111-1111-4111-8111-111111111111';
