# ASSETS_INGEST_CONTRACT_V1

Status: Core-lane contract baseline
Route: `POST /api/assets/ingest`
Runtime owner: `azure/functions/asset_ingest/function_app.py`

This document records the currently executable contract for the assets ingest route. It is grounded in the live function code on `main`.

## Current Behavior

- Requires the `x-altus-org-id` header and validates it as a UUID.
- Accepts a JSON object request body.
- Requires `source` to be one of `CORELOGIC`, `MLS`, `DOORLOOP`, `MANUAL`, or `OTHER`.
- Requires `raw` and validates it as a JSON object.
- Writes one row to `assets` and one row to `asset_data_raw` on success.
- Returns a `200` JSON object on success.
- Returns a `400` JSON object for validation failures.
- Returns a `500` JSON object for unexpected runtime failures.

## Required Header

- `x-altus-org-id`

## Required Request Fields

- `source`
- `raw`

## Optional Request Fields

- `asset.name`
- `asset.asset_type`
- `asset.status`

## Success Contract

Status code:
- `200`

Response shape:

```json
{
  "ok": true,
  "asset_id": "00000000-0000-0000-0000-000000000001",
  "raw_id": "00000000-0000-0000-0000-000000000002",
  "payload_hash": "960598a594426ae33aa821f596e4f26189fa328578c1d125301c9850eecb7238"
}
```

Notes:
- Success response is a flat JSON object.
- `payload_hash` is the SHA-256 of the canonicalized `raw` object.
- `asset_id` and `raw_id` are sourced from the insert results returned by the durable write path.

## Error Contract

Status code:
- `400` for validation failures
- `500` for unexpected runtime failures

Response shape:

```json
{
  "ok": false,
  "error": "human readable message"
}
```

Observed validation messages in code include:
- `Missing required header: x-altus-org-id`
- `x-altus-org-id must be a valid UUID`
- `Request body must be a JSON object`
- `source must be one of CORELOGIC|MLS|DOORLOOP|MANUAL|OTHER`
- `raw is required`
- `raw must be a JSON object`
- `asset must be a JSON object when provided`

Named error codes:
- none observed in the current route implementation

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/assets_ingest/success_request.json`
- `docs/contracts/fixtures/assets_ingest/success_response.json`
- `docs/contracts/fixtures/assets_ingest/error_missing_header_request.json`
- `docs/contracts/fixtures/assets_ingest/error_missing_header_response.json`
- `docs/contracts/fixtures/assets_ingest/error_invalid_source_request.json`
- `docs/contracts/fixtures/assets_ingest/error_invalid_source_response.json`
- `docs/contracts/fixtures/assets_ingest/error_internal_response.json`

## Proof Rules

- If the request, header, or response contract changes, the fixtures and tests must change in the same PR.
- If the route begins returning named error codes later, they must be documented here and covered by proof-bearing tests.
- This contract does claim durable write behavior because the route currently inserts into both `assets` and `asset_data_raw`.
