# CANONICAL PROPERTY RECONCILIATION CONTRACT V1

Status: Proposed backend contract baseline
Owner: core lane
Last Updated: 2026-03-21

## Purpose

Define the backend-side canonical property model for underwriting and cockpit workflows when property facts arrive from competing sources:

- CoreLogic
- MLS
- manual analyst override

This contract is implementation-ready and intentionally backend-first.

## Authority Rule

The source-of-truth order for underwriting property data is:

1. database
2. API fallback
3. calculation last

The database persists raw imports, normalized field observations, canonical resolutions, manual overrides, and unresolved conflicts. UI consumers must read the canonical database-backed contract instead of inventing local merge rules.

## Exact Entities / Objects Proposed

### 1. `properties`

Root canonical property record for underwriting use.

Required fields:

- `property_id`
- `org_id`
- `canonical_address`
- `canonical_apn`
- `canonical_beds`
- `canonical_baths`
- `canonical_sqft`
- `canonical_lot_size_sqft`
- `canonical_year_built`
- `canonical_property_type`
- `canonical_unit_count`
- `canonical_rent_indicators_json`
- `canonical_valuation_json`
- `canonical_tax_metadata_json`
- `canonical_source_summary_json`
- `freshness_summary_json`
- `reconciliation_status`
- `unresolved_conflict_count`
- `active_manual_override_count`
- `last_reconciled_at`
- `created_at`
- `updated_at`

Notes:

- This table holds the current canonical answer only.
- Every canonical field must be explainable by a resolution record.
- `canonical_source_summary_json` stores selected source by field.

### 2. `property_source_imports`

Immutable raw ingest record per provider payload.

Required fields:

- `source_import_id`
- `property_id`
- `org_id`
- `source_type`
- `source_record_id`
- `source_version`
- `payload_json`
- `payload_hash`
- `import_status`
- `fetched_at`
- `source_observed_at`
- `ingested_at`

Exact `source_type` enum:

- `CORELOGIC`
- `MLS`

Notes:

- One row per imported payload snapshot.
- `payload_json` remains immutable.
- `source_observed_at` captures provider-side record freshness when available.
- `fetched_at` captures Altus retrieval time.

### 3. `property_field_observations`

Normalized field-level extraction from a source import.

Required fields:

- `field_observation_id`
- `property_id`
- `source_import_id`
- `source_type`
- `field_key`
- `raw_value_json`
- `normalized_value_json`
- `normalized_display_value`
- `value_hash`
- `observed_at`
- `is_null_value`
- `normalization_status`

Exact `field_key` values in V1:

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
- `valuation_avm`
- `tax_metadata`

Notes:

- This object is the audit bridge from raw provider payload to field-level reconciliation.
- `normalized_value_json` is the comparison payload used by the resolver.

### 4. `property_manual_overrides`

Manual analyst override layer above imported sources.

Required fields:

- `manual_override_id`
- `property_id`
- `org_id`
- `field_key`
- `override_value_json`
- `override_display_value`
- `reason_code`
- `reason_note`
- `created_by_user_id`
- `created_at`
- `effective_at`
- `expires_at`
- `is_active`

Exact `reason_code` values in V1:

- `analyst_verified_document`
- `servicer_statement`
- `title_commitment`
- `lease_roll`
- `operator_judgment`
- `other`

Notes:

- Manual override always wins canonical selection while `is_active = true`.
- Overrides are field-level, not payload-level.
- Expiration is supported so temporary corrections do not become hidden permanent truth.

### 5. `property_field_resolutions`

Current selected answer and decision metadata for each canonical field.

Required fields:

- `field_resolution_id`
- `property_id`
- `field_key`
- `resolution_status`
- `selected_source_type`
- `selected_source_import_id`
- `selected_manual_override_id`
- `canonical_value_json`
- `canonical_display_value`
- `resolution_reason_code`
- `conflict_state`
- `source_count_present`
- `last_resolved_at`

Exact `selected_source_type` enum:

- `CORELOGIC`
- `MLS`
- `MANUAL`
- `NONE`

### 6. `property_conflicts`

Unresolved conflict record for competing non-equal source facts.

Required fields:

- `property_conflict_id`
- `property_id`
- `field_key`
- `conflict_status`
- `candidate_values_json`
- `preferred_source_type`
- `resolution_blocking`
- `created_at`
- `resolved_at`
- `resolved_by_user_id`
- `resolution_note`

Exact `conflict_status` enum:

- `open`
- `resolved`
- `suppressed`

## Exact Field Groups Proposed

### Identity Group

- `address`
- `apn`

### Physical Group

- `sqft`
- `lot_size`
- `year_built`
- `property_type`
- `unit_count`

### Unit / Occupancy Group

- `beds`
- `baths`

### Income Group

- `rent_indicators`

### Valuation Group

- `valuation_avm`

### Tax Group

- `tax_metadata`

## Reconciliation Status Model

Exact field-level `resolution_status` enum:

- `aligned`
- `conflicting`
- `manually_overridden`
- `missing_source_data`

Resolution meaning:

- `aligned`
  - canonical value exists
  - either only one non-null source exists or all present source values normalize equal
- `conflicting`
  - two or more non-null imported sources exist and normalize unequal
  - no active manual override exists
- `manually_overridden`
  - an active manual override exists for the field
- `missing_source_data`
  - no active manual override exists and no non-null imported source value is available for the field

## Override Model

Manual override precedence:

1. active manual override
2. imported source chosen by field rule
3. unresolved / missing

Manual override requirements:

- override must be field-level
- override must record actor and reason
- override must never mutate raw source payloads
- override must preserve underlying conflicting source values
- override removal must re-run canonical resolution against imported sources

## Canonical Field Resolution Rules

All rules assume normalization has already occurred in `property_field_observations`.

### `address`

Selection rule:

1. active manual override
2. CoreLogic normalized address
3. MLS normalized address

Conflict rule:

- mark `conflicting` when CoreLogic and MLS both exist and normalize unequal

### `apn`

Selection rule:

1. active manual override
2. CoreLogic APN
3. MLS APN

Conflict rule:

- mark `conflicting` when both sources exist and normalize unequal

### `beds`

Selection rule:

1. active manual override
2. MLS beds
3. CoreLogic beds

Conflict rule:

- mark `conflicting` when both exist and normalize unequal

### `baths`

Selection rule:

1. active manual override
2. MLS baths
3. CoreLogic baths

Conflict rule:

- mark `conflicting` when both exist and normalize unequal

### `sqft`

Selection rule:

1. active manual override
2. MLS living area sqft
3. CoreLogic building area sqft

Conflict rule:

- mark `conflicting` when both exist and the normalized numeric delta is greater than 5 percent

### `lot_size`

Selection rule:

1. active manual override
2. CoreLogic lot size
3. MLS lot size

Conflict rule:

- mark `conflicting` when both exist and the normalized numeric delta is greater than 5 percent

### `year_built`

Selection rule:

1. active manual override
2. CoreLogic year built
3. MLS year built

Conflict rule:

- mark `conflicting` when both exist and values differ

### `property_type`

Selection rule:

1. active manual override
2. MLS property type
3. CoreLogic property type

Conflict rule:

- mark `conflicting` when normalized class values differ

### `unit_count`

Selection rule:

1. active manual override
2. CoreLogic unit count
3. MLS unit count

Conflict rule:

- mark `conflicting` when both exist and values differ

### `rent_indicators`

Selection rule:

1. active manual override
2. MLS rent indicators
3. CoreLogic rent indicators

Expected subfields:

- `is_rental_candidate`
- `reported_rent`
- `rent_range_low`
- `rent_range_high`
- `rent_source_note`

Conflict rule:

- mark `conflicting` when either source indicates materially different rentability or rent amounts

### `valuation_avm`

Selection rule:

1. active manual override
2. CoreLogic AVM
3. MLS valuation/list-derived signal

Expected subfields:

- `amount`
- `valuation_date`
- `valuation_type`
- `confidence_band`

Conflict rule:

- mark `conflicting` when both exist and the normalized numeric delta is greater than 10 percent

### `tax_metadata`

Selection rule:

1. active manual override
2. CoreLogic tax metadata
3. MLS tax metadata

Expected subfields:

- `tax_year`
- `annual_tax_amount`
- `assessed_value`
- `tax_status`

Conflict rule:

- mark `conflicting` when overlapping subfields differ materially

## Source Freshness Tracking

Each source value surfaced to consumers must include:

- `fetchedAt`
- `sourceObservedAt`
- `ageDays`
- `freshnessStatus`

Exact `freshnessStatus` enum:

- `fresh`
- `aging`
- `stale`
- `unknown`

V1 freshness rule:

- freshness is derived from `sourceObservedAt` when present, otherwise `fetchedAt`
- the API returns freshness state, but canonical resolution does not auto-null a selected value solely for age
- stale values remain visible and may still be canonical if no better source exists

## Canonical Cockpit Payload Shape

```json
{
  "propertyId": "prop_123",
  "orgId": "org_123",
  "status": {
    "reconciliationStatus": "conflicting",
    "unresolvedConflictCount": 2,
    "activeManualOverrideCount": 1,
    "lastReconciledAt": "2026-03-21T15:00:00Z"
  },
  "fieldGroups": {
    "identity": {
      "address": {
        "status": "aligned",
        "canonical": {
          "value": {
            "line1": "123 Main St",
            "city": "Dallas",
            "state": "TX",
            "postalCode": "75001"
          },
          "displayValue": "123 Main St, Dallas, TX 75001",
          "selectedSource": "CORELOGIC",
          "selectedSourceImportId": "src_corelogic_001",
          "selectedManualOverrideId": null
        },
        "sources": {
          "CORELOGIC": {
            "value": {
              "line1": "123 Main St",
              "city": "Dallas",
              "state": "TX",
              "postalCode": "75001"
            },
            "displayValue": "123 Main St, Dallas, TX 75001",
            "fetchedAt": "2026-03-20T10:00:00Z",
            "sourceObservedAt": "2026-03-19T00:00:00Z",
            "ageDays": 2,
            "freshnessStatus": "fresh"
          },
          "MLS": {
            "value": {
              "line1": "123 Main Street",
              "city": "Dallas",
              "state": "TX",
              "postalCode": "75001"
            },
            "displayValue": "123 Main Street, Dallas, TX 75001",
            "fetchedAt": "2026-03-18T10:00:00Z",
            "sourceObservedAt": "2026-03-18T00:00:00Z",
            "ageDays": 3,
            "freshnessStatus": "fresh"
          },
          "MANUAL": null
        },
        "conflict": {
          "hasConflict": false,
          "conflictIds": []
        },
        "manualOverride": {
          "isActive": false,
          "overrideId": null
        }
      }
    },
    "physical": {},
    "unitOccupancy": {},
    "income": {},
    "valuation": {},
    "tax": {}
  }
}
```

## Cockpit Payload Requirements

Every cockpit field node must expose:

- canonical value
- all available source values
- source freshness
- conflict state
- manual override state
- selected source identity

The cockpit must not infer conflict, freshness, or override state locally.

## Backend Implementation Notes

- raw provider payloads persist in `property_source_imports`
- normalized extraction persists in `property_field_observations`
- canonical selected field values persist in `property_field_resolutions`
- property-wide current answer persists in `properties`
- unresolved field disagreement persists in `property_conflicts`
- manual analyst authority persists in `property_manual_overrides`

This preserves:

- auditability
- explainability
- field-level source provenance
- deterministic underwriting reads
