# DATA_MAP_V1

Canonical runtime owner: `azure/functions/asset_ingest/function_app.py`

## DB Governance Overlay

- Repository artifacts are authoritative for governed DB work.
- Dashboard-only schema changes are not authoritative until they are backfilled into repo truth.
- DB tasks that change canonical ownership, fallback authority, or contract-facing data sources must update this map in the same PR.
- Unknown live schema state must be labeled as unknown until verified by proof or repository artifacts.

## Persistence Authority

- `assets` is canonical for current asset state (`status`, identity fields, timestamps).
- `asset_data_raw` is canonical event/evidence stream for ingest/audit/timeline and for fallback link/lifecycle evidence.
- `asset_links` is optional fast-path table; when unavailable, runtime falls back to `asset_data_raw` evidence.

## Endpoint to Source-of-Truth Mapping

| Endpoint | Primary Source | Fallback Source | Notes |
|---|---|---|---|
| `GET /api/assets` | `assets` | none | Default excludes `ARCHIVED` unless explicit filter. |
| `GET /api/assets/search` | `assets` | none | Search on `display_name` + `address_canonical`. |
| `GET /api/assets/{id}` | `assets` + `asset_data_raw` + links | `asset_data_raw` for links | Detail hydrates latest raw + relationships. |
| `GET /api/assets/{id}/raw` | `asset_data_raw` | none | Requires asset existence in org scope first. |
| `GET /api/assets/{id}/timeline` | `asset_data_raw` | none | Event type normalization from row source/payload. |
| `GET /api/assets/{id}/snapshot` | `assets` + links + `asset_data_raw` | `asset_data_raw` links | Snapshot combines current state + relationship view. |
| `GET /api/assets/{id}/audit` | `asset_data_raw` | none | Recognized event families normalized in handler. |
| `POST /api/assets/match` | `assets` | none | Candidate selection in org scope. |
| `POST /api/assets/resolve` | `assets` (+ insert on create path) | none | Accepted live resolve surface with matched/created semantics. |
| `POST /api/assets/bulk-resolve` | `assets` (+ insert) | none | Per-row match or create semantics. |
| `POST /api/assets/upsert` | `assets` (+ optional raw evidence) | none | Creates/updates state row. |
| `POST /api/assets/link` | `asset_links` | `asset_data_raw` (`ASSET_LINK::`) | Fallback evidence row emitted when link table unavailable. |
| `DELETE /api/assets/link` | `asset_links` | `asset_data_raw` (`ASSET_LINK_DELETE::`) | Fallback delete evidence row. |
| `POST /api/assets/{id}/archive` | `assets` status update | `asset_data_raw` evidence | Emits lifecycle evidence `ASSET_ARCHIVE::...`. |
| `POST /api/assets/{id}/restore` | `assets` status update | `asset_data_raw` evidence | Emits lifecycle evidence `ASSET_RESTORE::...`. |
| `DELETE /api/assets/{id}` | `assets` delete/soft-delete path | `asset_data_raw` evidence | Emits delete evidence where implemented. |
| `GET /api/assets/export` | `assets` | none | JSON/CSV export over canonical state. |
| `GET /api/assets/overview` | `assets` + link/audit derivation | `asset_data_raw` for link/audit fallback | Summary + deterministic recent slices. |
| `GET /api/assets/metrics` | `assets` + windowed audit/link derivation | `asset_data_raw` for link/audit fallback | Compact metrics only, no raw row payloads. |
| `POST /api/assets/ingest` | `assets` + `asset_data_raw` | none | State row + raw source evidence write path. |

## Explicit Fallback Authority Notes

### Link Relationship Evidence

- Preferred: `asset_links` table.
- Fallback truth: `asset_data_raw` rows where:
  - create evidence: `source` prefixed `ASSET_LINK::` or `payload_jsonb.record_type == "asset_link"`
  - delete evidence: `source` prefixed `ASSET_LINK_DELETE::` or `payload_jsonb.record_type == "asset_link_delete"`

### Audit / Timeline Evidence

- Source of truth: `asset_data_raw` rows ordered deterministically.
- Recognized normalized event families:
  - `raw_ingest`
  - `enrichment_write`
  - `asset_link_create`
  - `asset_link_delete`
  - `asset_archived`
  - `asset_restored`

### Lifecycle Evidence

- Archive evidence source prefix: `ASSET_ARCHIVE::`
- Restore evidence source prefix: `ASSET_RESTORE::`
- Delete evidence source prefix: `ASSET_DELETE::`

