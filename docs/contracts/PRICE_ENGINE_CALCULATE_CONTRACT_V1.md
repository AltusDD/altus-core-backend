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
- `financeLenderFees`
- `financeTitleFees`
- `financePoints`
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
- `annualInterestRate`
- `interestRateAnnual`
- `interestOnly`
- `exitSalePrice`
- `saleCommissionRate`
- `sellerClosingCostRate`
- `dispositionFee`
- `sellerConcessions`
- `otherExitCosts`

## Supported Strategy Values

- `flip`
- `rental_hold`
- `brrrr`

## Scenario Preset Rules

- `flip`, `brrrr`, and `rental_hold` each provide deterministic default assumptions for hold duration, rate, debt-service mode, sale commission, seller closing cost rate, and target profit margin.
- Presets only fill missing fields; explicit caller-provided values are preserved.
- `ScenarioProfile` echoes the preset selected by `strategy`.
- `AppliedPresetFields` records exactly which preset-backed fields were filled during normalization.

## Canonical Validation Rules

- `purchasePrice >= 0`
- `afterRepairValue >= 0`
- `exitSalePrice >= 0` when provided
- `loanAmount >= 0` when provided
- `loanOriginationFee`, `underwritingFee`, `processingFee`, `appraisalFee`, `creditReportFee`, `points`, `closingCosts`, `holdingCosts`, `rehabCost`, `cashAvailable`, `rentMonthly`, `operatingExpenseMonthly`, `dispositionFee`, `sellerConcessions`, `otherExitCosts`, and `reserves` must be non-negative when provided
- `annualInterestRate` must be between `0` and `1`
- `interestRateAnnual` must be between `0` and `1`
- `saleCommissionRate` must be between `0` and `1`
- `sellerClosingCostRate` must be between `0` and `1`
- `pointsRate` must be between `0` and `0.25`
- `holdingMonths` must be greater than `0` when provided
- `amortizationMonths` must be greater than `0` when provided

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
  "TotalTransactionCosts": 0.0,
  "TotalPoints": 0.0,
  "CashPaidTransactionCosts": 0.0,
  "FinancedTransactionCosts": 0.0,
  "MonthlyDebtService": 0.0,
  "TotalInterestCarry": 0.0,
  "DebtServiceType": "amortized",
  "GrossSaleProceeds": 0.0,
  "TotalExitCosts": 0.0,
  "ExitLoanPayoff": 0.0,
  "NetDispositionProceeds": 0.0,
  "ScenarioProfile": "flip",
  "AppliedPresetFields": [],
  "ValidationWarnings": []
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
- `TotalPoints` is calculated as `loanAmount * pointsRate` when `pointsRate` is provided; otherwise it falls back to the flat `points` input.
- `TotalTransactionCosts` aggregates `closingCosts + TotalLenderFees + TotalTitleFees + TotalPoints`.
- `CashPaidTransactionCosts` includes only non-financed lender fees, title fees, and points.
- `FinancedTransactionCosts` includes only lender fees, title fees, and points flagged for financing.
- `MonthlyDebtService` is the normalized monthly financing obligation generated from the effective financed principal.
- `TotalInterestCarry` is the deterministic interest portion accumulated across the hold period.
- `DebtServiceType` is `interest-only`, `amortized`, or `none`.
- `GrossSaleProceeds` uses `exitSalePrice` when provided and otherwise defaults to `afterRepairValue`.
- `TotalExitCosts` normalizes sale commission, seller closing costs, disposition fee, seller concessions, and other exit costs into one canonical disposition stack.
- `ExitLoanPayoff` is the financed principal payoff required at disposition after carry normalization.
- `NetDispositionProceeds` is `GrossSaleProceeds - TotalExitCosts - ExitLoanPayoff`.
- `ScenarioProfile` echoes the canonical preset profile used for normalization.
- `AppliedPresetFields` lists preset-backed fields that were filled because the caller omitted them.
- `ValidationWarnings` is reserved for non-fatal normalization notices and is empty in this slice.
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
