# ECC PORTFOLIO ASSETS BACKING TRUTH DECISION V1

## Purpose

Select the single next ECC backend surface that can produce real product progress
after the portfolio-summary expansion path paused on unproven occupancy
semantics.

This decision is limited to the remaining contract-locked ECC routes:

- `GET /api/ecc/system/health`
- `GET /api/ecc/portfolio/assets`
- `GET /api/ecc/assets/search`
- `GET /api/ecc/assets/metrics`

## Current Decision

The next safest implementation target is:

- `GET /api/ecc/portfolio/assets`

This slice should remain route-scoped, read-only, and contract-preserving.

## Why This Route Comes Next

`GET /api/ecc/portfolio/assets` is the lowest-risk next surface because it
already shares the same portfolio cohort concept proven in the live
`GET /api/ecc/portfolio/summary` path:

1. the route is portfolio-scoped rather than free-form search scoped
2. the cohort can reuse the existing `public.assets.external_ids` mapping seam
3. the row authority can come from normalized asset records rather than raw
   evidence payloads
4. the visible product value is immediate because this route renders the asset
   list users would expect behind a portfolio detail surface
5. the implementation can activate a small subset of fields while leaving
   higher-risk fields on deterministic fallback

## Selected Normalized Authorities

The clearest repo-grounded normalized authorities for this route are:

- `public.assets`
  - authoritative row identity through `id`
  - canonical presentation field through `display_name`
  - normalized lifecycle state through `status`
  - portfolio cohort resolution through `external_ids[<configured_key>]`
- `public.asset_specs_reconciled`
  - read-only per-asset unit count through `units_count`
  - join path through `asset_specs_reconciled.asset_id -> public.assets.id`

## Smallest Safe Implementation Slice

The smallest safe read-only slice for this route is:

1. resolve the requested portfolio cohort from `public.assets` using the
   existing `external_ids` portfolio mapping pattern already proven for
   portfolio summary
2. page the resolved cohort deterministically
3. back only the fields that are directly proven by normalized authorities:
   - `assetId`
   - `portfolioId`
   - `displayName`
   - `status`
   - `totalUnits` when a complete `asset_specs_reconciled.units_count` row is
     present for every returned asset
4. preserve deterministic fallback for fields whose semantics are not yet
   proven:
   - `occupiedUnits`
   - `occupancyRate`
   - `marketValue`
   - `city`
   - `state`
   - `assetType` if no normalized governing field is explicitly mapped in the
     same slice
   - `meta.total` if count pagination semantics cannot be proven cleanly from
     the same query path without contract drift

## Route-By-Route Audit

### `GET /api/ecc/system/health`

Current route shape is operational summary data:

- top-level `status`
- generated timestamps
- component health rows
- incident count

Why it is not next:

- no repo-grounded operational authority is currently documented for these
  component statuses or latency values
- backing this route safely would require inventing monitoring-to-contract
  semantics or widening into Azure observability sources that are not yet part
  of the locked ECC contract proof set
- product value is lower than moving a portfolio-facing list surface off stub
  data

Decision:

- not the next safest route

### `GET /api/ecc/portfolio/assets`

Current route shape is a portfolio-scoped list of asset rows plus pagination
metadata.

Why it is next:

- shares the already-proven portfolio cohort pattern
- `public.assets` already exposes normalized row identity, presentation, and
  lifecycle fields
- `public.asset_specs_reconciled.units_count` already supports one direct
  per-asset aggregate without inventing occupancy semantics
- route can improve visible portfolio product behavior without touching other
  ECC surfaces

Decision:

- selected as the next safest route

### `GET /api/ecc/assets/search`

Current route shape depends on free-form query behavior and match scoring.

Why it is not next:

- repo truth does not yet prove a contract-safe search ranking or fuzzy-match
  authority
- current response includes a nested `match.strategy` and `match.score`, and
  those semantics are not grounded in canonical DB truth
- even if `public.assets.display_name` is normalized, translating user query
  text into ranked results would require new search semantics rather than a
  small backing slice

Decision:

- not the next safest route

### `GET /api/ecc/assets/metrics`

Current route shape includes occupancy, collections, maintenance ratios,
delinquent units, work orders, NOI, and timestamps.

Why it is not next:

- nearly every response field depends on metric or occupancy semantics not yet
  proven by canonical read-only authorities
- current repo truth proves neither a normalized occupancy authority nor a
  windowed metrics authority for the route
- the route would require a much wider semantic decision than the portfolio
  assets list surface

Decision:

- not the next safest route

## Risks And Guardrails

- `public.assets.external_ids` is proven live in staging and already used as the
  active portfolio cohort seam, but its broader canonical semantics remain
  intentionally narrow; the route should use only the explicit configured
  portfolio mapping key
- `public.asset_specs_reconciled` is structurally proven, but live semantic
  usage beyond `units_count` remains narrow; no occupancy or market-value
  semantics should be inferred from it
- partial or incomplete per-asset unit rows must not leak mixed real/stub
  aggregates; deterministic fallback must remain intact whenever proof is
  incomplete

## Decision

The next provable ECC backend surface is `GET /api/ecc/portfolio/assets`.

The route is safer than the remaining ECC routes because it can reuse the
existing portfolio cohort resolver and read normalized per-asset records from
`public.assets`, with one narrow optional join to
`public.asset_specs_reconciled.units_count`, while preserving deterministic
fallback for every field whose meaning is not already proven.

## Next Action

Open the next Core-only implementation PR for `GET /api/ecc/portfolio/assets`
that activates only the smallest read-only field subset proven by
`public.assets` and `public.asset_specs_reconciled.units_count`, while leaving
all higher-risk fields on deterministic fallback.
