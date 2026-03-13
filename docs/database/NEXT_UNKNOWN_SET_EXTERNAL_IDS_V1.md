# NEXT UNKNOWN SET: ASSETS.EXTERNAL_IDS V1

## Chosen Unknown Set

`public.assets.external_ids`

## Why This Comes Next

- `external_ids` is already proven present in staging, unlike `payload_sha256` and `source_record_id`, which are still absent from the proven staging schema.
- Current runtime code already writes `external_ids` on asset ingest, so this unknown is about semantic intent and canonical ownership rather than first proving table existence.
- Resolving `external_ids` next is safer than `asset_specs_reconciled` extra columns because it is narrower, asset-local, and less likely to hide broader product-contract drift.
- This unknown can be reduced with staged proof and contract clarification before any schema or documentation canonicalization decision is made.

## Required Proof Before Any Canonicalization

The next Database-lane proof task must establish:

1. what actual values are stored in `public.assets.external_ids` in staging
2. whether the column is consistently JSON-shaped and what keys are used in practice
3. whether `payload_hash` is the only active semantic currently written
4. whether any other producers or historical rows use alternate key shapes
5. whether the field is serving as durable external identity, ingest bookkeeping, or transitional runtime convenience only

Proof should start with non-destructive staging inspection plus current repo-code review only.

## Likely Next Move

Additional staging proof.

Reason:
- the column exists, but meaning is not yet canonical
- a docs reconciliation or schema migration would be premature before proving real staged values and usage shape
- the next safe step is to inspect staged contents and then decide whether the field should remain tolerated, be documented canonically, or be redesigned later

## Issue-Ready Scope

Title:
- `DB: prove assets.external_ids semantic intent in staging`

In scope:
- add non-destructive verification SQL for `public.assets.external_ids`
- capture staged value shape, key usage, and null/non-null prevalence
- compare staged findings with current ingest write behavior
- update DB docs only if proof justifies it

Out of scope:
- renaming `external_ids`
- changing runtime writes
- introducing migrations
- resolving `payload_sha256`, `source_record_id`, or `asset_specs_reconciled` semantics in the same task

## Success Condition

- staging proof shows the real value shape and practical role of `external_ids`
- the follow-up DB task can then choose one explicit path:
  - verification-only closure if it is transitional and should remain tolerated
  - docs reconciliation if the current meaning is stable enough to canonize
  - schema migration only if staged proof and contract review show the field must be redesigned
