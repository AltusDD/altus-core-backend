# ROUTE_MAP_V1

Canonical route owner: `azure/functions/asset_ingest/function_app.py`

## Endpoint Ownership Map

| Method | Endpoint | Handler | Runtime File | Notes |
|---|---|---|---|---|
| POST | `/api/assets/ingest` | `assets_ingest` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/match` | `assets_match` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/resolve` | `assets_resolve` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/bulk-resolve` | `assets_bulk_resolve` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/upsert` | `assets_upsert` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/link` | `assets_link_create` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/{asset_id}/archive` | `asset_archive` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| POST | `/api/assets/{asset_id}/restore` | `asset_restore` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| DELETE | `/api/assets/link` | `assets_link_delete` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| DELETE | `/api/assets/{asset_id}` | `asset_delete` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| GET | `/api/assets` | `assets_list` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| GET | `/api/assets/overview` | `assets_overview` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| GET | `/api/assets/metrics` | `assets_metrics` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| GET | `/api/assets/export` | `assets_export` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| GET | `/api/assets/{id}` | `asset_detail` | `azure/functions/asset_ingest/function_app.py` | Runtime path param name: `{asset_id}` |
| GET | `/api/assets/{id}/raw` | `asset_raw_list` | `azure/functions/asset_ingest/function_app.py` | Runtime path param name: `{asset_id}` |
| GET | `/api/assets/{id}/links` | `asset_detail` / `asset_snapshot` link projections | `azure/functions/asset_ingest/function_app.py` | Link views produced inside detail/snapshot contracts in current module |
| GET | `/api/assets/{id}/timeline` | `asset_timeline` | `azure/functions/asset_ingest/function_app.py` | Runtime path param name: `{asset_id}` |
| GET | `/api/assets/{id}/snapshot` | `asset_snapshot` | `azure/functions/asset_ingest/function_app.py` | Runtime path param name: `{asset_id}` |
| GET | `/api/assets/{id}/audit` | `asset_audit` | `azure/functions/asset_ingest/function_app.py` | Runtime path param name: `{asset_id}` |
| GET | `/api/assets/search` | `assets_search` | `azure/functions/asset_ingest/function_app.py` | Accepted live route |
| GET | `/api/ecc/portfolio/summary` | `ecc_portfolio_summary` | `azure/functions/asset_ingest/function_app.py` | ECC singleton summary stub with deterministic placeholder data |

## Determinism Notes

- Route ownership in this map is derived from live decorators in `function_app.py`.
- Any route addition/removal requires this map update in the same PR.
- Accepted contract surfaces must remain mapped to live handlers and cannot be downgraded in documentation.
