# PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1

Status: Core-lane Price Engine contract coverage index
Scope: Discovered Price Engine HTTP routes in `azure/functions/asset_ingest/function_app.py`

This index records the current proof-bearing contract coverage for the discovered Price Engine route surface on `main`.

## Coverage Summary

All discovered Price Engine routes currently have:
- route-scoped contract documentation
- route-scoped proof fixtures
- route-scoped contract tests
- route-scoped CI workflows

Accepted aggregate backend proof for the current live Price Engine surface is:
- `.github/workflows/price_engine_proof_gate.yml`

## Route Coverage Index

| Route | Contract doc | Fixtures | Contract test | Route-scoped CI workflow | Current proof status |
| --- | --- | --- | --- | --- | --- |
| `POST /api/price-engine/calculate` | `docs/contracts/PRICE_ENGINE_CALCULATE_CONTRACT_V1.md` | `docs/contracts/fixtures/price_engine_calculate/` | `tests/contracts/test_price_engine_calculate_contract.py` | `.github/workflows/price_engine_contract_proof.yml` | live on `main` |
| `GET /api/price-engine/calculations-preview` | `docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md` | `docs/contracts/fixtures/price_engine_calculations_preview/` | `tests/contracts/test_price_engine_calculations_preview_contract.py` | `.github/workflows/price_engine_calculations_preview_contract_proof.yml` | live on `main` |
| `POST /api/price-engine/title-rate-quote` | `docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md` | `docs/contracts/fixtures/title_rate_quote/` | `tests/contracts/test_title_rate_quote_contract.py` | `.github/workflows/title_rate_quote_contract_proof.yml` | live on `main` |

## Audit Basis

The route inventory above is grounded in the current route declarations in `azure/functions/asset_ingest/function_app.py`.

## Maintenance Rule

If a discovered Price Engine route changes contract shape, its contract doc, fixtures, test module, and route-scoped CI workflow must be updated in the same PR.
The aggregate proof gate at `.github/workflows/price_engine_proof_gate.yml` must stay aligned with the accepted live route surface and its governance proofs.
