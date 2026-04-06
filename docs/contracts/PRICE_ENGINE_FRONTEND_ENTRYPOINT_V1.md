# PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1

Status: Canonical frontend entrypoint for the current live Price Engine backend surface
Scope: Live Price Engine routes declared in `azure/functions/asset_ingest/function_app.py`

This document gives frontend consumers one place to find the accepted live Price Engine route surface, its current route posture, and the proof-bearing artifacts that govern each route.

## Canonical Route Posture

The current live Price Engine backend surface is:

- `POST /api/price-engine/calculate`
- `GET /api/price-engine/calculations-preview`
- `POST /api/price-engine/title-rate-quote`

Canonical route ownership is recorded in:

- `docs/architecture/ROUTE_MAP_V1.md`

Canonical proof-bearing route coverage is recorded in:

- `docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md`

Accepted aggregate backend proof is recorded in:

- `.github/workflows/price_engine_proof_gate.yml`

## Live Route Entry Table

| Route | Purpose | Primary contract doc | Fixtures | Contract test | Workflow integrity test | Route-scoped CI workflow | Workflow integrity CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST /api/price-engine/calculate` | Main calculation envelope for underwriting output | `docs/contracts/PRICE_ENGINE_CALCULATE_CONTRACT_V1.md` | `docs/contracts/fixtures/price_engine_calculate/` | `tests/contracts/test_price_engine_calculate_contract.py` | `tests/contracts/test_price_engine_contract_proof_integrity.py` | `.github/workflows/price_engine_contract_proof.yml` | `.github/workflows/price_engine_contract_proof_integrity.yml` |
| `GET /api/price-engine/calculations-preview` | Read-only preview surface over query parameters | `docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md` | `docs/contracts/fixtures/price_engine_calculations_preview/` | `tests/contracts/test_price_engine_calculations_preview_contract.py` | `tests/contracts/test_price_engine_calculations_preview_contract_proof_integrity.py` | `.github/workflows/price_engine_calculations_preview_contract_proof.yml` | `.github/workflows/price_engine_calculations_preview_contract_proof_integrity.yml` |
| `POST /api/price-engine/title-rate-quote` | Provider-normalized title quote seam | `docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md` | `docs/contracts/fixtures/title_rate_quote/` | `tests/contracts/test_title_rate_quote_contract.py` | `tests/contracts/test_title_rate_quote_contract_proof_integrity.py` | `.github/workflows/title_rate_quote_contract_proof.yml` | `.github/workflows/title_rate_quote_contract_proof_integrity.yml` |

## Frontend Integration Rules

- Frontend work should treat repo contract docs as authoritative for field shape and failure-envelope behavior.
- Route additions or removals are not accepted frontend truth until they appear in `docs/architecture/ROUTE_MAP_V1.md`.
- A Price Engine route is not treated as proof-bearing until its fixtures, contract test, workflow integrity test, route-scoped CI workflow, and workflow-integrity CI are all present.
- The accepted aggregate backend proof gate for this surface is `.github/workflows/price_engine_proof_gate.yml`.
- No speculative frontend dependency should be taken on routes not listed in this document.

## Maintenance Rule

If the accepted live Price Engine route surface changes, update this entrypoint document in the same PR as the route map, coverage index, and route-scoped proof artifacts.
