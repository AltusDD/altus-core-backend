# ECC_PORTFOLIO_SUMMARY_BACKING_TRUTH_PLAN_V1

Status: Core-lane transition plan
Route: `GET /api/ecc/portfolio/summary`

## Purpose

Define the safest first implementation path for moving `GET /api/ecc/portfolio/summary` from deterministic in-code payload generation toward backed truth without widening scope into sibling ECC routes or introducing schema changes.

## Current Route Ownership

Runtime ownership today:
- route entrypoint: `azure/functions/asset_ingest/function_app.py`
- route handler: `azure/functions/asset_ingest/ecc_portfolio_summary_handler.py`
- current deterministic service: `azure/functions/asset_ingest/ecc_portfolio_summary_service.py`
- active contract baseline: `docs/contracts/ECC_PORTFOLIO_SUMMARY_CONTRACT_V1.md`
- active proof module: `tests/contracts/test_ecc_portfolio_summary_contract.py`
- route-scoped CI proof: `.github/workflows/ecc_portfolio_summary_contract_proof.yml`

Current status:
- response contract is proof-bearing on `main`
- implementation is still deterministic stub logic derived from the input `portfolioId`
- no live Supabase read path is currently proven in the handler or service

## Contract Constraints That Must Not Drift

Any first execution pass must preserve:
- required query parameter: `portfolioId`
- optional query parameter: `asOfDate`
- success envelope shape: top-level `data`
- required success fields:
  - `portfolioId`
  - `asOfDate`
  - `assetCount`
  - `occupiedUnits`
  - `totalUnits`
  - `occupancyRate`
  - `estimatedValue`
  - `currency`
  - `activeAlerts`
  - `status`
- error envelopes and current named error codes:
  - `VALIDATION_FAILED`
  - `INTERNAL_ERROR`
- response headers:
  - `x-altus-build-sha`
  - `x-ecc-handler`
  - `x-ecc-domain-signature`

## Canonical Repo-Grounded Source Context

Current canonical data docs say:
- `docs/architecture/ROUTE_MAP_V1.md` marks `/api/ecc/portfolio/summary` as an ECC singleton summary stub with deterministic placeholder data.
- `docs/architecture/DATA_MAP_V1.md` explicitly states there are no repo-proven authoritative DB objects yet for ECC portfolio summary surfaces.
- `docs/database/SCHEMA_INVENTORY_V1.md` repeats that `ecc_portfolio_summary_service.py` is currently deterministic stub logic with no proven Supabase persistence calls.

That means the route can move only toward backed truth from repo-proven structural candidates, not from already-proven route-specific persistence.

## Candidate Backing Sources From Current Canonical Docs

### Candidate A: `public.assets`

Grounding:
- `docs/architecture/DATA_MAP_V1.md` and `docs/database/SCHEMA_INVENTORY_V1.md` both treat `public.assets` as canonical current-state storage for asset surfaces.

Potential future use for this route:
- counting assets in a resolved portfolio cohort
- deriving a coarse asset-count-backed summary base

Current limitation:
- no repo-proven portfolio membership source currently maps `portfolioId` to a concrete asset cohort on `main`

### Candidate B: `public.asset_specs_reconciled`

Grounding:
- `docs/database/SCHEMA_INVENTORY_V1.md` proves the structure exists conceptually and notes `units_count` is part of repo-proven columns somewhere in migrations.

Potential future use for this route:
- deriving `totalUnits`

Current limitation:
- canonical final column semantics are not fully settled
- staging semantic usage is unproven because the structurally proven table currently has zero rows

### Candidate C: `public.asset_data_raw`

Grounding:
- `docs/architecture/DATA_MAP_V1.md` and `docs/database/SCHEMA_INVENTORY_V1.md` treat `asset_data_raw` as the canonical raw evidence stream and fallback evidence source.

Potential future use for this route:
- deriving alert-style or audit-style supporting metrics in a later pass

Current limitation:
- no route-specific summary derivation contract is proven from this source today
- using it for `activeAlerts` now would be speculative without additional proof

### Candidate D: org-scope anchors only

Grounding:
- `public.organizations`, `public.profiles`, and `public.organization_members` are repo-proven identity and scoping anchors.

Potential future use for this route:
- scoping any future backed portfolio read path safely to the caller's organization

Current limitation:
- these objects do not prove a `portfolioId` to asset-membership mapping by themselves

## Critical Backing Gap

The current repo truth has no proven portfolio membership authority for `portfolioId`.

Implication:
- the route cannot truthfully switch to a DB-backed portfolio summary read until there is a repo-grounded way to resolve `portfolioId` into a concrete asset cohort
- any implementation that silently substitutes org-wide assets for portfolio membership would drift route meaning and is out of scope

## Required Proof Before Implementation

Before a runtime-backed portfolio summary can replace stub values, the next execution work must prove:
- what repository-grounded source resolves `portfolioId` to an asset cohort
- whether `asset_specs_reconciled.units_count` is sufficiently populated and semantically reliable for `totalUnits`
- whether any repo-grounded source can support `estimatedValue` without inventing a new column mapping
- whether `activeAlerts` should remain deterministic/stubbed until a separate alert authority exists

## Safest First Implementation Slice

The safest first execution PR should:
- keep the public response contract exactly unchanged
- add an internal source-adapter seam inside `ecc_portfolio_summary_service.py`
- preserve the current deterministic stub as the fallback path
- gate any backed read attempt behind an explicit, repo-grounded cohort resolver interface rather than directly querying arbitrary tables
- limit backed-truth activation to fields that can be proven from the resolved cohort without guessing

Recommended first slice detail:
- introduce a private portfolio cohort resolver abstraction for this route only
- keep it returning `not_proven` / fallback by default until a repo-grounded membership source is defined
- structure the service so backed fields can be introduced one field-group at a time without changing the response envelope
- do not switch `activeAlerts`, `estimatedValue`, or `totalUnits` to backed values until their sources are proven by repository truth and route-specific proof

## Explicit Non-Goals For The First Execution Pass

The next execution PR must not:
- modify sibling ECC routes
- introduce schema changes or migrations
- retarget deployment or runtime ownership
- invent a new `portfolio` table or membership table on the fly
- infer portfolio membership from unrelated org-wide assets
- change response field names, headers, or error shapes
- claim live alert or valuation truth that is not repo-proven

## Decision Checkpoint For The Next Execution PR

The next execution PR is ready only if it can answer all of the following with repo-grounded evidence:
- what exact source resolves `portfolioId`
- what exact fields can switch from deterministic to backed values without contract drift
- what fields must remain deterministic until more proof exists
- what route-scoped tests and fixtures will prove the mixed backed/stub state truthfully
