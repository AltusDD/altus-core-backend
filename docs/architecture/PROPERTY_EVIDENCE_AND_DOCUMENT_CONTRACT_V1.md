# PROPERTY EVIDENCE AND DOCUMENT CONTRACT V1

Status: Proposed backend contract baseline
Owner: core lane
Last Updated: 2026-03-21

## Purpose

Define the canonical backend-side operating contract for property evidence, media, and transaction document workflows across these evidence lanes:

1. MLS imported data and MLS media
2. CoreLogic imported data and source snapshots
3. field-captured media and field evidence
4. Dropbox-resident operational file storage
5. ZipForms-originated transaction document packets once returned and filed

This contract extends the canonical property reconciliation layer and keeps evidence, files, checklist state, and client-visible artifacts database-first.

## Authority Rule

The source-of-truth order is:

1. database
2. API fallback
3. calculation last

Additional operating rules:

- raw source snapshots remain durable
- canonical records do not overwrite raw source evidence
- Dropbox is a storage and file-workflow surface, not canonical data authority
- ZipForms is external document origination, not canonical data authority
- missing required files must be represented as system state, not operator memory

## Exact Entities / Objects Proposed

### 1. `property_evidence_records`

Unified evidence/document root record for anything file-backed or evidence-backed.

Required fields:

- `property_evidence_id`
- `organization_id`
- `property_id`
- `asset_id`
- `deal_id`
- `transaction_id`
- `source_type`
- `source_record_id`
- `source_import_id`
- `document_class`
- `evidence_domain`
- `evidence_kind`
- `title`
- `description`
- `file_name`
- `mime_type`
- `file_size`
- `checksum_hash`
- `provider_timestamp`
- `observed_at`
- `created_at`
- `captured_by_user_id`
- `storage_provider`
- `storage_pointer`
- `storage_container`
- `storage_version`
- `visibility_scope`
- `verification_status`
- `review_status`
- `supersedes_evidence_id`
- `is_active`

Notes:

- this is the canonical row for evidence/document identity and workflow state
- file-backed and non-file-backed evidence can both exist, but file-backed records must include storage metadata
- supersession is first-class so newer files do not destroy earlier audit evidence

### 2. `property_evidence_source_links`

Join object for linking one evidence record to multiple upstream systems or packets.

Required fields:

- `property_evidence_source_link_id`
- `property_evidence_id`
- `source_type`
- `source_record_id`
- `source_import_id`
- `source_reference_json`
- `created_at`

Notes:

- supports evidence traced to both a source snapshot and a later filed packet
- avoids overloading one column with multi-system lineage

### 3. `property_imported_structured_data`

Domain envelope for imported non-file structured evidence snapshots.

Required fields:

- `property_structured_data_id`
- `organization_id`
- `property_id`
- `source_type`
- `source_import_id`
- `structured_domain`
- `payload_json`
- `payload_hash`
- `observed_at`
- `created_at`

Exact `structured_domain` values:

- `importedStructuredData`
- `clientVisibleArtifacts`

Notes:

- this complements `property_source_imports` from reconciliation work
- use for structured evidence derivatives that should remain durable and queryable

### 4. `property_media_assets`

Normalized media wrapper for imported media and field media.

Required fields:

- `property_media_asset_id`
- `property_evidence_id`
- `organization_id`
- `property_id`
- `source_type`
- `source_import_id`
- `media_role`
- `ordinal`
- `media_url`
- `thumbnail_url`
- `preview_url`
- `width_px`
- `height_px`
- `duration_seconds`
- `caption`
- `alt_text`
- `is_primary`
- `created_at`

Exact `media_role` values:

- `listing_media`
- `field_photo`
- `floor_plan`
- `client_shareable_artifact`
- `other`

### 5. `property_field_evidence`

Non-imported field evidence captured by users or attached manually.

Required fields:

- `property_field_evidence_id`
- `property_evidence_id`
- `captured_by_user_id`
- `capture_method`
- `capture_device_id`
- `capture_notes`
- `field_evidence_type`
- `geo_json`
- `created_at`

Exact `field_evidence_type` values:

- `field_photo`
- `field_video`
- `field_note`
- `field_measurement`
- `field_document`

### 6. `property_transaction_document_checklists`

Checklist header for a property / deal / transaction file set.

Required fields:

- `transaction_checklist_id`
- `organization_id`
- `property_id`
- `deal_id`
- `transaction_id`
- `checklist_status`
- `required_item_count`
- `received_item_count`
- `missing_item_count`
- `needs_review_item_count`
- `approved_item_count`
- `last_evaluated_at`
- `created_at`
- `updated_at`

### 7. `property_transaction_checklist_items`

Required/optional document expectation rows for determining completeness.

Required fields:

- `transaction_checklist_item_id`
- `transaction_checklist_id`
- `checklist_group`
- `document_class`
- `requirement_level`
- `document_state`
- `linked_property_evidence_id`
- `expected_source_type`
- `superseded_by_evidence_id`
- `notes`
- `created_at`
- `updated_at`

### 8. `property_client_visible_artifacts`

Normalized shareable artifact records for client / investor surfaces.

Required fields:

- `client_visible_artifact_id`
- `property_evidence_id`
- `organization_id`
- `property_id`
- `artifact_type`
- `artifact_status`
- `visibility_scope`
- `share_link_pointer`
- `expires_at`
- `revoked_at`
- `created_at`

Exact `artifact_type` values:

- `offering_package`
- `listing_sheet`
- `marketing_brochure`
- `photo_gallery`
- `deal_room_file`
- `client_shareable_artifact`

### 9. `property_file_storage_references`

Storage abstraction row for Dropbox and other object stores.

Required fields:

- `property_file_storage_reference_id`
- `property_evidence_id`
- `storage_provider`
- `storage_pointer`
- `folder_pointer`
- `provider_file_id`
- `provider_version_id`
- `provider_path_display`
- `created_at`
- `verified_at`
- `storage_status`

Notes:

- Dropbox lives here as file-workflow/storage metadata only
- this table is not the canonical authority for document meaning or completeness

## Unified Top-Level Evidence Domains

Exact `evidence_domain` values:

- `importedStructuredData`
- `importedMedia`
- `fieldEvidence`
- `transactionDocuments`
- `fileStorageReferences`
- `clientVisibleArtifacts`

## Evidence Source Types

Exact `source_type` enum:

- `MLS`
- `CORELOGIC`
- `FIELD`
- `DROPBOX`
- `ZIPFORMS`
- `MANUAL`
- `MANUAL_FILED_FROM_ZIPFORMS`

## Canonical Document / Evidence Classes

Exact `document_class` values at minimum:

- `listing_media`
- `field_photos`
- `floor_plans`
- `appraisal`
- `inspection_report`
- `construction_proposal`
- `loi`
- `purchase_agreement`
- `accepted_contract`
- `amendment`
- `counter_offer`
- `disclosures`
- `title_settlement_closing_package`
- `due_diligence_documents`
- `transaction_correspondence_packet`
- `client_shareable_artifact`

Optional additional supported classes:

- `survey`
- `insurance_document`
- `lease_document`
- `closing_statement`
- `title_commitment`
- `media_other`

## Required Metadata For Every Evidence / Document Object

Every `property_evidence_records` row must support at minimum:

- `organization_id`
- `property_id`
- `asset_id`
- `source_type`
- `source_record_id`
- `source_import_id`
- `document_class`
- `file_name`
- `mime_type`
- `file_size`
- `created_at`
- `observed_at`
- `captured_by_user_id`
- `provider_timestamp`
- `storage_provider`
- `storage_pointer`
- `checksum_hash`
- `visibility_scope`
- `verification_status`
- `review_status`

## Evidence / Document Status Model

### Verification Status

Exact `verification_status` enum:

- `unverified`
- `received`
- `needs_review`
- `approved`
- `rejected`
- `superseded`
- `missing`

### Review Status

Exact `review_status` enum:

- `not_started`
- `in_review`
- `approved`
- `rejected`
- `superseded`

### Requirement Level

Exact `requirement_level` enum:

- `required`
- `optional`

### Document State

Exact `document_state` enum:

- `missing`
- `received`
- `needs_review`
- `approved`
- `rejected`
- `superseded`

### Visibility Flags

The operating contract must support these file-state predicates:

- `client_visible`
- `internal_only`

These are represented through `visibility_scope` rather than a separate boolean matrix.

## Document Checklist Model

Checklist groups required in V1:

- `LOI`
- `executed_purchase_agreement`
- `amendments_counters`
- `disclosures`
- `construction_proposal`
- `appraisal`
- `due_diligence_packet`
- `title_settlement_documents`
- `closing_documents`
- `marketing_property_media`

Checklist behavior:

- one checklist header per property / deal / transaction context
- one or more checklist items per required or optional class
- completeness is computed from persisted item state, not inferred in UI
- a missing required document is a first-class persisted state
- a newly received document can supersede the prior linked document while preserving history

Checklist status:

Exact `checklist_status` enum:

- `complete`
- `incomplete`
- `needs_review`
- `blocked`

## ZipForms Representation Contract

ZipForms-returned documents must be represented as durable evidence records with:

- `source_type = ZIPFORMS` when the document remains directly attributable to ZipForms output
- `source_type = MANUAL_FILED_FROM_ZIPFORMS` when a user or process files the returned document into Altus-controlled storage
- linked `deal_id`
- linked `property_id`
- linked `transaction_id`
- checklist item linkage for required-file detection
- `supersedes_evidence_id` support for newer signed packets or amended versions

ZipForms packets are origination evidence only. They never become canonical property-data authority.

## Visibility / Access Model

Exact `visibility_scope` enum:

- `internal_team_only`
- `agent_team`
- `client_visible`
- `investor_visible`
- `restricted_legal_accounting`
- `expiring_share`
- `revoked`

Visibility rules:

- `internal_team_only` is the default for unreviewed operational files
- `client_visible` and `investor_visible` require an approved or explicitly shareable artifact state
- `expiring_share` must support `expires_at`
- revoked access must support `revoked_at`

## Canonical Cockpit / Deal-Room Payload Shape

```json
{
  "propertyId": "prop_123",
  "dealId": "deal_123",
  "transactionId": "txn_123",
  "sourceHeaderSummary": {
    "structuredSources": [
      {
        "sourceType": "MLS",
        "latestSourceImportId": "src_mls_001",
        "observedAt": "2026-03-21T13:58:00Z",
        "freshnessStatus": "fresh"
      },
      {
        "sourceType": "CORELOGIC",
        "latestSourceImportId": "src_corelogic_001",
        "observedAt": "2026-03-20T22:10:00Z",
        "freshnessStatus": "aging"
      }
    ],
    "evidenceSources": [
      "MLS",
      "CORELOGIC",
      "FIELD",
      "DROPBOX",
      "ZIPFORMS"
    ]
  },
  "reconciliationSummary": {
    "reconciliationStatus": "conflicting",
    "unresolvedConflictCount": 2,
    "activeManualOverrideCount": 1,
    "lastReconciledAt": "2026-03-21T15:00:00Z"
  },
  "evidenceMediaSummary": {
    "importedStructuredData": {
      "latestMlsSnapshotId": "src_mls_001",
      "latestCorelogicSnapshotId": "src_corelogic_001"
    },
    "importedMedia": {
      "listingMediaCount": 36,
      "hasPrimaryPhoto": true
    },
    "fieldEvidence": {
      "fieldPhotoCount": 18,
      "fieldDocumentCount": 4,
      "lastCapturedAt": "2026-03-21T12:45:00Z"
    },
    "fileStorageReferences": {
      "dropboxFileCount": 22,
      "verifiedReferenceCount": 22
    }
  },
  "transactionDocumentChecklistSummary": {
    "checklistStatus": "incomplete",
    "requiredItemCount": 10,
    "receivedItemCount": 7,
    "missingItemCount": 2,
    "needsReviewItemCount": 1,
    "groups": [
      {
        "checklistGroup": "executed_purchase_agreement",
        "documentState": "received",
        "linkedEvidenceId": "evid_2001"
      },
      {
        "checklistGroup": "title_settlement_documents",
        "documentState": "missing",
        "linkedEvidenceId": null
      }
    ]
  },
  "clientVisibleFileSummary": {
    "clientVisibleCount": 4,
    "investorVisibleCount": 2,
    "expiringShareCount": 1,
    "artifacts": [
      {
        "propertyEvidenceId": "evid_5001",
        "documentClass": "client_shareable_artifact",
        "artifactType": "offering_package",
        "visibilityScope": "client_visible",
        "artifactStatus": "approved",
        "expiresAt": null
      }
    ]
  }
}
```

## Operating Notes

- `importedStructuredData` maps to source snapshots and structured derivatives, never to Dropbox pointers
- `importedMedia` and `fieldEvidence` remain durable evidence rows with file metadata and storage references
- `transactionDocuments` drive checklist completeness and supersession state
- `fileStorageReferences` are attachment/storage facts, not source-of-truth property meaning
- `clientVisibleArtifacts` are explicit derived or approved outward-facing evidence records, not inferred from any file in storage
