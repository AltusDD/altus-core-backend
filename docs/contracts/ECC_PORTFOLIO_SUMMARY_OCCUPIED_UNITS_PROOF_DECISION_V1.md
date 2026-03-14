# ECC PORTFOLIO SUMMARY occupiedUnits PROOF DECISION V1

## Purpose

Decide whether `GET /api/ecc/portfolio/summary` can safely activate `occupiedUnits`
from the already resolved `public.assets` portfolio cohort without changing the
public contract, widening route scope, or inventing occupancy semantics.

## Route Scope

- Route entrypoint: `azure/functions/asset_ingest/function_app.py`
- Handler: `azure/functions/asset_ingest/ecc_portfolio_summary_handler.py`
- Service: `azure/functions/asset_ingest/ecc_portfolio_summary_service.py`
- Public contract baseline: `docs/contracts/ECC_PORTFOLIO_SUMMARY_CONTRACT_V1.md`

## Current Backed Fields On Main

- `assetCount`
  - backed from `public.assets` through the `external_ids` cohort resolver seam
- `totalUnits`
  - backed from `public.asset_specs_reconciled.units_count`
  - aggregated across the same resolved asset cohort

`occupiedUnits` remains deterministic fallback on `main`.

## Resolved Cohort Path Already Proven

Current route-scoped read path:

1. Resolve the portfolio asset cohort from `public.assets`.
2. Use `public.assets.external_ids[<configured_key>] == portfolioId` as the only
   allowed persistent cohort mapping rule.
3. Read additional aggregate-safe fields only if a repo-grounded source exists
   for the exact same resolved asset IDs.

This path is already proven safe for `assetCount` and `totalUnits`.

## Candidate Source Evaluation For occupiedUnits

### Candidate Table: `public.assets`

Possible join path:

- same resolved cohort, directly on `public.assets.id`

Potentially relevant proven column:

- `status`

Why it is not enough:

- `docs/database/SCHEMA_INVENTORY_V1.md` proves `public.assets.status` exists, but
  does not define any occupancy meaning for that field.
- `docs/architecture/DATA_MAP_V1.md` describes `assets` as canonical current asset
  state, identity, and timestamps, not unit occupancy.
- current ingest code in `azure/functions/asset_ingest/function_app.py` writes
  asset lifecycle status values such as active/archive-style asset state, not a
  unit-level occupied-vs-vacant contract.

Decision:

- not a contract-safe source for `occupiedUnits`

### Candidate Table: `public.asset_specs_reconciled`

Possible join path:

- join `public.asset_specs_reconciled.asset_id` to the resolved `public.assets.id`
  cohort

Relevant proven columns:

- `units_count`
- `beds`
- `baths`
- `sqft`
- `year_built`
- `property_type`

Why it is not enough:

- `units_count` safely supports `totalUnits`, but repo-grounded truth does not
  prove any occupied-unit field, vacancy field, lease field, tenant field, or
  occupancy-state field in `public.asset_specs_reconciled`.
- `docs/database/SCHEMA_INVENTORY_V1.md` explicitly says live semantic usage for
  `asset_specs_reconciled` remains unproven beyond structural existence.

Decision:

- not a contract-safe source for `occupiedUnits`

### Candidate Table: `public.asset_data_raw`

Possible join path:

- join `public.asset_data_raw.asset_id` to the resolved `public.assets.id` cohort

Why it is not enough:

- `docs/database/SCHEMA_INVENTORY_V1.md` treats `asset_data_raw` as a raw evidence
  stream, not a canonical summary authority.
- no repo-grounded occupancy schema or normalized occupied/vacant contract is
  proven in `payload_jsonb`.
- using raw evidence would require inferred semantics, which this slice forbids.

Decision:

- not a contract-safe source for `occupiedUnits`

## Semantic Definition Check

Repo-grounded proof for the meaning of `occupiedUnits` is currently absent.

The repository does not yet prove any of the following for the resolved cohort:

- a unit-level occupied/vacant state field
- a lease-backed occupied-unit aggregate
- a vacancy-backed inverse aggregate
- a documented rule that asset-level `status` maps to occupied units

Current `occupiedUnits` behavior in the route contract is therefore still a stub
value only.

## Nullability / Incompleteness Risk

If a future source is introduced, the field must still remain fallback-first
unless all of the following are proven:

- the source is read-only and cohort-joinable
- the source semantics explicitly define occupied units
- every row required for the resolved cohort is present and complete
- partial occupancy evidence does not leak mixed real/stub values

Until then, deterministic fallback must remain intact for `occupiedUnits`.

## Decision

`occupiedUnits` is not safely provable from current repo-grounded, read-only truth
for the resolved portfolio asset cohort.

The route must not activate `occupiedUnits` in this slice.

## Exact Reason

No repository-grounded table, view, or function currently defines contract-safe
occupancy semantics for the resolved cohort; the closest proven sources expose
asset lifecycle status or structural unit counts only, which is insufficient to
derive occupied units without inventing new route semantics.

## Next Safe Follow-On

The next Core-only slice should remain proof-first and determine whether a
normalized occupancy authority exists or needs an explicit future contract
decision before any `occupiedUnits` or `occupancyRate` activation can proceed.
