# ROUTE_MAP_V1

Canonical route owner: `azure/functions/asset_ingest/function_app.py`

## Endpoint Ownership Map

| Method | Endpoint | Handler | Runtime File | Notes |
|---|---|---|---|---|
| POST | `/api/assets/ingest` | `assets_ingest` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/price-engine/calculate` | `price_engine_calculate` | `azure/functions/asset_ingest/function_app.py` | Price engine calculation stub with contract field rounding and failure catalog |
| GET | `/api/ecc/system/health` | `ecc_system_health` | `azure/functions/asset_ingest/function_app.py` | ECC singleton health stub with deterministic component status values |
| GET | `/api/ecc/assets/metrics` | `ecc_asset_metrics` | `azure/functions/asset_ingest/function_app.py` | ECC singleton stub for asset metrics with normalized occupancy values |
| GET | `/api/ecc/assets/search` | `ecc_asset_search` | `azure/functions/asset_ingest/function_app.py` | ECC list stub for asset search with normalized match scores |
| GET | `/api/ecc/portfolio/assets` | `ecc_portfolio_assets` | `azure/functions/asset_ingest/function_app.py` | ECC list stub for portfolio asset membership with pagination meta |
| GET | `/api/ecc/portfolio/summary` | `ecc_portfolio_summary` | `azure/functions/asset_ingest/function_app.py` | ECC singleton summary stub with deterministic placeholder data |

## Determinism Notes

- Route ownership in this map is derived from live decorators in `function_app.py`.
- Any route addition/removal requires this map update in the same PR.
- Accepted contract surfaces must remain mapped to live handlers and cannot be downgraded in documentation.
