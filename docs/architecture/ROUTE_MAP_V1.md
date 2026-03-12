# ROUTE_MAP_V1

Status: active discovery baseline  
Canonical route owner: `azure/functions/asset_ingest/function_app.py`

This map is derived from live `@app.route(...)` decorators on `origin/main`. It should be treated as the backend route SSOT until a new runtime surface is added.

## Discovered Route Families

- `assets`: ingest/write path
- `ecc`: read-only portfolio, search, metrics, and health surfaces
- `price-engine`: calculation surface

## Endpoint Ownership Map

| Method | Endpoint | Route Family | Entry Function | Downstream Handler | Service/Write Path | Notes |
|---|---|---|---|---|---|---|
| POST | `/api/assets/ingest` | `assets` | `assets_ingest` | Inline in `function_app.py` | Supabase REST writes to `assets` and `asset_data_raw` | Only discovered route with clear durable write behavior |
| GET | `/api/ecc/portfolio/summary` | `ecc` | `ecc_portfolio_summary` | `handle_ecc_portfolio_summary` | `build_portfolio_summary` | Deterministic in-code response; no storage read discovered |
| GET | `/api/ecc/portfolio/assets` | `ecc` | `ecc_portfolio_assets` | `handle_ecc_portfolio_assets` | `build_portfolio_assets` | Deterministic in-code response with pagination metadata |
| GET | `/api/ecc/assets/search` | `ecc` | `ecc_asset_search` | `handle_ecc_asset_search` | `build_asset_search_results` | Deterministic in-code response; query parameter is required |
| GET | `/api/ecc/assets/metrics` | `ecc` | `ecc_asset_metrics` | `handle_ecc_asset_metrics` | `build_asset_metrics` | Deterministic in-code response; `assetId` is required |
| GET | `/api/ecc/system/health` | `ecc` | `ecc_system_health` | `handle_ecc_system_health` | `build_system_health` | Deterministic in-code health payload; not yet bound to live dependency probes |
| POST | `/api/price-engine/calculate` | `price-engine` | `price_engine_calculate` | `handle_price_engine_calculate` | `calculate_price_engine` | Pure calculation path with validation and error codes; no durable storage discovered |

## Route Contract Notes

| Endpoint | Inputs Observed in Code | Output Shape Observed in Code | Unknowns / Gaps |
|---|---|---|---|
| `/api/assets/ingest` | Header `x-altus-org-id`; body fields `source`, `raw`, optional `asset` | `{ ok, asset_id, raw_id, payload_hash }` on success | No external contract doc found for request schema beyond handler validation |
| `/api/ecc/portfolio/summary` | Query `portfolioId`, optional `asOfDate` | `{ data: { ... } }` or `{ error: { ... } }` | Response is service-generated placeholder data, not linked to a persistent source |
| `/api/ecc/portfolio/assets` | Query `portfolioId`, optional `limit`, `offset` | `{ data: [...], meta: { ... } }` or `{ error: { ... } }` | No evidence yet that asset rows come from a persistent store |
| `/api/ecc/assets/search` | Query `q`, optional `limit`, `offset` | `{ data: [...], meta: { ... } }` or `{ error: { ... } }` | Matching logic is deterministic and code-local today |
| `/api/ecc/assets/metrics` | Query `assetId`, optional `windowDays` | `{ data: { ... } }` or `{ error: { ... } }` | Metrics are deterministic calculations, not observed from telemetry or DB reads |
| `/api/ecc/system/health` | No required query parameters | `{ data: { ... } }` or `{ error: { ... } }` | Health result is synthetic and should not be treated as infrastructure truth without further work |
| `/api/price-engine/calculate` | JSON body with strategy and financial inputs | `{ MAO, IRR, CoC, CashToClose, Profit, RiskScore }` or `{ error: { ... } }` | No separate contract spec file exists yet; this map is the current executable contract reference |

## Ownership Rules

- Any route add/remove/rename must update this file in the same PR.
- Any route whose behavior changes must update both this file and [docs/contracts/README.md](../contracts/README.md).
- If a route begins reading from or writing to a new system of record, [docs/architecture/DATA_MAP_V1.md](DATA_MAP_V1.md) must be updated in the same change.

## Known Unknowns

- No second backend runtime surface was discovered outside `azure/functions/asset_ingest/function_app.py`.
- No OpenAPI document, schema registry, or explicit versioned contract pack was found on `origin/main`.
- ECC route names and headers are real, but the underlying payloads are currently code-generated placeholders rather than proven persistent reads.
