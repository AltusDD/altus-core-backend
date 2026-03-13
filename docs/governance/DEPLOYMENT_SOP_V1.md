# DEPLOYMENT SOP V1

## Purpose

Define the safe apply path for governed DB changes.

## Supabase Apply Path

1. Merge or prepare the governed PR only after `db_proof_gate.yml` passes.
2. Run `.github/workflows/supabase_apply.yml`.
3. Keep `target=staging` unless an authorized production promotion is intended.
4. Let the workflow:
   - resolve secrets from GitHub Secrets only
   - apply repo migrations
   - run verification SQL
   - upload proof artifacts
5. Review staging proof before any production promotion.
6. Run production only through the protected `production` environment.

## Required Secrets

- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_STAGING_PROJECT_REF`
- `SUPABASE_STAGING_DB_PASSWORD`
- `SUPABASE_PROD_PROJECT_REF`
- `SUPABASE_PROD_DB_PASSWORD`

## Safety Rules

- Production is never the default target.
- Secrets must not be echoed or committed.
- Destructive migrations remain out of scope unless separately approved.
- Runtime handlers are not modified by this governance install.
