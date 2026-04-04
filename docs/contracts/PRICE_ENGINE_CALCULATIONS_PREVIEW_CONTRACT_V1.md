# PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1

Status: Core-lane calculation preview baseline  
Route: `GET /api/price-engine/calculations-preview`  
Runtime owner: `azure/functions/asset_ingest/price_engine_calculations_preview_handler.py`

This document records the additive calculation-preview surface for the Price Engine. It reuses the shared backend math in `price_engine_calculations.py` and exposes a read-only preview over query parameters.

## Current Behavior

- Accepts query string parameters that mirror the calculation payload fields.
- Returns a `200` JSON object on success.
- Returns a `400` JSON error envelope for validation and named business-rule failures.
- Returns a `500` JSON error envelope for unexpected internal failures.

## Required Query Parameters

- `strategy`
- `purchasePrice`
- `afterRepairValue`
- `rehabCost`
- `holdingCosts`
- `closingCosts`
- `cashAvailable`

## Optional Query Parameters

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
  "NetDispositionProceeds": 0.0
}
```

Notes:
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

## Proof Fixtures

- `docs/contracts/fixtures/price_engine_calculations_preview/success_request.json`
- `docs/contracts/fixtures/price_engine_calculations_preview/success_response.json`
- `docs/contracts/fixtures/price_engine_calculations_preview/error_missing_purchase_price_request.json`
- `docs/contracts/fixtures/price_engine_calculations_preview/error_missing_purchase_price_response.json`
