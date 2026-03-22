begin;

do $$
declare
  v_property_id constant uuid := '11111111-1111-4111-8111-111111111111';
  v_import_run_id constant uuid := '22222222-2222-4222-8222-222222222222';
  v_source_import_id constant uuid := '33333333-3333-4333-8333-333333333333';
  v_address_field_id constant uuid := '44444444-4444-4444-8444-444444444441';
  v_type_field_id constant uuid := '44444444-4444-4444-8444-444444444442';
  v_value_field_id constant uuid := '44444444-4444-4444-8444-444444444443';
  v_media_storage_ref_id constant uuid := '55555555-5555-4555-8555-555555555551';
  v_report_storage_ref_id constant uuid := '55555555-5555-4555-8555-555555555552';
  v_media_file_version_id constant uuid := '66666666-6666-4666-8666-666666666661';
  v_report_file_version_id constant uuid := '66666666-6666-4666-8666-666666666662';
  v_source_media_id constant uuid := '77777777-7777-4777-8777-777777777771';
  v_address_recon_id constant uuid := '88888888-8888-4888-8888-888888888881';
  v_type_recon_id constant uuid := '88888888-8888-4888-8888-888888888882';
  v_value_recon_id constant uuid := '88888888-8888-4888-8888-888888888883';
  v_evidence_media_id constant uuid := '99999999-9999-4999-8999-999999999991';
  v_evidence_report_id constant uuid := '99999999-9999-4999-8999-999999999992';
  v_evidence_link_media_id constant uuid := 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1';
  v_evidence_link_report_id constant uuid := 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2';
  v_checklist_id constant uuid := 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
  v_checklist_item_id constant uuid := 'cccccccc-cccc-4ccc-8ccc-ccccccccccc1';
  v_client_visible_artifact_id constant uuid := 'dddddddd-dddd-4ddd-8ddd-ddddddddddd1';
  v_transaction_id constant uuid := 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeee1';
begin
  insert into public.properties (
    id,
    property_key,
    status,
    canonical_address,
    canonical_apn,
    canonical_sqft,
    canonical_property_type,
    canonical_valuation,
    canonical_source_summary,
    canonical_listing_lifecycle,
    canonical_document_state,
    last_reconciled_at,
    last_imported_at
  )
  values (
    v_property_id,
    'cockpit-seed-property-v1',
    'active',
    jsonb_build_object(
      'line1', '123 Seed Lane',
      'city', 'Dallas',
      'state', 'TX',
      'postal_code', '75201'
    ),
    'SEED-APN-001',
    1850,
    'single_family',
    jsonb_build_object(
      'avm', 485000,
      'valuation_date', '2026-03-22'
    ),
    jsonb_build_object(
      'preferred_source', 'mls',
      'available_sources', jsonb_build_array('mls', 'manual')
    ),
    jsonb_build_object(
      'listing_status', 'active',
      'days_on_market', 12
    ),
    jsonb_build_object(
      'checklists', jsonb_build_array(
        jsonb_build_object(
          'checklist_key', 'due-diligence-inspection-report',
          'status', 'received',
          'unresolved_missing_count', 1
        )
      )
    ),
    now(),
    now()
  )
  on conflict (id) do update
  set
    property_key = excluded.property_key,
    status = excluded.status,
    canonical_address = excluded.canonical_address,
    canonical_apn = excluded.canonical_apn,
    canonical_sqft = excluded.canonical_sqft,
    canonical_property_type = excluded.canonical_property_type,
    canonical_valuation = excluded.canonical_valuation,
    canonical_source_summary = excluded.canonical_source_summary,
    canonical_listing_lifecycle = excluded.canonical_listing_lifecycle,
    canonical_document_state = excluded.canonical_document_state,
    last_reconciled_at = excluded.last_reconciled_at,
    last_imported_at = excluded.last_imported_at;

  insert into public.property_import_runs (
    id,
    source_type,
    provider_name,
    run_status,
    trigger_type,
    source_started_at,
    source_completed_at,
    source_snapshot_at,
    record_count,
    success_count,
    error_count,
    metadata
  )
  values (
    v_import_run_id,
    'mls',
    'seed_loader',
    'completed',
    'manual',
    now() - interval '5 minutes',
    now() - interval '4 minutes',
    now() - interval '1 hour',
    1,
    1,
    0,
    jsonb_build_object('seed', true, 'purpose', 'cockpit_minimal')
  )
  on conflict (id) do update
  set
    run_status = excluded.run_status,
    source_snapshot_at = excluded.source_snapshot_at,
    record_count = excluded.record_count,
    success_count = excluded.success_count,
    error_count = excluded.error_count,
    metadata = excluded.metadata;

  update public.property_source_imports
  set is_latest = false
  where property_id = v_property_id
    and source_type = 'mls'
    and id <> v_source_import_id;

  insert into public.property_source_imports (
    id,
    property_id,
    import_run_id,
    source_type,
    provider_record_id,
    provider_record_key,
    source_record_version,
    source_timestamp,
    source_effective_at,
    listing_timestamp,
    listing_status,
    listing_event,
    source_path,
    source_locator,
    is_latest,
    raw_payload,
    raw_payload_hash
  )
  values (
    v_source_import_id,
    v_property_id,
    v_import_run_id,
    'mls',
    'MLS-SEED-001',
    'MLS:SEED:001',
    'v1',
    now() - interval '1 hour',
    now() - interval '1 hour',
    now() - interval '1 hour',
    'active',
    jsonb_build_object('event', 'listing_imported'),
    '/imports/mls/cockpit-seed-property-v1.json',
    jsonb_build_object('provider', 'mls', 'record_key', 'MLS:SEED:001'),
    true,
    jsonb_build_object(
      'address', '123 Seed Lane',
      'property_type', 'single_family',
      'valuation', jsonb_build_object('avm', 485000)
    ),
    'seed-mls-payload-hash-v1'
  )
  on conflict (id) do update
  set
    import_run_id = excluded.import_run_id,
    listing_status = excluded.listing_status,
    listing_event = excluded.listing_event,
    source_locator = excluded.source_locator,
    is_latest = excluded.is_latest,
    raw_payload = excluded.raw_payload,
    raw_payload_hash = excluded.raw_payload_hash;

  insert into public.property_source_field_values (
    id,
    property_id,
    source_import_id,
    field_name,
    value_text,
    normalized_value,
    source_timestamp
  )
  values
    (
      v_address_field_id,
      v_property_id,
      v_source_import_id,
      'address',
      '123 Seed Lane, Dallas, TX 75201',
      jsonb_build_object(
        'line1', '123 Seed Lane',
        'city', 'Dallas',
        'state', 'TX',
        'postal_code', '75201'
      ),
      now() - interval '1 hour'
    ),
    (
      v_type_field_id,
      v_property_id,
      v_source_import_id,
      'property_type',
      'single_family',
      jsonb_build_object('value', 'single_family'),
      now() - interval '1 hour'
    ),
    (
      v_value_field_id,
      v_property_id,
      v_source_import_id,
      'valuation',
      null,
      jsonb_build_object('avm', 485000, 'currency', 'USD'),
      now() - interval '1 hour'
    )
  on conflict (id) do update
  set
    value_text = excluded.value_text,
    normalized_value = excluded.normalized_value,
    source_timestamp = excluded.source_timestamp;

  insert into public.property_reconciliation_status (
    id,
    property_id,
    field_name,
    resolution_status,
    conflict_flag,
    override_flag,
    selected_source_type,
    selected_source_import_id,
    selected_field_value_id,
    selected_canonical_value,
    selected_source_timestamp,
    conflict_sources,
    decision_reason,
    reviewed_at
  )
  values
    (
      v_address_recon_id,
      v_property_id,
      'address',
      'matched',
      false,
      false,
      'mls',
      v_source_import_id,
      v_address_field_id,
      jsonb_build_object(
        'line1', '123 Seed Lane',
        'city', 'Dallas',
        'state', 'TX',
        'postal_code', '75201'
      ),
      now() - interval '1 hour',
      '[]'::jsonb,
      'seed canonical address from MLS import',
      now()
    ),
    (
      v_type_recon_id,
      v_property_id,
      'property_type',
      'matched',
      false,
      false,
      'mls',
      v_source_import_id,
      v_type_field_id,
      jsonb_build_object('value', 'single_family'),
      now() - interval '1 hour',
      '[]'::jsonb,
      'seed canonical property type from MLS import',
      now()
    ),
    (
      v_value_recon_id,
      v_property_id,
      'valuation',
      'fallback',
      false,
      false,
      'mls',
      v_source_import_id,
      v_value_field_id,
      jsonb_build_object('avm', 485000, 'currency', 'USD'),
      now() - interval '1 hour',
      '[]'::jsonb,
      'seed valuation fallback from MLS AVM',
      now()
    )
  on conflict (id) do update
  set
    resolution_status = excluded.resolution_status,
    selected_source_type = excluded.selected_source_type,
    selected_source_import_id = excluded.selected_source_import_id,
    selected_field_value_id = excluded.selected_field_value_id,
    selected_canonical_value = excluded.selected_canonical_value,
    selected_source_timestamp = excluded.selected_source_timestamp,
    decision_reason = excluded.decision_reason,
    reviewed_at = excluded.reviewed_at;

  insert into public.property_file_storage_references (
    id,
    property_id,
    transaction_id,
    storage_provider,
    storage_bucket,
    storage_path,
    canonical_pointer,
    file_name,
    mime_type,
    byte_size,
    checksum_sha256,
    captured_from_source_type,
    source_import_id,
    import_run_id,
    fetched_at,
    last_verified_at
  )
  values
    (
      v_media_storage_ref_id,
      v_property_id,
      v_transaction_id,
      'dropbox',
      null,
      '/Altus/Seed Property/listing-photo-1.jpg',
      jsonb_build_object('provider', 'dropbox', 'path', '/Altus/Seed Property/listing-photo-1.jpg'),
      'listing-photo-1.jpg',
      'image/jpeg',
      245760,
      'seed-photo-sha256-v1',
      'dropbox',
      v_source_import_id,
      v_import_run_id,
      now() - interval '30 minutes',
      now() - interval '30 minutes'
    ),
    (
      v_report_storage_ref_id,
      v_property_id,
      v_transaction_id,
      'zipforms',
      null,
      '/zipforms/seed/inspection-report.pdf',
      jsonb_build_object('provider', 'zipforms', 'path', '/zipforms/seed/inspection-report.pdf'),
      'inspection-report.pdf',
      'application/pdf',
      512000,
      'seed-report-sha256-v1',
      'zipforms',
      v_source_import_id,
      v_import_run_id,
      now() - interval '20 minutes',
      now() - interval '20 minutes'
    )
  on conflict (id) do update
  set
    storage_path = excluded.storage_path,
    canonical_pointer = excluded.canonical_pointer,
    checksum_sha256 = excluded.checksum_sha256,
    last_verified_at = excluded.last_verified_at;

  update public.property_file_versions
  set is_latest = false
  where property_id = v_property_id
    and file_class in ('listing_photo', 'inspection_report')
    and id not in (v_media_file_version_id, v_report_file_version_id);

  insert into public.property_file_versions (
    id,
    property_id,
    transaction_id,
    storage_reference_id,
    file_class,
    version_number,
    version_label,
    review_state,
    verification_state,
    is_latest,
    is_approved,
    client_visibility_state,
    source_type,
    source_import_id,
    import_run_id,
    version_metadata
  )
  values
    (
      v_media_file_version_id,
      v_property_id,
      v_transaction_id,
      v_media_storage_ref_id,
      'listing_photo',
      1,
      'seed-photo-v1',
      'approved',
      'verified',
      true,
      true,
      'client_visible',
      'dropbox',
      v_source_import_id,
      v_import_run_id,
      jsonb_build_object('seed', true)
    ),
    (
      v_report_file_version_id,
      v_property_id,
      v_transaction_id,
      v_report_storage_ref_id,
      'inspection_report',
      1,
      'seed-inspection-v1',
      'under_review',
      'verified',
      true,
      false,
      'internal_only',
      'zipforms',
      v_source_import_id,
      v_import_run_id,
      jsonb_build_object('seed', true)
    )
  on conflict (id) do update
  set
    review_state = excluded.review_state,
    verification_state = excluded.verification_state,
    is_latest = excluded.is_latest,
    is_approved = excluded.is_approved,
    client_visibility_state = excluded.client_visibility_state,
    version_metadata = excluded.version_metadata;

  insert into public.property_source_media (
    id,
    property_id,
    source_import_id,
    source_type,
    provider_media_key,
    storage_reference_id,
    file_version_id,
    storage_pointer,
    sort_order,
    media_type,
    caption,
    description,
    mime_type,
    width_px,
    height_px,
    fetched_at,
    source_timestamp,
    is_primary
  )
  values (
    v_source_media_id,
    v_property_id,
    v_source_import_id,
    'dropbox',
    'dropbox:listing-photo-1',
    v_media_storage_ref_id,
    v_media_file_version_id,
    '/Altus/Seed Property/listing-photo-1.jpg',
    1,
    'image',
    'Front exterior',
    'Seed cockpit listing photo',
    'image/jpeg',
    1280,
    720,
    now() - interval '30 minutes',
    now() - interval '1 hour',
    true
  )
  on conflict (id) do update
  set
    storage_reference_id = excluded.storage_reference_id,
    file_version_id = excluded.file_version_id,
    storage_pointer = excluded.storage_pointer,
    caption = excluded.caption,
    description = excluded.description,
    is_primary = excluded.is_primary;

  insert into public.property_evidence_records (
    id,
    property_id,
    transaction_id,
    source_type,
    evidence_class,
    file_version_id,
    storage_reference_id,
    source_media_id,
    import_run_id,
    review_state,
    verification_state,
    client_visibility_state,
    is_primary,
    sort_order,
    captured_at,
    caption,
    description,
    metadata
  )
  values
    (
      v_evidence_media_id,
      v_property_id,
      v_transaction_id,
      'dropbox',
      'listing_photo',
      v_media_file_version_id,
      v_media_storage_ref_id,
      v_source_media_id,
      v_import_run_id,
      'approved',
      'verified',
      'client_visible',
      true,
      1,
      now() - interval '30 minutes',
      'Front exterior',
      'Seed listing photo evidence',
      jsonb_build_object('seed', true)
    ),
    (
      v_evidence_report_id,
      v_property_id,
      v_transaction_id,
      'zipforms',
      'inspection_report',
      v_report_file_version_id,
      v_report_storage_ref_id,
      null,
      v_import_run_id,
      'under_review',
      'verified',
      'internal_only',
      false,
      2,
      now() - interval '20 minutes',
      'Inspection report',
      'Seed due diligence report',
      jsonb_build_object('seed', true)
    )
  on conflict (id) do update
  set
    review_state = excluded.review_state,
    verification_state = excluded.verification_state,
    client_visibility_state = excluded.client_visibility_state,
    caption = excluded.caption,
    description = excluded.description,
    metadata = excluded.metadata;

  insert into public.property_evidence_source_links (
    id,
    evidence_record_id,
    source_type,
    source_import_id,
    source_media_id,
    file_version_id,
    storage_reference_id,
    link_role
  )
  values
    (
      v_evidence_link_media_id,
      v_evidence_media_id,
      'dropbox',
      v_source_import_id,
      v_source_media_id,
      v_media_file_version_id,
      v_media_storage_ref_id,
      'primary'
    ),
    (
      v_evidence_link_report_id,
      v_evidence_report_id,
      'zipforms',
      v_source_import_id,
      null,
      v_report_file_version_id,
      v_report_storage_ref_id,
      'primary'
    )
  on conflict (id) do update
  set
    file_version_id = excluded.file_version_id,
    storage_reference_id = excluded.storage_reference_id,
    link_role = excluded.link_role;

  insert into public.property_transaction_document_checklists (
    id,
    property_id,
    transaction_id,
    checklist_key,
    checklist_group,
    deal_stage,
    file_class,
    required_flag,
    checklist_status,
    review_state,
    latest_approved_file_version_id,
    latest_received_at,
    unresolved_missing_count,
    notes
  )
  values (
    v_checklist_id,
    v_property_id,
    v_transaction_id,
    'due-diligence-inspection-report',
    'due_diligence',
    'under_contract',
    'inspection_report',
    true,
    'received',
    'under_review',
    null,
    now() - interval '20 minutes',
    1,
    'Seed partial checklist with report received but not yet approved'
  )
  on conflict (id) do update
  set
    checklist_status = excluded.checklist_status,
    review_state = excluded.review_state,
    latest_received_at = excluded.latest_received_at,
    unresolved_missing_count = excluded.unresolved_missing_count,
    notes = excluded.notes;

  insert into public.property_transaction_checklist_items (
    id,
    checklist_id,
    property_id,
    transaction_id,
    file_version_id,
    storage_reference_id,
    evidence_record_id,
    submission_source_type,
    item_status,
    review_state,
    submitted_at,
    is_latest,
    notes
  )
  values (
    v_checklist_item_id,
    v_checklist_id,
    v_property_id,
    v_transaction_id,
    v_report_file_version_id,
    v_report_storage_ref_id,
    v_evidence_report_id,
    'zipforms',
    'received',
    'under_review',
    now() - interval '20 minutes',
    true,
    'Seed checklist item pending approval'
  )
  on conflict (id) do update
  set
    item_status = excluded.item_status,
    review_state = excluded.review_state,
    notes = excluded.notes;

  update public.property_transaction_document_checklists
  set current_checklist_item_id = v_checklist_item_id
  where id = v_checklist_id;

  insert into public.property_client_visible_artifacts (
    id,
    property_id,
    transaction_id,
    file_version_id,
    storage_reference_id,
    evidence_record_id,
    visibility_state,
    share_token,
    share_url,
    expires_at,
    access_metadata
  )
  values (
    v_client_visible_artifact_id,
    v_property_id,
    v_transaction_id,
    v_media_file_version_id,
    v_media_storage_ref_id,
    v_evidence_media_id,
    'client_visible',
    'seed-client-photo-token',
    'https://example.invalid/client/seed-photo',
    now() + interval '30 days',
    jsonb_build_object('seed', true)
  )
  on conflict (id) do update
  set
    visibility_state = excluded.visibility_state,
    share_url = excluded.share_url,
    expires_at = excluded.expires_at,
    access_metadata = excluded.access_metadata;
end
$$;

commit;
