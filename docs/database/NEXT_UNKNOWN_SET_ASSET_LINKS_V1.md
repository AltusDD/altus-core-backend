# NEXT UNKNOWN SET: ASSET_LINKS V1

## Chosen Unknown Set

`asset_links`

## Why This Comes First

- `asset_links` is the safest remaining unknown because the canonical baseline for `assets`, `asset_data_raw`, and `public.assets` policies is already proven in staging.
- `docs/architecture/DATA_MAP_V1.md` already treats `asset_links` as optional fast-path authority with explicit `asset_data_raw` fallback evidence, so the unresolved question is existence and authority, not a proven live mismatch inside the canonical baseline.
- This unknown can be reduced with non-destructive proof first, without requiring runtime changes or immediate schema mutation.
- Resolving `asset_links` first lowers uncertainty around detail, snapshot, and link lifecycle surfaces without reopening the now-settled `asset_data_raw` and `assets` reconciliation work.

## Required Proof Before Any Schema Change

The next Database-lane proof task must answer these questions in staging:

1. Does `public.asset_links` exist?
2. If it exists, what columns are actually present?
3. If it exists, are any indexes, foreign keys, or unique constraints present?
4. If it exists, is RLS enabled?
5. If it exists, what policies are active?
6. If it does not exist, is `asset_data_raw` fallback evidence the only live authority for link lifecycle events?

Proof should be collected through non-destructive verification SQL only.

## Likely Resolution Class

Staged reconciliation proof first.

Reason:
- No repository migration on `main` currently proves `asset_links`.
- No current staging proof run queried `asset_links` directly.
- A schema-changing PR would be premature until the repo knows whether the table is absent, present-but-untracked, or present with policy drift.

## Issue-Ready Scope

Title:
- `DB: prove asset_links authority in staging`

In scope:
- add non-destructive verification SQL for `public.asset_links`, related constraints, and related policies
- run `supabase_apply.yml` against `staging`
- record whether `asset_links` is authoritative, absent, or tolerated live drift
- update DB docs only if the proof justifies it

Out of scope:
- creating `asset_links`
- deleting `asset_links`
- modifying runtime handlers
- resolving `payload_sha256`, `source_record_id`, `external_ids`, or `asset_specs_reconciled` semantics

## Success Condition

- staging proof establishes whether `asset_links` exists and whether it carries active policy/constraint authority
- repo docs can then choose one follow-up path:
  - verification-only closure if `asset_links` is absent and fallback evidence remains canonical
  - repo doc reconciliation if `asset_links` exists but is intentionally tolerated
  - schema migration if `asset_links` should become governed canonical repo truth
