# ECC PORTFOLIO SUMMARY COHORT MAPPING SLICE V1

## Purpose

Define the next bounded Core-only slice for `GET /api/ecc/portfolio/summary` after the initial cohort-resolver seam shipped on `main`.

This slice exists to prove the smallest persistent `portfolioId` to asset cohort mapping path that can support additional safe summary backing without changing the public contract, widening to other routes, or removing deterministic fallback behavior.

## Current Runtime State

- Route entrypoint: `azure/functions/asset_ingest/function_app.py`
- Handler: `azure/functions/asset_ingest/ecc_portfolio_summary_handler.py`
- Service: `azure/functions/asset_ingest/ecc_portfolio_summary_service.py`
- Public contract baseline: `docs/contracts/ECC_PORTFOLIO_SUMMARY_CONTRACT_V1.md`
- Current backing seam status:
  - public response shape unchanged
  - deterministic fallback remains the default path
  - read-only backing can currently override `assetCount` only when an explicit cohort-resolution mode is configured

## Governing Constraints

- No schema migrations
- No deploy target changes
- No widening into `portfolio/assets`, `assets/search`, `assets/metrics`, or any other route
- No public contract drift
- No fallback removal
- Read-only persistence access only

## Smallest Repo-Grounded Persistence Source

### Primary Candidate

`public.assets.external_ids`

Why this is the smallest grounded source:

- `docs/architecture/DATA_MAP_V1.md` and `docs/database/SCHEMA_INVENTORY_V1.md` already treat `public.assets` as the canonical current-state asset table.
- Staging proof recorded in `docs/database/SCHEMA_INVENTORY_V1.md` proves `public.assets.external_ids` exists as a `jsonb` object field with default `{}`.
- Current runtime already writes `payload_hash` into `assets.external_ids`, so this field is proven to carry structured external identity material in the canonical asset table.
- A configurable `external_ids` key allows route-scoped cohort resolution without inventing a new table or schema shape.

### Deferred Candidates

- `public.asset_specs_reconciled`
  - not a cohort authority by itself
  - only becomes useful for additional fields after cohort membership is proven
- `public.asset_data_raw`
  - raw evidence stream only
  - not the first safe authority for direct portfolio cohort membership

## Required Proof Before Activating Additional Backed Fields

The next execution PR must prove all of the following before any additional field moves off deterministic fallback:

1. A single configurable `external_ids` key can map `portfolioId` to the intended asset cohort in a read-only way.
2. Missing mapping data returns deterministic fallback rather than partial or broken backed output.
3. Ambiguous or multi-key mapping remains fallback-only until the route has explicit proof for resolution rules.
4. The public response shape remains byte-for-byte compatible with the current contract fixture structure.

## Safest First Execution Slice

Implement a route-scoped read-only cohort mapping activation that does all of the following:

- keeps `assetCount` as the only live backed field
- treats `public.assets.external_ids[<configured_key>] == portfolioId` as the only allowed persistent cohort mapping rule
- refuses to infer cohort membership from names, addresses, free text, or other unproven fields
- returns deterministic fallback when:
  - the mapping key is unset
  - the mapping key is absent on matching rows
  - the query errors
  - the result shape is incomplete or untrusted

## Additional Fields Explicitly Deferred

These remain deterministic until later proof exists:

- `totalUnits`
- `occupiedUnits`
- `occupancyRate`
- `estimatedValue`
- `activeAlerts`

Reason:

- each depends on semantics not yet proven by the current canonical docs as route-safe derived truth from the resolved cohort alone

## Expected File Scope For The Next Execution PR

- `azure/functions/asset_ingest/ecc_portfolio_summary_service.py`
- `tests/contracts/test_ecc_portfolio_summary_contract.py`

Only add docs if the execution PR needs an additive proof note grounded in the implemented read path.

## Non-Goals

- proving all portfolio summary fields in one pass
- introducing org-wide query abstractions for other ECC routes
- redesigning `external_ids`
- changing handler response envelopes or error shapes
- introducing background reconciliation or scheduled materialization
