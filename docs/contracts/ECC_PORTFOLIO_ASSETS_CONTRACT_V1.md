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
- Returns a deterministic payload today from in-code service logic derived from `portfolioId`, `limit`, and `offset`.

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

Deterministic behavior grounded in current code:
- top-level payload contains `data` and `meta`
- `meta.portfolioId`, `meta.limit`, and `meta.offset` echo request values after validation/defaulting
- `meta.total` is derived deterministically from the `portfolioId` character seed
- each returned asset row is deterministic for the given `portfolioId`, `limit`, and `offset`
- `assetType` is currently `multifamily`
- `status` is currently `stub_ready`
- `x-ecc-handler` is `ecc-portfolio-assets`
- `x-ecc-domain-signature` is `ecc.portfolio.assets.v1`

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

- If the response payload, handler headers, or deterministic service logic changes, the fixtures and tests must change in the same PR.
- If the route begins reading additional request inputs later, the request contract and proof fixtures must be expanded in the same PR.
- This contract does not claim persistence behavior because the current implementation returns deterministic in-code portfolio asset data only.
