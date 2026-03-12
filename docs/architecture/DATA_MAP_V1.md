# DATA_MAP_V1

Status: active discovery baseline

This document maps the durable and non-durable backend data surfaces currently discoverable on `origin/main`. It is intentionally conservative: if a storage read or write was not evident in code or migrations, it is marked as unknown rather than assumed.

## Data Plane Summary

| Surface | Type | Source of Truth Status | Evidence |
|---|---|---|---|
| Supabase `assets` | Durable table | Confirmed write target | `assets_ingest` posts to `/rest/v1/assets` |
| Supabase `asset_data_raw` | Durable table | Confirmed write target | `assets_ingest` posts to `/rest/v1/asset_data_raw` |
| Supabase `asset_specs_reconciled` | Durable table | Declared in docs/migrations, no live runtime usage discovered | Mentioned in architecture docs and migrations |
| Supabase identity/org tables | Durable tables | Schema present, no route usage discovered in current runtime | `organizations`, `profiles`, `organization_members` in migrations |
| ECC service payloads | In-code generated data | Not a system of record | `ecc_*_service.py` files generate deterministic payloads |
| Price engine result payload | In-code calculation | Not persisted | `price_engine_service.py` returns computed values |

## Route-to-Data Map

| Route | Read Path | Write Path | External Dependency | Proof Level |
|---|---|---|---|---|
| `POST /api/assets/ingest` | Request body only | `assets`, then `asset_data_raw` via Supabase REST | Azure Key Vault, Managed Identity, Supabase | High: changes here should carry request/response proof and write-path validation |
| `GET /api/ecc/portfolio/summary` | None discovered beyond query params | None discovered | None discovered in current implementation | Medium: contract proof required, storage claims prohibited unless implementation changes |
| `GET /api/ecc/portfolio/assets` | None discovered beyond query params | None discovered | None discovered in current implementation | Medium |
| `GET /api/ecc/assets/search` | None discovered beyond query params | None discovered | None discovered in current implementation | Medium |
| `GET /api/ecc/assets/metrics` | None discovered beyond query params | None discovered | None discovered in current implementation | Medium |
| `GET /api/ecc/system/health` | None discovered | None discovered | None discovered in current implementation | Low to medium; do not market as live infra health without implementation proof |
| `POST /api/price-engine/calculate` | Request body only | None discovered | None discovered in current implementation | Medium: calculation and validation proof required |

## Durable Schema Surfaces Discovered

### `supabase/migrations/0001_enterprise_asset_master.sql`

- Creates or defines the enterprise asset master baseline.
- Observed core tables:
  - `assets`
  - `asset_data_raw`
  - `asset_specs_reconciled`

### `supabase/migrations/0002_altus_core_identity.sql`

- Introduces identity and org membership scaffolding.
- Observed core tables:
  - `organizations`
  - `profiles`
  - `organization_members`
- Also defines or redefines:
  - `assets`
  - `asset_data_raw`

### `supabase/migrations/0003_altus_is_org_member_service_role.sql`

- Adjusts membership function behavior to allow `service_role`.

## Runtime Secret and Dependency Path

`assets_ingest` is the only discovered path that requires runtime credentials.

| Dependency | How It Is Resolved | Where Observed |
|---|---|---|
| Azure Managed Identity | `ManagedIdentityCredential()` | `function_app.py` |
| Azure Key Vault | `KEY_VAULT_URL` env var, defaulting to staging vault URL | `function_app.py` |
| Supabase URL | Secret name from `SUPABASE_URL_SECRET_NAME`, default `SUPABASE_URL` | `function_app.py` |
| Supabase service role key | Secret name from `SUPABASE_SERVICE_ROLE_KEY_SECRET_NAME`, default `SUPABASE_SERVICE_ROLE_KEY` | `function_app.py` |

## Known Drift / Unknowns

- Migration drift exists between `0001` and `0002` for `asset_data_raw`:
  - `0001` references `payload_jsonb` and `fetched_at`
  - `0002` references `payload`, `organization_id`, and `created_at`
- Migration drift also exists in the surrounding `assets` table context across `0001` and `0002`.
- No runtime read path into `asset_specs_reconciled` was discovered.
- No repository-local test or contract fixture was found that proves ECC payloads are backed by a persistent source.
- No deployment-time check was found that proves Supabase schema and Azure Function runtime are in sync.

## Governance Implications

- Backend tasks must distinguish between:
  - contract-only changes
  - calculation-only changes
  - durable write-path changes
- Durable write-path changes require a stronger proof pack than deterministic in-code response changes.
- Claims about production data sources are not allowed unless the corresponding runtime read/write path is shown in code and reflected here.
