# ECC PORTFOLIO SUMMARY NORMALIZED OCCUPANCY AUTHORITY PROOF V1

## Purpose

Determine whether a normalized, read-only occupancy authority already exists for
the resolved `GET /api/ecc/portfolio/summary` asset cohort that could safely
back `occupiedUnits` in a future slice without schema mutation.

## Accepted Current State

- `occupiedUnits` remains deterministic fallback
- no normalized authority exists in current proof review
- `assetCount` and `totalUnits` are already activated

## Cohort Boundary

The only proven portfolio cohort path is:

1. resolve asset membership from `public.assets`
2. match `public.assets.external_ids[<configured_key>] == portfolioId`
3. join any future backing source by the resolved `public.assets.id` cohort only

This proof does not widen route scope, activate any field, or change schema.

## Investigation Scope

Inspected repo-grounded candidate areas:

- `public.asset_data_raw`
- external ingestion code and feed entrypoints
- future normalized views
- existing SQL views
- pipeline transforms
- materialized views
- ETL outputs

## Candidate Structures Discovered

### `public.assets`

Join path:

- direct cohort authority on `public.assets.id`

Semantic relevance:

- exposes asset lifecycle/current-state fields including `status`

Why it is not a normalized occupancy authority:

- repo docs define `assets` as current asset state, identity, and timestamps
- no repo-grounded rule maps `assets.status` to occupied-unit counts
- current runtime writes lifecycle-style asset status, not unit occupancy

Completeness and nullability risks:

- no occupied-unit field exists to test for completeness
- any derivation from `status` would invent semantics outside the contract-safe
  proof boundary

Decision:

- not a candidate authority for `occupiedUnits`

### `public.asset_specs_reconciled`

Join path:

- `public.asset_specs_reconciled.asset_id = public.assets.id`

Semantic relevance:

- exposes `units_count` and structural/spec columns such as `beds`, `baths`,
  `sqft`, `year_built`, `property_type`, `specs`, `provenance`, and
  `effective_at`

Why it is not a normalized occupancy authority:

- no occupied-unit, vacancy, lease, tenant, or occupancy-state field is proven
- structural staging proof shows `0` rows, so live semantic usage is unproven
- `units_count` safely supports `totalUnits` only; it does not define occupancy

Completeness and nullability risks:

- `units_count` is nullable
- staging proof currently shows zero rows, so cohort completeness is not proven
- extra versioning/provenance columns do not establish occupied-unit semantics

Decision:

- not a candidate authority for `occupiedUnits`

### `public.asset_data_raw`

Join path:

- `public.asset_data_raw.asset_id = public.assets.id`

Semantic relevance:

- canonical raw evidence stream for ingest, audit, timeline, and fallback
  evidence flows

Why it is not a normalized occupancy authority:

- no repo-proven normalized occupied/vacant contract exists in
  `payload_jsonb`
- raw evidence would require inference from payload shape or source strings
- proof rules for this slice forbid invented semantics from raw evidence

Completeness and nullability risks:

- payload shape is source-dependent rather than normalized
- occupancy keys are not documented, proven, or completeness-checked
- missing or partial evidence could leak mixed real/stub behavior

Decision:

- not a candidate authority for `occupiedUnits`

### Repo-Proven SQL Views

Join path:

- none discovered

Semantic relevance:

- `docs/database/SCHEMA_INVENTORY_V1.md` states no critical views are proven by
  repository migrations on `main`

Completeness and nullability risks:

- no view exists to evaluate for occupancy completeness

Decision:

- no candidate normalized occupancy view is provable

### Repo-Proven Materialized Views

Join path:

- none discovered

Semantic relevance:

- no repository migration or documentation proves a materialized view for
  occupancy or portfolio summary backing

Completeness and nullability risks:

- no object exists to evaluate

Decision:

- no candidate materialized occupancy authority is provable

### External Ingestion / Pipeline / ETL Outputs

Join path:

- ingest writes to `public.assets` and `public.asset_data_raw`

Semantic relevance:

- repo-grounded ingest output is current-state asset data plus raw evidence

Why it is not a normalized occupancy authority:

- no separate normalized occupancy output table, view, or ETL product is proven
- no downstream transform artifact in repo exposes occupied-unit aggregates for
  the resolved asset cohort

Completeness and nullability risks:

- any occupancy extraction would depend on unproven raw payload conventions
- no contract-safe coverage proof exists for all assets in the resolved cohort

Decision:

- no normalized occupancy authority is proven in ingestion or ETL surfaces

## Exact Authority Discovered

None.

The closest repo-grounded objects are:

- `public.assets` for cohort membership and current asset state
- `public.asset_specs_reconciled` for `totalUnits` via `units_count`
- `public.asset_data_raw` for raw evidence only

None explicitly defines occupied units for the resolved portfolio cohort.

## Final Decision

Not provable.

No normalized, read-only occupancy authority is currently proven for the
resolved `public.assets` cohort, so `occupiedUnits` must remain deterministic
fallback until a future explicit DB-backed occupancy contract is proven.

## Exact Next Database-Only Action

Run a dedicated staging discovery proof that checks whether any live
read-only table or view outside current repo truth exposes an explicit
asset-joinable occupied-unit field for the resolved cohort.
