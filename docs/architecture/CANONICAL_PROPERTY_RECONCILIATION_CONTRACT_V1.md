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
It must support full-ingestion durability for MLS records while allowing selective cockpit exposure.

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
- `canonical_geo_json`
- `canonical_apn`
- `canonical_listing_identity_json`
- `canonical_listing_lifecycle_json`
- `canonical_beds`
- `canonical_baths`
- `canonical_bath_breakdown_json`
- `canonical_rooms_total`
- `canonical_sqft`
- `canonical_above_grade_finished_sqft`
- `canonical_below_grade_finished_sqft`
- `canonical_main_level_finished_sqft`
- `canonical_upper_level_finished_sqft`
- `canonical_lower_level_finished_sqft`
- `canonical_lot_size_sqft`
- `canonical_lot_size_acres`
- `canonical_year_built`
- `canonical_levels`
- `canonical_architectural_style`
- `canonical_property_type`
- `canonical_property_subtype`
- `canonical_property_attached`
- `canonical_new_construction`
- `canonical_basement_json`
- `canonical_garage_json`
- `canonical_fireplace`
- `canonical_waterfront`
- `canonical_water_body_name`
- `canonical_unit_count`
- `canonical_interior_systems_json`
- `canonical_exterior_systems_json`
- `canonical_association_json`
- `canonical_rent_indicators_json`
- `canonical_listing_terms_json`
- `canonical_remarks_json`
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
- `import_family`
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
- MLS listing snapshots stay durable even when many fields are not promoted to canonical property truth.

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
- `city`
- `state`
- `postal_code`
- `county`
- `township`
- `subdivision_name`
- `mls_number`
- `historical_mls_number`
- `listing_status`
- `listing_date`
- `status_change_timestamp`
- `dom`
- `original_list_price`
- `list_price`
- `close_price`
- `contingent`
- `back_on_market_date`
- `close_date`
- `apn`
- `tax_legal_description`
- `zoning_description`
- `latitude`
- `longitude`
- `directions`
- `cross_street`
- `beds`
- `baths`
- `bath_breakdown`
- `rooms_total`
- `sqft`
- `above_grade_finished_area`
- `below_grade_finished_area`
- `main_level_finished_sqft`
- `upper_level_finished_sqft`
- `lower_level_finished_sqft`
- `lot_size`
- `lot_size_acres`
- `year_built`
- `levels`
- `architectural_style`
- `property_type`
- `property_subtype`
- `property_attached`
- `new_construction`
- `basement`
- `garage`
- `garage_spaces`
- `fireplace`
- `waterfront`
- `water_body_name`
- `unit_count`
- `appliances`
- `interior_features`
- `exterior_features`
- `flooring`
- `parking_features`
- `patio_and_porch_features`
- `cooling`
- `heating`
- `utilities`
- `water_source`
- `sewer`
- `roof`
- `security_features`
- `construction_materials`
- `electric`
- `laundry_features`
- `lot_features`
- `other_structures`
- `association_name`
- `association_phone`
- `association_fee`
- `association_fee_frequency`
- `association_amenities`
- `earnest_money_deposit`
- `listing_terms`
- `seller_concessions`
- `buyer_financing`
- `concessions`
- `possession`
- `public_remarks`
- `public_historical_remarks`
- `documents_available`
- `special_listing_conditions`
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

### 7. `property_source_rooms`

Repeatable room-level child records per source snapshot.

Required fields:

- `source_room_id`
- `property_id`
- `source_import_id`
- `source_type`
- `ordinal`
- `room_name`
- `level`
- `length`
- `width`
- `dimensions_display`
- `room_remarks`
- `normalized_room_type`
- `created_at`

Notes:

- one-to-many room records are source-snapshot scoped
- room rows are durable ingest evidence, not flattened into one JSON string
- cockpit detail views can render these without mutating canonical field tables

### 8. `property_source_media`

Ordered media references per source snapshot.

Required fields:

- `source_media_id`
- `property_id`
- `source_import_id`
- `source_type`
- `ordinal`
- `media_type`
- `media_url`
- `thumbnail_url`
- `caption`
- `mime_type`
- `width_px`
- `height_px`
- `source_media_key`
- `is_primary`
- `created_at`

Notes:

- media must not be stored as a flat URL-only list
- ordering is durable per source snapshot
- metadata is retained for selective cockpit display and future asset download pipelines

### 9. `property_source_association_amenities`

Repeatable association amenity child records when a provider emits structured amenities.

Required fields:

- `source_association_amenity_id`
- `property_id`
- `source_import_id`
- `source_type`
- `ordinal`
- `amenity_name`
- `amenity_category`
- `created_at`

## Expanded Field Groups Proposed

### Listing Identity / Lifecycle Group

- `mls_number`
- `listing_status`
- `listing_date`
- `status_change_timestamp`
- `dom`
- `original_list_price`
- `list_price`
- `close_price`
- `contingent`
- `back_on_market_date`
- `close_date`
- `historical_mls_number`

### Property Identity Group

- `address`
- `apn`
- `city`
- `state`
- `postal_code`
- `county`
- `township`
- `subdivision_name`
- `tax_legal_description`
- `zoning_description`
- `latitude`
- `longitude`
- `directions`
- `cross_street`

### Physical Structure Group

- `sqft`
- `lot_size`
- `lot_size_acres`
- `year_built`
- `levels`
- `architectural_style`
- `property_type`
- `property_subtype`
- `property_attached`
- `new_construction`
- `garage`
- `garage_spaces`
- `fireplace`
- `waterfront`
- `water_body_name`
- `above_grade_finished_area`
- `below_grade_finished_area`
- `main_level_finished_sqft`
- `upper_level_finished_sqft`
- `lower_level_finished_sqft`
- `unit_count`

### Unit / Occupancy Group

- `beds`
- `baths`
- `bath_breakdown`
- `rooms_total`

### Interior / Exterior / Systems Group

- `appliances`
- `interior_features`
- `exterior_features`
- `flooring`
- `parking_features`
- `patio_and_porch_features`
- `cooling`
- `heating`
- `utilities`
- `water_source`
- `sewer`
- `roof`
- `security_features`
- `construction_materials`
- `electric`
- `laundry_features`
- `lot_features`
- `other_structures`
- `basement`

### Association / Taxes / Financial Terms Group

- `association_name`
- `association_phone`
- `association_fee`
- `association_fee_frequency`
- `association_amenities`
- `tax_annual_amount`
- `tax_year`
- `earnest_money_deposit`
- `listing_terms`
- `seller_concessions`
- `buyer_financing`
- `concessions`
- `possession`

### Remarks / Marketing / Source Text Group

- `public_remarks`
- `public_historical_remarks`
- `documents_available`
- `special_listing_conditions`

### Income Group

- `rent_indicators`

### Valuation Group

- `valuation_avm`

### Tax Group

- `tax_metadata`

### Child Collection Group

- `rooms`
- `media`
- `association_amenities`

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

### `listing_status`

Selection rule:

1. active manual override
2. MLS listing status
3. CoreLogic market status proxy when available

Conflict rule:

- mark `conflicting` when sources indicate materially different active vs closed state

### `mls_number`

Selection rule:

1. active manual override
2. MLS number
3. historical MLS number set retained in source snapshots only

Conflict rule:

- mark `conflicting` when multiple active MLS identifiers compete for the same source snapshot lineage

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

### `bath_breakdown`

Selection rule:

1. active manual override
2. MLS typed bath breakdown
3. CoreLogic bath detail breakdown

Conflict rule:

- mark `conflicting` when total or typed composition differs materially

### `sqft`

Selection rule:

1. active manual override
2. MLS living area sqft
3. CoreLogic building area sqft

Conflict rule:

- mark `conflicting` when both exist and the normalized numeric delta is greater than 5 percent

### `above_grade_finished_area`, `below_grade_finished_area`, `main_level_finished_sqft`, `upper_level_finished_sqft`, `lower_level_finished_sqft`

Selection rule:

1. active manual override
2. MLS finished-area components
3. CoreLogic finished-area components

Conflict rule:

- mark `conflicting` when overlapping component values differ by more than 5 percent

### `lot_size`

Selection rule:

1. active manual override
2. CoreLogic lot size
3. MLS lot size

Conflict rule:

- mark `conflicting` when both exist and the normalized numeric delta is greater than 5 percent

### `lot_size_acres`

Selection rule:

1. active manual override
2. normalized acreage derived from direct source acreage field
3. normalized acreage derived from square feet conversion

Conflict rule:

- mark `conflicting` when direct acreage fields materially disagree

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

### `property_subtype`

Selection rule:

1. active manual override
2. MLS subtype
3. CoreLogic subtype or class extension

Conflict rule:

- mark `conflicting` when normalized subtype values differ

### `levels`, `architectural_style`, `property_attached`, `new_construction`, `garage`, `garage_spaces`, `fireplace`, `waterfront`, `water_body_name`

Selection rule:

1. active manual override
2. MLS structural field
3. CoreLogic structural field

Conflict rule:

- mark `conflicting` when both sources exist and normalize unequal

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

### `listing_terms`, `seller_concessions`, `buyer_financing`, `concessions`, `possession`

Selection rule:

1. active manual override
2. MLS transaction term fields
3. CoreLogic transaction term fields when available

Conflict rule:

- mark `conflicting` when overlapping structured term values differ materially

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

### `association_name`, `association_phone`, `association_fee`, `association_fee_frequency`, `association_amenities`

Selection rule:

1. active manual override
2. MLS association fields
3. CoreLogic HOA / association fields

Conflict rule:

- mark `conflicting` when overlapping structured association fields differ materially

### `public_remarks`, `public_historical_remarks`, `documents_available`, `special_listing_conditions`

Selection rule:

1. active manual override
2. MLS listing text and document metadata
3. CoreLogic descriptive text fields when available

Conflict rule:

- descriptive fields are typically not blocking conflicts
- retain source text independently even when canonical selection prefers one source

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

## Child Collection Model

Repeatable child collections must remain source-snapshot scoped rather than collapsed into single canonical scalar fields.

### Rooms

Storage:

- `property_source_rooms`

Canonical handling:

- room rows are source detail, not top-level canonical property truth
- top-level canonical promotion is limited to summary fields such as `rooms_total`

### Media

Storage:

- `property_source_media`

Canonical handling:

- media remains ordered source detail
- cockpit reads may expose selected primary media separately, but durable storage keeps full ordered metadata

### Association Amenities

Storage:

- `property_source_association_amenities`

Canonical handling:

- canonical property may expose summarized amenity sets, but durable ingest remains repeatable child rows

## Updated Cockpit Payload Shape

### 1. Source-Aware Summary View

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
  "summary": {
    "address": "123 Main St, Dallas, TX 75001",
    "propertyType": "single_family",
    "beds": 4,
    "bathsTotal": 3.5,
    "livingAreaSqft": 2480,
    "lotSizeSqft": 8400,
    "yearBuilt": 1998,
    "listingStatus": "active",
    "listPrice": 425000,
    "valuationAmount": 418000,
    "selectedPrimarySource": "MLS",
    "selectedPrimarySourceFreshness": {
      "ageDays": 1,
      "freshnessStatus": "fresh"
    }
  }
}
```

### 2. Reconciliation View

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
    "listingIdentityLifecycle": {},
    "propertyIdentity": {
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
    "physicalStructure": {},
    "unitOccupancy": {},
    "interiorExteriorSystems": {},
    "associationTaxesFinancialTerms": {},
    "remarksMarketingSourceText": {},
    "income": {},
    "valuation": {},
    "tax": {}
  }
}
```

### 3. Expanded Listing Detail Drawer / Panel

```json
{
  "propertyId": "prop_123",
  "activeSourceSnapshot": {
    "sourceImportId": "src_mls_20260321_001",
    "sourceType": "MLS",
    "mlsNumber": "MLS-998877",
    "fetchedAt": "2026-03-21T14:00:00Z",
    "sourceObservedAt": "2026-03-21T13:58:00Z"
  },
  "listingDetail": {
    "listingIdentityLifecycle": {
      "listingStatus": "active",
      "listingDate": "2026-03-20",
      "statusChangeTimestamp": "2026-03-21T09:05:00Z",
      "dom": 3,
      "originalListPrice": 435000,
      "listPrice": 425000,
      "closePrice": null,
      "contingent": false,
      "backOnMarketDate": null,
      "closeDate": null,
      "historicalMlsNumber": ["MLS-991122"]
    },
    "propertyIdentity": {
      "address": "123 Main St",
      "city": "Dallas",
      "state": "TX",
      "postalCode": "75001",
      "county": "Dallas",
      "township": null,
      "subdivisionName": "Oak Ridge",
      "parcelNumber": "R123456",
      "taxLegalDescription": "Lot 5 Block 2 Oak Ridge",
      "zoningDescription": "SF-8",
      "latitude": 32.991,
      "longitude": -96.802,
      "directions": "From Main turn east on Oak",
      "crossStreet": "Oak Ave"
    },
    "physicalStructure": {},
    "interiorExteriorSystems": {},
    "associationTaxesFinancialTerms": {},
    "remarksMarketingSourceText": {
      "publicRemarks": "Updated home with flexible floor plan.",
      "publicHistoricalRemarks": [],
      "documentsAvailable": ["seller_disclosure", "survey"],
      "specialListingConditions": ["none"]
    },
    "rooms": [
      {
        "ordinal": 1,
        "roomName": "Primary Bedroom",
        "level": "Upper",
        "length": 16,
        "width": 14,
        "remarks": "Walk-in closet"
      }
    ],
    "media": [
      {
        "ordinal": 1,
        "mediaType": "photo",
        "mediaUrl": "https://example.test/photo-1.jpg",
        "thumbnailUrl": "https://example.test/photo-1-thumb.jpg",
        "caption": "Front elevation",
        "mimeType": "image/jpeg",
        "widthPx": 2048,
        "heightPx": 1365,
        "isPrimary": true
      }
    ]
  }
}
```

## Cockpit Payload Requirements

Every reconciliation field node must expose:

- canonical value
- all available source values
- source freshness
- conflict state
- manual override state
- selected source identity

The cockpit must not infer conflict, freshness, or override state locally.

Detail drawer requirements:

- source snapshot detail can expose child collections directly
- source snapshot detail does not need to flatten rooms or media into field-level scalars
- listing metadata and remarks may be durable source detail even when not elevated into underwriting summary cards

## Backend Implementation Notes

- raw provider payloads persist in `property_source_imports`
- normalized extraction persists in `property_field_observations`
- canonical selected field values persist in `property_field_resolutions`
- property-wide current answer persists in `properties`
- unresolved field disagreement persists in `property_conflicts`
- manual analyst authority persists in `property_manual_overrides`
- room-level ingest persists in `property_source_rooms`
- media ingest persists in `property_source_media`
- repeatable association amenity ingest persists in `property_source_association_amenities`

This preserves:

- auditability
- explainability
- field-level source provenance
- deterministic underwriting reads
