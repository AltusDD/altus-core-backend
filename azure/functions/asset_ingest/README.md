# Asset Ingest Azure Function

## Endpoint

- Method: `POST`
- Route: `/api/assets/ingest`
- Required header: `x-altus-org-id` (UUID)

## Request Body

```json
{
  "source": "CORELOGIC|MLS|DOORLOOP|MANUAL|OTHER",
  "asset": {
    "name": "optional",
    "asset_type": "optional",
    "status": "optional"
  },
  "raw": {}
}
```

## Behavior

- Validates `x-altus-org-id` as UUID.
- Validates `source` and `raw` payload.
- Canonicalizes `raw` using stable JSON and computes `sha256` as `payload_hash`.
- Inserts into `public.assets`.
- Inserts into `public.asset_data_raw`.

## Runtime Secrets (Key Vault via Managed Identity)

The function reads secrets at runtime from Key Vault:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Required app settings:

- `KEY_VAULT_URL`
- `SUPABASE_URL_SECRET_NAME` (default `SUPABASE_URL`)
- `SUPABASE_SERVICE_ROLE_KEY_SECRET_NAME` (default `SUPABASE_SERVICE_ROLE_KEY`)

## Success Response

```json
{ "ok": true, "asset_id": "<uuid>", "raw_id": "<uuid>", "payload_hash": "<hex>" }
```
