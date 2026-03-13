# ECC_SYSTEM_HEALTH_CONTRACT_V1

Status: Core-lane contract baseline
Route: `GET /api/ecc/system/health`
Runtime owner: `azure/functions/asset_ingest/ecc_system_health_handler.py`

This document records the currently executable contract for the ECC system health route. It is grounded in the live handler and service code on `main`.

## Current Behavior

- Accepts a `GET` request with no required query parameters, headers, or body fields.
- Returns a `200` JSON object on success.
- Returns a `500` JSON error envelope only when an unexpected internal exception occurs.
- Adds response headers for build identity and ECC handler/domain identity.
- Returns a deterministic payload today from in-code service data rather than a live downstream probe.

## Request Contract

Required inputs:
- none

Optional inputs:
- none observed in the current handler implementation

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
    "status": "operational",
    "generatedAt": null,
    "components": [
      {
        "name": "assetIndex",
        "status": "operational",
        "latencyMs": 42,
        "details": null
      }
    ],
    "activeIncidents": 1
  }
}
```

Deterministic behavior grounded in current code:
- top-level payload is wrapped in `data`
- `status` is currently `operational`
- `generatedAt` is currently `null`
- `components` currently contains three fixed entries
- `activeIncidents` is currently `1`
- `x-ecc-handler` is `ecc-system-health`
- `x-ecc-domain-signature` is `ecc.system.health.v1`

## Error Contract

Status code:
- `500` for unexpected internal failures

Response shape:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

Named error codes currently observed in code:
- `INTERNAL_ERROR`

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/ecc_system_health/success_response.json`
- `docs/contracts/fixtures/ecc_system_health/error_internal_response.json`

## Proof Rules

- If the response payload, handler headers, or deterministic service values change, the fixtures and tests must change in the same PR.
- If the route begins accepting request inputs later, the request contract and proof fixtures must be expanded in the same PR.
- This contract does not claim persistence behavior because the current implementation returns deterministic in-code system health data only.
