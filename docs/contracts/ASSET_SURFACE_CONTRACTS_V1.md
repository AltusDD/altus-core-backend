# Asset Surface Contracts V1

Canonical runtime owner: `azure/functions/asset_ingest/function_app.py`

Global response headers (all surfaces):

- `x-altus-build-sha`
- `x-altus-config-mode`

Global required request header (all surfaces):

- `x-altus-org-id`

## ORG SCOPING REQUIREMENT

All asset routes require header:

- `x-altus-org-id: <uuid>`

Requests without this header must return HTTP 400.

## NEGATIVE PROOF STANDARD (ACCEPTED ASSET ROUTES)

Accepted asset routes must include deterministic negative-proof evidence in runtime-affecting bundles.

Required negative classes (where applicable to route shape):

- Missing required header `x-altus-org-id` must return `400` with JSON body containing `ok` and `error`.
- Invalid UUID in `x-altus-org-id` must return `400` with JSON body containing `ok` and `error`.
- Invalid payload for JSON body routes must return `400` with JSON body containing `ok` and `error`.
- Internal error responses remain deterministic JSON shape: `{ ok:false, code:<STRING>, error:"Internal server error", status:500 }` for route-specific internal error code paths.

Bundled negative proof for accepted surfaces must preserve reviewed/live SHA continuity via response header `x-altus-build-sha`.
## assets_list

- Route: `GET /api/assets`
- Handler: `assets_list`
- Query params: `limit`, `offset`, `status`, `asset_type`, `q`
- Canonical response: `{ ok, items[], limit, offset }`
- Guaranteed fields: `ok`, `items`, `limit`, `offset`
- Nullable fields: item-level `display_name`, `address_canonical`, `apn`, `clip`, `updated_at`
- Failures: `400 { ok:false, error }`, `500 { ok:false, code:"INGEST_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","status":"ACTIVE"}],"limit":20,"offset":0}
```
- Regression assertions: org-scoped filter enforced; deterministic order `created_at.desc`; default excludes `ARCHIVED`.

## assets_search

- Route: `GET /api/assets/search`
- Handler: `assets_search`
- Query params: `limit`, `offset`, `q`, `apn`, `clip`
- Canonical response: `{ ok, items[], limit, offset }`
- Guaranteed fields: `ok`, `items`, `limit`, `offset`
- Nullable fields: item-level `display_name`, `address_canonical`, `apn`, `clip`
- Failures: `400 { ok:false, error }`, `500 { ok:false, code:"ASSET_SEARCH_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","asset_type":"PROPERTY","status":"ACTIVE"}],"limit":25,"offset":0}
```
- Regression assertions: org-scoped only; `apn/clip` exact-match precedence over `q`.

## asset_detail

- Route: `GET /api/assets/{asset_id}`
- Handler: `asset_detail`
- Query params: none
- Canonical response: `{ ok, asset, latest_raw, links }`
- Guaranteed fields: `ok`, `asset`, `links`
- Nullable fields: `latest_raw`, asset-level `display_name`, `address_canonical`, `apn`, `clip`
- Failures: `400 { ok:false, error }`, `404 { ok:false, code:"ASSET_NOT_FOUND", error:"Asset not found", status:404 }`, `500 { ok:false, code:"INGEST_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset":{"id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","status":"ACTIVE"},"latest_raw":null,"links":[]}
```
- Regression assertions: org ownership required; UUID normalization enforced.

## asset_raw_list

- Route: `GET /api/assets/{asset_id}/raw`
- Handler: `asset_raw_list`
- Query params: `limit`, `offset`
- Canonical response: `{ ok, items[], limit, offset }`
- Guaranteed fields: `ok`, `items`, `limit`, `offset`
- Nullable fields: row-level `payload_jsonb`
- Failures: `400 { ok:false, error:"Invalid request" }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_RAW_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","source":"MANUAL"}],"limit":50,"offset":0}
```
- Regression assertions: asset existence check in org scope before raw read.

## asset_timeline

- Route: `GET /api/assets/{asset_id}/timeline`
- Handler: `asset_timeline`
- Query params: `limit`, `offset`
- Canonical response: `{ ok, items[], limit, offset }`
- Guaranteed fields: `ok`, `items`, `limit`, `offset`
- Nullable fields: `items[].payload`
- Failures: `400 { ok:false, error:"Invalid request" }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_TIMELINE_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"event_type":"raw_ingest","occurred_at":"2026-03-07T16:12:58.522011+00:00"}],"limit":50,"offset":0}
```
- Regression assertions: deterministic newest-first source ordering from `asset_data_raw`.

## asset_snapshot

- Route: `GET /api/assets/{asset_id}/snapshot`
- Handler: `asset_snapshot`
- Query params: none
- Canonical response: `{ ok, asset, links, latest_raw }`
- Guaranteed fields: `ok`, `asset`, `links`
- Nullable fields: `latest_raw`, asset nullable identity fields
- Failures: `400 { ok:false, error:"Invalid request" }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_SNAPSHOT_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset":{"id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179"},"links":[],"latest_raw":null}
```
- Regression assertions: links table fallback supported via `asset_data_raw` evidence.

## asset_audit

- Route: `GET /api/assets/{asset_id}/audit`
- Handler: `asset_audit`
- Query params: `limit`, `offset`, `event_type`
- Canonical response: `{ ok, items[], limit, offset }`
- Guaranteed fields: `ok`, `items`, `limit`, `offset`
- Nullable fields: `items[].payload`
- Failures: `400 { ok:false, error:"Invalid request" }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_AUDIT_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"event_type":"asset_restored","asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","occurred_at":"2026-03-07T20:01:36.319796+00:00"}],"limit":50,"offset":0}
```
- Regression assertions: recognized event normalization preserved (`raw_ingest`, `enrichment_write`, `asset_link_create`, `asset_link_delete`, `asset_archived`, `asset_restored`).

## assets_match

- Route: `POST /api/assets/match`
- Handler: `assets_match`
- Query params: none
- Canonical response: `{ ok, mode, matched, asset_id, candidates[] }`
- Guaranteed fields: `ok`, `mode`
- Nullable fields: `asset_id`, `candidates`
- Failures: `400 { ok:false, error }`, `500 { ok:false, code:"ASSET_MATCH_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"mode":"matched","matched":true,"asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","candidates":[]}
```
- Regression assertions: matching remains org-scoped and deterministic by candidate ordering.

## assets_resolve

- Route: `POST /api/assets/resolve`
- Handler: `assets_resolve`
- Query params: none
- Required headers: `x-altus-org-id: <uuid>`, `Content-Type: application/json`
- Canonical request shape: `{ "asset": { "display_name"?, "address_canonical"?, "apn"?, "clip"?, "asset_type"? } }` with at least one matchable identity key (`display_name`, `address_canonical`, `apn`, `clip`).
- Canonical success response shape: `{ "ok": true, "resolution": "matched|created", "asset_id": "<uuid>", "match_strategy": "<strategy|none>" }`
- Canonical failure response shape: `400 { ok:false, error }`, `500 { ok:false, code:"ASSET_RESOLVE_INTERNAL", error:"Internal server error", status:500 }`
- Guaranteed fields: `ok`, `resolution`, `asset_id`, `match_strategy`
- Nullable fields: none
- Example success payload:
```json
{"ok":true,"resolution":"matched","asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","match_strategy":"apn"}
```
- Regression assertions: accepted route remains live and org-scoped; matched path never creates duplicates and created path emits deterministic `resolution` + `asset_id` + `match_strategy` fields.

## assets_bulk_resolve

- Route: `POST /api/assets/bulk-resolve`
- Handler: `assets_bulk_resolve`
- Query params: none
- Canonical response: `{ ok, items[], summary }`
- Guaranteed fields: `ok`, `items`
- Nullable fields: per item `matched_asset_id`, `created_asset_id`
- Failures: `400 { ok:false, error }`, `500 { ok:false, code:"ASSET_BULK_RESOLVE_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"client_row_id":"row-1","resolution":"matched","asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179"}],"summary":{"matched":1,"created":0}}
```
- Regression assertions: mixed matched/created rows remain supported; deterministic client row echo.

## assets_upsert

- Route: `POST /api/assets/upsert`
- Handler: `assets_upsert`
- Query params: none
- Canonical response: `{ ok, asset_id, status }`
- Guaranteed fields: `ok`, `asset_id`
- Nullable fields: none
- Failures: `400 { ok:false, error }`, `500 { ok:false, code:"ASSET_UPSERT_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset_id":"aa22c3ae-1f62-4074-a832-75f98ebdbe31","status":"ACTIVE"}
```
- Regression assertions: org ownership written on create; update path preserves idempotent identity keys.

## assets_link_create

- Route: `POST /api/assets/link`
- Handler: `assets_link_create`
- Query params: none
- Canonical response: `{ ok, link }`
- Guaranteed fields: `ok`, `link.parent_asset_id`, `link.child_asset_id`, `link.link_type`
- Nullable fields: `link.id`
- Failures: `400 { ok:false, error }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_LINK_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"link":{"id":"dfcf2a8c-6e8b-46a9-a36a-7caa5a27d668","parent_asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","child_asset_id":"54b4bacb-e959-44c5-bdfb-28ba6afc7262","link_type":"structure_deal"}}
```
- Regression assertions: allowed link type guard remains strict; fallback raw evidence remains accepted truth when table missing.

## assets_link_delete

- Route: `DELETE /api/assets/link`
- Handler: `assets_link_delete`
- Query params: none
- Canonical response: `{ ok, deleted }`
- Guaranteed fields: `ok`, `deleted`
- Nullable fields: none
- Failures: `400 { ok:false, error }`, `404 { ok:false, code:"LINK_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_LINK_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"deleted":true}
```
- Regression assertions: delete evidence emitted for fallback model; deterministic link key matching.

## asset_archive

- Route: `POST /api/assets/{asset_id}/archive`
- Handler: `asset_archive`
- Query params: none
- Canonical response: `{ ok, asset_id, status }`
- Guaranteed fields: `ok`, `asset_id`, `status`
- Nullable fields: none
- Failures: `400 { ok:false, error }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_DELETE_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","status":"ARCHIVED"}
```
- Regression assertions: lifecycle evidence row `ASSET_ARCHIVE::` emitted in `asset_data_raw`.

## asset_restore

- Route: `POST /api/assets/{asset_id}/restore`
- Handler: `asset_restore`
- Query params: none
- Canonical response: `{ ok, asset_id, status }`
- Guaranteed fields: `ok`, `asset_id`, `status`
- Nullable fields: none
- Failures: `400 { ok:false, error }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_RESTORE_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","status":"ACTIVE"}
```
- Regression assertions: lifecycle evidence row `ASSET_RESTORE::` emitted in `asset_data_raw`.

## asset_delete

- Route: `DELETE /api/assets/{asset_id}`
- Handler: `asset_delete`
- Query params: none
- Canonical response: `{ ok, asset_id, deleted }`
- Guaranteed fields: `ok`, `asset_id`, `deleted`
- Nullable fields: none
- Failures: `400 { ok:false, error }`, `404 { ok:false, code:"ASSET_NOT_FOUND" }`, `500 { ok:false, code:"ASSET_DELETE_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset_id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","deleted":true}
```
- Regression assertions: delete evidence row written when configured path requires audit trail.

## assets_export

- Route: `GET /api/assets/export`
- Handler: `assets_export`
- Query params: `format`, `limit`, `offset`, `status`, `asset_type`, `q`
- Canonical response:
  - JSON: `{ ok, items[], limit, offset, format:"json" }`
  - CSV: text/csv rows with canonical columns
- Guaranteed fields: JSON mode includes `ok`, `items`, `limit`, `offset`, `format`
- Nullable fields: exported identity fields may be null
- Failures: `400 { ok:false, error:"Invalid request" }`, `500 { ok:false, code:"ASSET_EXPORT_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"items":[{"id":"7c9d0ddf-7de7-4e5d-8fda-a6e2e56d6179","status":"ACTIVE"}],"limit":1000,"offset":0,"format":"json"}
```
- Regression assertions: search filter uses `display_name` and `address_canonical` only.

## assets_overview

- Route: `GET /api/assets/overview`
- Handler: `assets_overview`
- Query params: `recent_limit` (default 5, max 20)
- Canonical response: `{ ok, summary, recent_created[], recent_changed[], recent_audit_assets[], recent_limit }`
- Guaranteed fields: `ok`, `summary.total_assets`, `summary.active_assets`, `summary.archived_assets`, `summary.linked_assets`, `summary.assets_with_recent_audit`, `recent_limit`
- Nullable fields: `display_name` in lists
- Failures: `400 { ok:false, error:"Invalid request" }`, `500 { ok:false, code:"ASSET_OVERVIEW_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"summary":{"total_assets":16,"active_assets":16,"archived_assets":0,"linked_assets":2,"assets_with_recent_audit":2},"recent_created":[],"recent_changed":[],"recent_audit_assets":[],"recent_limit":5}
```
- Regression assertions: deterministic ordering (`created_at.desc,id.desc`, `updated_at.desc,id.desc`, audit `occurred_at.desc,asset_id.desc`).

## assets_metrics

- Route: `GET /api/assets/metrics`
- Handler: `assets_metrics`
- Query params: `window_days` (default 7, max 90)
- Canonical response: `{ ok, metrics, window_days }`
- Guaranteed fields: `ok`, all `metrics.*` fields, `window_days`
- Nullable fields: none
- Failures: `400 { ok:false, error:"Invalid request" }`, `500 { ok:false, code:"ASSET_METRICS_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"metrics":{"total_assets":16,"active_assets":16,"archived_assets":0,"created_in_window":16,"updated_in_window":16,"assets_with_audit_in_window":2,"linked_assets":2},"window_days":7}
```
- Regression assertions: no raw rows exposed in success payload; audit/link counts honor fallback evidence model.

## assets_ingest

- Route: `POST /api/assets/ingest`
- Handler: `assets_ingest`
- Query params: none
- Canonical response: `{ ok, asset_id, status, source }`
- Guaranteed fields: `ok`, `asset_id`
- Nullable fields: optional enrichment fields in payload source record
- Failures: `400 { ok:false, error }`, `500 { ok:false, code:"INGEST_INTERNAL", error:"Internal server error", status:500 }`
- Example payload:
```json
{"ok":true,"asset_id":"0f0a9bf7-3c24-45eb-b8e8-24ee361791e0","status":"ACTIVE","source":"MANUAL"}
```
- Regression assertions: canonicalization/hash path remains deterministic; raw ingest evidence stored in `asset_data_raw`.

