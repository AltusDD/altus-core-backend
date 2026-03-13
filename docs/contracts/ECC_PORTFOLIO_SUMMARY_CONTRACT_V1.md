# ECC_PORTFOLIO_SUMMARY_CONTRACT_V1

Status: Core-lane contract baseline
Route: `GET /api/ecc/portfolio/summary`
Runtime owner: `azure/functions/asset_ingest/ecc_portfolio_summary_handler.py`

This document records the currently executable contract for the ECC portfolio summary route. It is grounded in the live handler and service code on `main`.

## Current Behavior

- Requires the `portfolioId` query parameter.
- Accepts an optional `asOfDate` query parameter.
- Returns a `200` JSON object on success.
- Returns a `400` JSON error envelope when `portfolioId` is missing.
- Returns a `500` JSON error envelope only when an unexpected internal exception occurs.
- Adds response headers for build identity and ECC handler/domain identity.
- Returns a deterministic payload today from in-code service logic derived from the provided `portfolioId`.

## Request Contract

Required query parameters:
- `portfolioId`

Optional query parameters:
- `asOfDate`

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
  "data": {
    "portfolioId": "portfolio-001",
    "asOfDate": "2026-03-13",
    "assetCount": 13,
    "occupiedUnits": 48,
    "totalUnits": 52,
    "occupancyRate": 0.9230769230769231,
    "estimatedValue": 1625000.0,
    "currency": "USD",
    "activeAlerts": 0,
    "status": "stub_ready"
  }
}
```

Deterministic behavior grounded in current code:
- top-level payload is wrapped in `data`
- `portfolioId` echoes the required query parameter
- `asOfDate` echoes the optional query parameter value or `null`
- numeric fields are derived deterministically from the `portfolioId` character seed
- `currency` is currently `USD`
- `status` is currently `stub_ready`
- `x-ecc-handler` is `ecc-portfolio-summary`
- `x-ecc-domain-signature` is `ecc.portfolio.summary.v1`

## Error Contract

Status code:
- `400` when `portfolioId` is missing
- `500` for unexpected internal failures

Response shape:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "portfolioId is required"
  }
}
```

Named error codes currently observed in code:
- `VALIDATION_FAILED`
- `INTERNAL_ERROR`

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/ecc_portfolio_summary/success_response.json`
- `docs/contracts/fixtures/ecc_portfolio_summary/error_missing_portfolio_id_response.json`
- `docs/contracts/fixtures/ecc_portfolio_summary/error_internal_response.json`

## Proof Rules

- If the response payload, handler headers, or deterministic service logic changes, the fixtures and tests must change in the same PR.
- If the route begins reading additional request inputs later, the request contract and proof fixtures must be expanded in the same PR.
- This contract does not claim persistence behavior because the current implementation returns deterministic in-code portfolio summary data only.
