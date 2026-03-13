# Supabase Verification

Place post-apply verification SQL here.

Rules:

- One or more `.sql` files are required when a PR claims a schema change.
- Verification SQL must be safe to run after the migration completes.
- Verification output is captured by `.github/workflows/supabase_apply.yml`.
- Rollback guidance lives in PR metadata and supporting docs, not in dashboard-only notes.
