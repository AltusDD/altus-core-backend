# BACKEND_CONTRACT_HARDENING_PLAN_V1

Status: issue-ready Core-lane plan
Scope: backend runtime truth only

This plan is grounded in the currently discovered Azure Functions runtime under `azure/functions/asset_ingest/`. It excludes DB-autonomy framework work and only describes the live backend surfaces that are currently routed in `function_app.py`.

## Current Runtime Surfaces

| Route | Runtime Type Today | Durable Write Today | Proof-Bearing Contract Tests Present | Hardening Priority |
|---|---|---|---|---|
| `POST /api/assets/ingest` | Live handler with external writes | Yes | No repo-local contract test discovered | P1 |
| `GET /api/ecc/portfolio/summary` | Deterministic/mock service response | No | No repo-local contract test discovered | P3 |
| `GET /api/ecc/portfolio/assets` | Deterministic/mock service response | No | No repo-local contract test discovered | P3 |
| `GET /api/ecc/assets/search` | Deterministic/mock service response | No | No repo-local contract test discovered | P3 |
| `GET /api/ecc/assets/metrics` | Deterministic/mock service response | No | No repo-local contract test discovered | P3 |
| `GET /api/ecc/system/health` | Deterministic/mock service response | No | No repo-local contract test discovered | P3 |
| `POST /api/price-engine/calculate` | Live deterministic calculation path | No | No repo-local contract test discovered | P2 |

## Route Truth By Surface

### `POST /api/assets/ingest`

Observed in code:
- validates `x-altus-org-id`
- validates body fields `source`, `raw`, and optional `asset`
- writes to Supabase `assets`
- writes to Supabase `asset_data_raw`
- depends on Azure Managed Identity, Azure Key Vault, and Supabase secrets

Risk profile:
- highest runtime risk of the current surface
- contract drift here can create bad writes or silently change ingest semantics
- failure modes depend on both request shape and external dependency availability

Current proof gap:
- no discovered proof-bearing request/response contract test
- no discovered write-path verification test that proves the expected Supabase payload shape end to end

### ECC read surfaces

Routes:
- `GET /api/ecc/portfolio/summary`
- `GET /api/ecc/portfolio/assets`
- `GET /api/ecc/assets/search`
- `GET /api/ecc/assets/metrics`
- `GET /api/ecc/system/health`

Observed in code:
- each route delegates to a handler and then to a service builder
- each service returns deterministic in-code payloads based on input seeds or fixed component values
- none of these routes show a durable read or write path in the current implementation
- `ecc/system/health` returns synthetic health data and should not be treated as live infrastructure truth

Risk profile:
- lower operational risk than ingest because they do not appear to mutate durable state
- still high contract clarity risk because they look production-like even though they are deterministic/mock-backed

Current proof gap:
- no discovered contract fixtures or proof-bearing tests that lock field names, validation errors, pagination semantics, or headers

### `POST /api/price-engine/calculate`

Observed in code:
- validates strategy and numeric inputs
- computes MAO, IRR, CoC, CashToClose, Profit, and RiskScore
- raises named error codes such as `UNSUPPORTED_STRATEGY_MODE`, `VALIDATION_FAILED`, `UNSOLVABLE_MAO`, and `CALCULATION_FAILED`
- does not show a durable write path in the current implementation

Risk profile:
- medium runtime risk because contract changes alter decision-support math rather than persistence
- highest non-write risk because output fields and error codes may become downstream contract dependencies quickly

Current proof gap:
- no discovered proof-bearing contract tests for success payloads
- no discovered proof-bearing test matrix for validation and error-code coverage

## Which Routes Are Mock / Deterministic Today

Deterministic or mock-backed today:
- `GET /api/ecc/portfolio/summary`
- `GET /api/ecc/portfolio/assets`
- `GET /api/ecc/assets/search`
- `GET /api/ecc/assets/metrics`
- `GET /api/ecc/system/health`
- `POST /api/price-engine/calculate` is deterministic calculation logic, but not a mock transport surface

Not mock-backed today:
- `POST /api/assets/ingest` because it performs durable writes through external dependencies

## Which Routes Have Durable Writes Today

Durable write path discovered:
- `POST /api/assets/ingest`

No durable write path discovered:
- `GET /api/ecc/portfolio/summary`
- `GET /api/ecc/portfolio/assets`
- `GET /api/ecc/assets/search`
- `GET /api/ecc/assets/metrics`
- `GET /api/ecc/system/health`
- `POST /api/price-engine/calculate`

## Which Routes Lack Proof-Bearing Contract Tests

No repo-local proof-bearing contract tests were discovered for:
- `POST /api/assets/ingest`
- `GET /api/ecc/portfolio/summary`
- `GET /api/ecc/portfolio/assets`
- `GET /api/ecc/assets/search`
- `GET /api/ecc/assets/metrics`
- `GET /api/ecc/system/health`
- `POST /api/price-engine/calculate`

## Safest First Hardening Target

`POST /api/price-engine/calculate`

Why it comes first:
- it is real executable backend logic, not a mock-only surface
- it has no discovered durable write path, so contract hardening is lower-risk than starting with ingest
- its request validation, error codes, and output fields are already explicit in code and can be locked with proof-bearing tests without changing deploy targets or persistence
- it creates a reusable pattern for contract fixtures and proof-bearing tests before applying the same discipline to the higher-risk ingest route

## Recommended Hardening Sequence

1. Harden `POST /api/price-engine/calculate`
   - add request/response fixtures
   - add proof-bearing tests for success and named failure modes
   - document current contract expectations explicitly
2. Harden `POST /api/assets/ingest`
   - add request validation coverage
   - add write-shape verification against the expected Supabase payload contract
   - add clear external-dependency failure expectations
3. Harden ECC read surfaces
   - decide whether they should remain deterministic placeholders or become storage-backed
   - add contract fixtures that make the current placeholder status explicit until real data reads exist

## Issue-Ready Follow-Up

First Core-only hardening issue to open:
- Title: `CORE HARDENING — proof-bearing contract tests for POST /api/price-engine/calculate`
- Scope:
  - add success and error-case contract fixtures/tests only
  - no deploy target changes
  - no runtime secret changes
  - no route expansion
