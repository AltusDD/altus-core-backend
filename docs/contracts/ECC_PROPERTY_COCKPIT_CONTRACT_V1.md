# ECC PROPERTY COCKPIT CONTRACT V1

Status: Core-lane contract baseline
Route: `GET /api/ecc/property/cockpit`
Runtime owner: `azure/functions/asset_ingest/function_app.py`

This document records the currently executable contract for the first canonical cockpit payload route. It is grounded in the live handler and service code on `main`.

## Current Behavior

- Accepts `assetId` as a required query parameter.
- Accepts `dealId` as an optional query parameter.
- Accepts `transactionId` as an optional query parameter.
- Returns a `200` JSON object with a `data` payload on success.
- Uses database-first reads when Supabase-backed tables are available.
- Falls back to a null-safe payload shape when schema-backed rows are not yet available.
- Guarantees non-null summary objects for frontend consumption.
- Uses empty arrays, zero counts, and `"unknown"` status defaults instead of summary-object nulls.
- Returns a `400` JSON object for validation failure.
- Returns a `500` JSON object for unexpected runtime failure.

## Required Query Parameters

- `assetId`

## Optional Query Parameters

- `dealId`
- `transactionId`

## Success Contract

Status code:
- `200`

Response shape:

```json
{
  "data": {
    "propertyId": "asset-001",
    "assetId": "asset-001",
    "organizationId": null,
    "dealId": "deal-001",
    "transactionId": "txn-001",
    "sourceHeaderSummary": {
      "structuredSources": [],
      "evidenceSources": []
    },
    "reconciliationSummary": {
      "reconciliationStatus": "unknown",
      "unresolvedConflictCount": 0,
      "activeManualOverrideCount": 0,
      "lastReconciledAt": null
    },
    "evidenceMediaSummary": {
      "importedStructuredData": {
        "latestMlsSnapshotId": null,
        "latestCorelogicSnapshotId": null
      },
      "importedMedia": {
        "listingMediaCount": 0,
        "hasPrimaryPhoto": false
      },
      "fieldEvidence": {
        "fieldPhotoCount": 0,
        "fieldDocumentCount": 0,
        "lastCapturedAt": null
      },
      "fileStorageReferences": {
        "dropboxFileCount": 0,
        "verifiedReferenceCount": 0
      },
      "sourceTypesPresent": []
    },
    "transactionDocumentChecklistSummary": {
      "checklistStatus": "unknown",
      "requiredItemCount": 0,
      "receivedItemCount": 0,
      "missingItemCount": 0,
      "needsReviewItemCount": 0,
      "approvedItemCount": 0,
      "groups": []
    },
    "clientVisibleFileSummary": {
      "clientVisibleCount": 0,
      "investorVisibleCount": 0,
      "expiringShareCount": 0,
      "artifacts": []
    }
  }
}
```

Notes:

- `propertyId` is currently sourced from the property row when present; otherwise it falls back to `assetId`.
- `sourceHeaderSummary` is backed today by current source rows when `asset_data_raw` is available.
- `reconciliationSummary`, evidence summaries, checklist summaries, and client-visible artifact summaries read schema-backed rows when those tables exist and fall back to null-safe defaults otherwise.
- The following objects are always present and non-null:
  - `sourceHeaderSummary`
  - `reconciliationSummary`
  - `evidenceMediaSummary`
  - `transactionDocumentChecklistSummary`
  - `clientVisibleFileSummary`
- Supported source types in payload logic are:
  - `MLS`
  - `CORELOGIC`
  - `FIELD`
  - `DROPBOX`
  - `ZIPFORMS`
  - `MANUAL`

## Error Contract

Status code:
- `400` for validation failures
- `500` for unexpected runtime failures

Response shape:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "assetId is required"
  }
}
```

Named error codes:

- `VALIDATION_FAILED`
- `INTERNAL_ERROR`

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/ecc_property_cockpit/success_response.json`
- `docs/contracts/fixtures/ecc_property_cockpit/error_missing_asset_id_response.json`
- `docs/contracts/fixtures/ecc_property_cockpit/error_internal_response.json`

## Proof Rules

- If query parameters, response shape, or handler headers change, the fixtures and tests must change in the same PR.
- If more schema-backed domains become live later, additive fields may be populated without removing this null-safe baseline shape.
