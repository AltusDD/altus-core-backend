# DATA_MAP_V1

Canonical runtime owner: `azure/functions/asset_ingest/function_app.py`

## DB Governance Overlay

- Repository artifacts are authoritative for governed DB work.
- Dashboard-only schema changes are not authoritative until they are backfilled into repo truth.
- DB tasks that change canonical ownership, fallback authority, or contract-facing data sources must update this map in the same PR.
- Unknown live schema state must be labeled as unknown until verified by proof or repository artifacts.
- Current repository-grounded schema inventory authority: `docs/database/SCHEMA_INVENTORY_V1.md`.

## Current Repo-Proven Schema Caveats

- `public.assets`, `public.asset_data_raw`, and `public.asset_specs_reconciled` were each defined more than once in historical migrations, so canonical repo truth must follow the latest approved reconciliation layer rather than the oldest definition.
- `supabase/migrations/0004_reconcile_assets_asset_data_raw_canonical_baseline.sql` is the current reconciliation layer for the decided `assets` and `asset_data_raw` mismatch areas.
- `asset_links` is referenced below as a potential future fast-path relationship table, but staging proof run `23066495260` confirmed it is not present in staging and no migration on `main` currently proves it exists.
- `public.assets.external_ids` is now proven in staging as a live `jsonb` object field with default `{}` and observed `payload_hash` key usage; staging proof run `23069329492` also confirmed `public.asset_data_raw.payload_sha256` is absent and that the current proven equivalent hash representation lives in `public.assets.external_ids.payload_hash`; semantic redesign remains deferred, while staging proof run `23073428262` confirmed `asset_data_raw.source_record_id` is absent and no equivalent source-record identity field is currently proven elsewhere.
- Staging proof run `23061749612` confirmed `assets.display_name` exists, confirmed `asset_data_raw` follows the `payload_jsonb` / `fetched_at` shape, and did not prove policy `assets_org_isolation` as active.
- Staging proof run `23090151849` structurally proved the broader `asset_specs_reconciled` shape, including extra live columns for versioning, provenance, and effective-dating support, but staging currently has zero rows so live semantic usage is not yet proven.

## Persistence Authority

- `assets` is canonical for current asset state (`status`, identity fields, timestamps), with `display_name` as the current reconciled presentation field.
- `asset_data_raw` is canonical event/evidence stream for ingest/audit/timeline and for fallback link/lifecycle evidence, using the reconciled `payload_jsonb` / `fetched_at` baseline.
- `asset_links` is not part of the current canonical staging baseline; `asset_data_raw` fallback evidence is the authoritative link source until a future explicit schema proposal introduces a governed link table.

## Endpoint to Source-of-Truth Mapping

| Endpoint | Primary Source | Fallback Source | Notes |
|---|---|---|---|
| `GET /api/assets` | `assets` | none | Current reconciled baseline treats `display_name` as the authoritative presentation field and leaves legacy `name` non-canonical. |
| `GET /api/assets/search` | `assets` | none | Intended search fields include `display_name` and `address_canonical`; `display_name` is now part of the reconciled repo baseline on this branch. |
| `GET /api/assets/{id}` | `assets` + `asset_data_raw` + link evidence | `asset_data_raw` for links | Detail hydration intent remains authoritative; staging proof confirmed `asset_links` is absent, so link authority currently comes from `asset_data_raw` evidence only. |
| `GET /api/assets/{id}/raw` | `asset_data_raw` | none | Current reconciled baseline is `payload_jsonb` + `fetched_at`. |
| `GET /api/assets/{id}/timeline` | `asset_data_raw` | none | Event type normalization from row source/payload. |
| `GET /api/assets/{id}/snapshot` | `assets` + link evidence + `asset_data_raw` | `asset_data_raw` links | Snapshot combines current state + relationship view; staging proof confirmed `asset_links` is absent, so link authority currently comes from `asset_data_raw` evidence only. |
| `GET /api/assets/{id}/audit` | `asset_data_raw` | none | Recognized event families normalized in handler. |
| `POST /api/assets/match` | `assets` | none | Candidate selection in org scope. |
| `POST /api/assets/resolve` | `assets` (+ insert on create path) | none | Accepted live resolve surface with matched/created semantics. |
| `POST /api/assets/bulk-resolve` | `assets` (+ insert) | none | Per-row match or create semantics. |
| `POST /api/assets/upsert` | `assets` (+ optional raw evidence) | none | Creates/updates state row. |
| `POST /api/assets/link` | `asset_data_raw` (`ASSET_LINK::`) | none | Staging proof confirmed `asset_links` is absent, so link creation authority currently lands in fallback evidence rows only. |
| `DELETE /api/assets/link` | `asset_data_raw` (`ASSET_LINK_DELETE::`) | none | Staging proof confirmed `asset_links` is absent, so link delete authority currently lands in fallback evidence rows only. |
| `POST /api/assets/{id}/archive` | `assets` status update | `asset_data_raw` evidence | Emits lifecycle evidence `ASSET_ARCHIVE::...`. |
| `POST /api/assets/{id}/restore` | `assets` status update | `asset_data_raw` evidence | Emits lifecycle evidence `ASSET_RESTORE::...`. |
| `DELETE /api/assets/{id}` | `assets` delete/soft-delete path | `asset_data_raw` evidence | Emits delete evidence where implemented. |
| `GET /api/assets/export` | `assets` | none | JSON/CSV export over canonical state. |
| `GET /api/assets/overview` | `assets` + link/audit derivation | `asset_data_raw` for link/audit fallback | Summary + deterministic recent slices. |
| `GET /api/assets/metrics` | `assets` + windowed audit/link derivation | `asset_data_raw` for link/audit fallback | Compact metrics only, no raw row payloads. |
| `POST /api/assets/ingest` | `assets` + `asset_data_raw` | none | Reconciled repo baseline aligns `assets.display_name`, staging-proven `assets.external_ids` as a `jsonb` object field with default `{}` and observed `payload_hash` usage, plus `asset_data_raw.payload_jsonb` / `fetched_at`; `asset_data_raw.payload_sha256` is not part of the current live staging schema, `asset_data_raw.source_record_id` is also absent with no proven equivalent field elsewhere, and no redesign is proposed here. |

## Explicit Fallback Authority Notes

### Link Relationship Evidence

- Current canonical authority: `asset_data_raw` evidence because staging proof run `23066495260` confirmed `asset_links` is absent.
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




