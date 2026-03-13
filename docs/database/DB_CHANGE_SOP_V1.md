# DB CHANGE SOP V1

## Purpose

Standard operating procedure for governed DB changes in this repo.

## Steps

1. Open a DB issue
   - Use the Supabase or general DB issue template.
   - Record risk, affected objects, rollback note, and unknowns.
2. Generate artifacts in repo
   - Schema changes require a migration file.
   - Validation requires verification SQL.
   - Contract or source-of-truth changes require doc updates.
3. Open a proof-bearing PR
   - Fill in the DB proof metadata block from `.github/pull_request_template.md`.
   - List exact files changed, workflows changed, docs changed, secrets required, and unknowns.
4. Pass the DB proof gate
   - Schema change claims require a migration file.
   - Schema change claims require verification SQL.
   - Changed objects must be documented.
   - Rollback note must be present.
   - `docs/architecture/DATA_MAP_V1.md` must change when contracts or data ownership change.
5. Apply to staging
   - Use `.github/workflows/supabase_apply.yml`.
   - Staging is the default target.
   - Verification SQL must run after apply.
6. Promote to production only when authorized
   - Production is manual and non-default.
   - Use protected GitHub environment rules and reviewers.

## Required Repository Locations

- Supabase migrations: `supabase/migrations/`
- Supabase verification SQL: `supabase/verification/`
- DB governance docs: `docs/database/`
- Contract references: `docs/contracts/`
- Governance gates and deploy SOPs: `docs/governance/`

## Rollback Notes

Every DB task must carry a rollback note that states:

- which migration or object change is being reversed
- whether rollback is SQL-based, operational, or restore-based
- which verification query proves the rollback state
- any irreversible or data-loss risk

## Secrets

The current Supabase apply workflow expects these GitHub secrets:

- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_STAGING_PROJECT_REF`
- `SUPABASE_STAGING_DB_PASSWORD`
- `SUPABASE_PROD_PROJECT_REF`
- `SUPABASE_PROD_DB_PASSWORD`

These are documented only. No values belong in repo history or issues.

## Non-Authoritative Changes

Dashboard-only changes are not authoritative.

If an operator uses the dashboard for emergency or exploratory work, the authoritative state must be backfilled into:

- repo migration artifacts
- verification SQL
- related contract or map docs
- PR proof metadata
