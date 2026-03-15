# ECC_PORTFOLIO_ASSETS_CONTRACT_V1

Status: Core-lane contract baseline
Route: `GET /api/ecc/portfolio/assets`
Runtime owner: `azure/functions/asset_ingest/ecc_portfolio_assets_handler.py`

This document records the currently executable contract for the ECC portfolio assets route. It is grounded in the live handler and service code on `main`.

## Current Behavior

- Requires the `portfolioId` query parameter.
- Accepts optional `limit` and `offset` query parameters.
- Returns a `200` JSON object on success.
- Returns a `400` JSON error envelope when `portfolioId` is missing or pagination inputs are invalid.
- Returns a `500` JSON error envelope only when an unexpected internal exception occurs.
- Adds response headers for build identity and ECC handler/domain identity.
- Returns deterministic fallback payload rows from in-code service logic when no proven backing source is configured or when live proof is incomplete.
- May back a narrow live field subset from normalized read-only sources when the portfolio cohort mapping seam is configured and the backing read succeeds.

## Request Contract

Required query parameters:
- `portfolioId`

Optional query parameters:
- `limit`
- `offset`

Current validation rules:
- `limit` defaults to `25`
- `offset` defaults to `0`
- `limit` and `offset` must be integers
- `limit` must be `1..100`
- `offset` must be `>= 0`

## Success Contract

Status code:
- `200`

Required headers:
- `x-altus-build-sha`
- `x-ecc-handler`
- `x-ecc-domain-signature`

Response shape:

```json
{
  "data": [
    {
      "assetId": "portfolio-001-asset-002",
      "portfolioId": "portfolio-001",
      "displayName": "Portfolio Asset 2",
      "assetType": "multifamily",
      "status": "stub_ready",
      "occupiedUnits": 7,
      "totalUnits": 9,
      "occupancyRate": 0.7777777777777778,
      "marketValue": 200000.0,
      "city": null,
      "state": null
    }
  ],
  "meta": {
    "portfolioId": "portfolio-001",
    "limit": 2,
    "offset": 1,
    "total": 13
  }
}
```

Current executable guarantees grounded in code:
- top-level payload contains `data` and `meta`
- `meta.portfolioId`, `meta.limit`, and `meta.offset` echo request values after validation/defaulting
- `assetType` remains deterministic fallback data
- `occupiedUnits` remains deterministic fallback data
- `occupancyRate` remains deterministic fallback data
- `marketValue` remains deterministic fallback data
- `city` and `state` remain deterministic fallback data
- `x-ecc-handler` is `ecc-portfolio-assets`
- `x-ecc-domain-signature` is `ecc.portfolio.assets.v1`

When the proven live backing path is configured and succeeds, the route may replace only this narrow field subset without changing the public response shape:

- `data[*].assetId` from `public.assets.id`
- `data[*].displayName` from `public.assets.display_name`
- `data[*].assetType` from `public.assets.asset_type`
- `data[*].status` from `public.assets.status`
- `data[*].totalUnits` from `public.asset_specs_reconciled.units_count` joined by `asset_specs_reconciled.asset_id -> public.assets.id`
- `meta.total` from the exact resolved `public.assets` cohort size

Fallback rules for the current live slice:

- if portfolio cohort resolution is unavailable, the full deterministic fallback payload is returned
- if a returned live asset row lacks a proven `asset_type`, only that row's `assetType` remains on deterministic fallback
- if a returned live asset row lacks a proven `units_count`, only that row's `totalUnits` remains on deterministic fallback
- no occupancy, market value, or geo semantics are inferred from DB truth in this slice

## Error Contract

Status code:
- `400` when required or pagination inputs are invalid
- `500` for unexpected internal failures

Response shape:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "human readable message"
  }
}
```

Named error codes currently observed in code:
- `VALIDATION_FAILED`
- `INTERNAL_ERROR`

Observed validation messages in code include:
- `portfolioId is required`
- `limit and offset must be integers`
- `limit must be 1..100 and offset must be >= 0`

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/ecc_portfolio_assets/success_response.json`
- `docs/contracts/fixtures/ecc_portfolio_assets/error_missing_portfolio_id_response.json`
- `docs/contracts/fixtures/ecc_portfolio_assets/error_invalid_pagination_response.json`
- `docs/contracts/fixtures/ecc_portfolio_assets/error_internal_response.json`

## Proof Rules

- If the response payload, handler headers, fallback behavior, or live-backed field subset changes, the fixtures and tests must change in the same PR.
- If the route begins reading additional request inputs later, the request contract and proof fixtures must be expanded in the same PR.
- This contract does not claim write behavior because the route is read-only in the current implementation.
- This contract now claims a narrow optional live read path for `assetId`, `displayName`, `assetType`, `status`, `totalUnits`, and `meta.total` only when the configured portfolio cohort mapping and normalized backing reads succeed.
