# NEXT UNKNOWN SET: ASSET_DATA_RAW.SOURCE_RECORD_ID V1

## Chosen Unknown Set

`public.asset_data_raw.source_record_id`

## Why This Comes Next

- `source_record_id` is the last narrow runtime-only field on the already-proven `asset_data_raw` surface, so it is safer to resolve before widening into the broader semantic question around `asset_specs_reconciled` extra live columns.
- Current runtime code explicitly writes `source_record_id: None`, which means the next question is not broad product meaning but whether any live staging schema or data pattern actually supports the field at all.
- The `payload_sha256` proof already reduced the adjacent raw-ingest uncertainty, so `source_record_id` is now the cleanest remaining single-field proof target.
- Resolving this field first will leave the remaining `asset_specs_reconciled` work as a separate, intentionally broader semantics task rather than mixing narrow runtime drift with multi-column modeling decisions.

## Required Proof Before Any Canonicalization

The next Database-lane proof task must establish:

1. whether `public.asset_data_raw.source_record_id` exists in staging
2. whether any similarly named source identifier column exists under a different name
3. whether equivalent source-record identity currently appears inside `public.asset_data_raw.payload_jsonb`
4. whether any asset-ingest-adjacent table, view, or constraint carries source-record identity today
5. whether the runtime expectation is true schema drift, equivalent representation elsewhere, or unsupported runtime-only expectation

Proof should start with non-destructive staging inspection plus current repo-code review only.

## Likely Next Move

Additional staging proof.

Reason:
- current evidence only shows a runtime write expectation with `None`, not a proven live schema field
- docs reconciliation or schema migration would be premature until staging inspection proves absence, alternate representation, or adjacent dependency
- the next safe step is to inspect staged raw-record structure and source-identifier patterns directly

## Issue-Ready Scope

Title:
- `DB: prove asset_data_raw.source_record_id intent in staging`

In scope:
- add non-destructive verification SQL for `public.asset_data_raw.source_record_id` or equivalent source-identity representation
- inspect `asset_data_raw` columns, likely source-id keys inside `payload_jsonb`, and any relevant dependencies
- compare staged findings with current ingest write behavior
- update DB docs only if proof justifies it

Out of scope:
- adding `source_record_id`
- changing runtime writes
- resolving `asset_specs_reconciled` extra-column semantics in the same task

## Success Condition

- staging proof shows whether `source_record_id` is truly absent, represented elsewhere, or depended on indirectly
- the follow-up DB task can then choose one explicit path:
  - verification-only closure if the field is runtime-only drift
  - docs reconciliation if an equivalent staged representation already exists
  - schema migration only if proof shows a missing governed persistence requirement
