# PRICE_ENGINE_CALCULATE_CONTRACT_V1

Status: Core-lane contract baseline
Route: `POST /api/price-engine/calculate`
Runtime owner: `azure/functions/asset_ingest/price_engine_handler.py`

This document records the currently executable contract for the price engine calculate route. It is grounded in the live handler and service code on `main`.

## Current Behavior

- Accepts a JSON object request body.
- Returns a `200` JSON object on success.
- Returns a `400` JSON error envelope for validation and named business-rule failures.
- Returns a `500` JSON error envelope for unexpected internal failures.

## Required Request Fields

- `strategy`
- `purchasePrice`
- `afterRepairValue`
- `rehabCost`
- `holdingCosts`
- `closingCosts`
- `cashAvailable`

## Optional Request Fields

- `rentMonthly`
- `operatingExpenseMonthly`
- `sellingCosts`
- `loanOriginationFee`
- `underwritingFee`
- `processingFee`
- `appraisalFee`
- `creditReportFee`
- `reserves`
- `points`
- `pointsRate`
- `loanAmount`
- `financedLtv`
- `holdingMonths`
- `interestRateAnnual`
- `amortizationMonths`
- `targetProfitMargin`
- `transactionType`
- `propertyState`
- `county`
- `city`
- `postalCode`
- `ownerPolicyAmount`
- `lenderPolicyAmount`
- `endorsements`
- `transactionDate`
- `providerContext`

## Supported Strategy Values

- `flip`
- `rental_hold`
- `brrrr`

## Success Contract

Status code:
- `200`

Response shape:

```json
{
  "MAO": 0.0,
  "IRR": 0.0,
  "CoC": 0.0,
  "CashToClose": 0.0,
  "Profit": 0.0,
  "RiskScore": 0,
  "TotalLenderFees": 0.0,
  "TotalTitleFees": 0.0,
  "TotalTransactionCosts": 0.0
}
```

Notes:
- Success response is a flat JSON object, not wrapped in `data`.
- Currency-like numeric fields are rounded to two decimals.
- `RiskScore` is returned as an integer.
- `IRR` is annualized from monthly hold-period cash flows.
- `CoC` uses annual net operating cash flow divided by upfront cash to close.
- `TotalLenderFees` aggregates loan origination, underwriting, processing, appraisal, and credit report fees.
- `TotalTitleFees` is sourced from the normalized title-rate quote mapping layer rather than caller-supplied title fee inputs.
- `TotalTransactionCosts` aggregates `closingCosts + TotalLenderFees + TotalTitleFees`.
- When no approved live title-rate provider is configured, the route uses the existing stub quote path and therefore returns zero title-fee totals instead of synthetic manual title fees.

## Error Contract

Status code:
- `400` for validation and named business-rule failures
- `500` for unexpected internal failures

Response shape:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "human readable message",
    "details": null
  }
}
```

Named error codes currently observed in code:
- `VALIDATION_FAILED`
- `UNSUPPORTED_STRATEGY_MODE`
- `UNSOLVABLE_MAO`
- `CALCULATION_FAILED`
- `INTERNAL_ERROR`

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/price_engine_calculate/success_request.json`
- `docs/contracts/fixtures/price_engine_calculate/success_response.json`
- `docs/contracts/fixtures/price_engine_calculate/error_unsupported_strategy_request.json`
- `docs/contracts/fixtures/price_engine_calculate/error_unsupported_strategy_response.json`
- `docs/contracts/fixtures/price_engine_calculate/error_missing_purchase_price_request.json`
- `docs/contracts/fixtures/price_engine_calculate/error_missing_purchase_price_response.json`

## Proof Rules

- If the request or response contract changes, the fixtures and tests must change in the same PR.
- If a new named error code is introduced, it must be added here and covered by proof-bearing tests.
- This contract does not claim persistence behavior because the route is a calculation surface, not a durable write path.
