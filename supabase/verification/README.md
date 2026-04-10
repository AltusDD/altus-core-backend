# Supabase Verification

This folder is the canonical home for post-apply schema and RLS verification SQL.

Rules:

- Add verification `.sql` files here when a PR introduces schema or policy changes.
- Keep verification read-safe and suitable for post-apply proof gathering.
- Do not use request-serving runtime code as a substitute for schema governance evidence.
- If no schema or policy change is made, a documentation-only note here is sufficient.
