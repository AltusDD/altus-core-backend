# Backend Contract Map

Status: initial SSOT baseline

This repo does not yet contain a full versioned API contract pack. Until one exists, the executable contract surface is defined by:

1. live route decorators in [ROUTE_MAP_V1.md](../architecture/ROUTE_MAP_V1.md)
2. request validation and response shaping in Azure Function handlers
3. proof artifacts attached to the PR that changes a contract

## Current Contract Sources

| Surface | Current Contract Source | Confidence |
|---|---|---|
| `POST /api/assets/ingest` | Inline validation and response body in `azure/functions/asset_ingest/function_app.py` | Medium |
| `GET /api/ecc/portfolio/summary` | `ecc_portfolio_summary_handler.py` and `ecc_portfolio_summary_service.py` | Medium |
| `GET /api/ecc/portfolio/assets` | `ecc_portfolio_assets_handler.py` and `ecc_portfolio_assets_service.py` | Medium |
| `GET /api/ecc/assets/search` | `ecc_asset_search_handler.py` and `ecc_asset_search_service.py` | Medium |
| `GET /api/ecc/assets/metrics` | `ecc_asset_metrics_handler.py` and `ecc_asset_metrics_service.py` | Medium |
| `GET /api/ecc/system/health` | `ecc_system_health_handler.py` and `ecc_system_health_service.py` | Medium |
| `POST /api/price-engine/calculate` | `price_engine_handler.py` and `price_engine_service.py` | Medium |

## Contract Gaps

- No OpenAPI or JSON Schema bundle was discovered on `origin/main`.
- No route-specific example corpus was discovered under `docs/contracts/`.
- No compatibility policy was found that defines what counts as breaking, additive, or internal-only.
- ECC endpoints currently return deterministic in-code payloads. That means the current contract is real, but its backing data source is not yet proven to be durable.

## Required Proof Pack For Future Backend Tasks

Any PR that changes request validation, response fields, status codes, headers, or route ownership should attach a proof pack containing:

- changed route list
- before/after sample requests
- before/after sample responses or error bodies
- note on whether storage behavior changed
- note on whether deployment/config changes are required

If the PR changes only docs or governance, the proof pack can be documentation diff plus route/data map confirmation.

## Contract Change Rules

- Do not invent undocumented endpoint behavior in docs.
- Do not claim storage-backed behavior for ECC routes until code proves it.
- Treat handler code as the current executable source of truth when no higher-order schema exists.
- When a versioned schema pack is introduced later, update this file to point to it and keep the route map/data map aligned.
