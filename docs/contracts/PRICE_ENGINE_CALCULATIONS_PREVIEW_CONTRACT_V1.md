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
- `titlePremium`
- `settlementFee`
- `recordingFee`
- `ownerPolicy`
- `lenderPolicy`
- `reserves`
- `points`
- `pointsRate`
- `loanAmount`
- `financedLtv`
- `holdingMonths`
- `interestRateAnnual`
- `amortizationMonths`
- `targetProfitMargin`

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
- `TotalLenderFees` aggregates loan origination, underwriting, processing, appraisal, and credit report fees.
- `TotalTitleFees` aggregates title premium, settlement, recording, owner policy, and lender policy fees.
- `TotalTransactionCosts` aggregates `closingCosts + TotalLenderFees + TotalTitleFees`.

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
