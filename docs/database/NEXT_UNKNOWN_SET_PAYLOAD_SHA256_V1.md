# NEXT UNKNOWN SET: ASSET_DATA_RAW.PAYLOAD_SHA256 V1

## Chosen Unknown Set

`public.asset_data_raw.payload_sha256`

## Why This Comes Next

- `payload_sha256` is narrower than `source_record_id` because it focuses on one runtime-written field with a clear, testable claim: whether a durable hash column actually exists or whether the hash only lives in application logic.
- Prior staging proof already showed `payload_sha256` is absent from the proven live `asset_data_raw` shape, so the next task is to verify whether that absence is complete and intentional rather than mixed or drifting.
- This unknown is safer to resolve before `asset_specs_reconciled` because it is local to the already-proven canonical `asset_data_raw` baseline and does not require broader product-contract interpretation.
- Resolving `payload_sha256` first will also make the later `source_record_id` question easier, because both currently sit in the same runtime-only write path.

## Required Proof Before Any Canonicalization

The next Database-lane proof task must establish:

1. whether `public.asset_data_raw.payload_sha256` exists anywhere in staging
2. whether any similarly named hash column or generated field exists under a different name
3. whether staged raw rows already encode equivalent hash material only inside `payload_jsonb`
4. whether the runtime expectation is pure application drift or a missing schema/backfill obligation
5. whether any index, constraint, trigger, or view depends on hash-style raw-record identity today

Proof should start with non-destructive staging inspection plus current repo-code review only.

## Likely Next Move

Additional staging proof.

Reason:
- current evidence only shows the column was not present in the earlier focused staging proof
- docs reconciliation or schema migration would be premature until staging inspection proves whether there is true absence, alternate representation, or adjacent dependency
- the next safe step is to inspect staged `asset_data_raw` structure and hash-like data patterns directly

## Issue-Ready Scope

Title:
- `DB: prove asset_data_raw.payload_sha256 intent in staging`

In scope:
- add non-destructive verification SQL for `public.asset_data_raw.payload_sha256` or equivalent hash representation
- inspect `asset_data_raw` columns, hash-like keys inside `payload_jsonb`, and any relevant dependencies
- compare staged findings with the current ingest write behavior
- update DB docs only if proof justifies it

Out of scope:
- adding `payload_sha256`
- changing runtime writes
- resolving `source_record_id` in the same task
- resolving `asset_specs_reconciled` extra-column semantics in the same task

## Success Condition

- staging proof shows whether `payload_sha256` is truly absent, represented elsewhere, or depended on indirectly
- the follow-up DB task can then choose one explicit path:
  - verification-only closure if the field is runtime-only drift
  - docs reconciliation if an equivalent staged representation already exists
  - schema migration only if proof shows a missing governed persistence requirement
