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
  "ValidationWarnings": [],
  "Disclaimers": {
    "calculation": {
      "message": "string",
      "warnings": []
    },
    "dataSources": {
      "message": "string",
      "warnings": []
    },
    "useDecision": {
      "message": "string",
      "warnings": []
    }
  },
  "Provenance": {
    "titleQuote": {
      "provider": "string",
      "status": "string",
      "source": "string",
      "quoteReference": null,
      "snapshotVersion": null,
      "quotedAt": null,
      "capturedAt": null,
      "expiresAt": null,
      "sourceWarnings": [],
      "sourceWarningCodes": [],
      "sourceWarningSeverities": [],
      "warningSummary": {
        "highestSeverity": null,
        "hasCritical": false,
        "hasWarning": false,
        "hasInfo": false
      },
      "warningCounts": {
        "critical": 0,
        "warning": 0,
        "info": 0,
        "total": 0
      },
      "exportArtifactId": null,
      "exportArtifactType": null,
      "exportTraceKey": null,
      "sourceTraceKey": "string",
      "snapshotTraceKey": null,
      "sourceEventRef": "string",
      "snapshotEventRef": null
    },
    "scenario": {
      "profile": "string",
      "appliedPresetFields": [],
      "validationWarnings": []
    },
    "trace": {
      "generatedAt": null
    }
  }
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
- When `PRICE_ENGINE_TITLE_RATE_PROVIDER=liberty` and an approved `providerContext.libertySnapshot` payload is present, title fees are sourced from the Liberty snapshot ingest path instead of the zero-fee stub path.
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
- `ValidationWarnings` contains non-fatal normalization notices when scenario presets fill missing or approximated underwriting inputs and is otherwise empty.
- `Disclaimers` is always present and contains deterministic `calculation`, `dataSources`, and `useDecision` disclaimer categories.
- `Disclaimers.calculation.warnings` is amplified when preset-backed defaults were used to fill missing or approximated underwriting inputs.
- `Disclaimers.dataSources.warnings` is amplified when Liberty fallback stub title data is used instead of an approved Liberty snapshot.
- `Disclaimers.useDecision.warnings` repeats any amplified assumptions that materially affect downstream reliance on the response.
- `Provenance` is always present and contains canonical `titleQuote`, `scenario`, and `trace` metadata for the response.
- `Provenance.titleQuote.provider` surfaces the normalized quote provider key such as `stub`, `liberty`, or `none`.
- `Provenance.titleQuote.status` surfaces the normalized quote status such as `stub`, `quoted`, `fallback_stub`, or `not_requested`.
- `Provenance.titleQuote.source` surfaces the canonical source path such as `stub`, `liberty_iframe_snapshot`, or `not_requested`.
- `Provenance.titleQuote.quoteReference` surfaces the provider quote or snapshot reference when available.
- `Provenance.titleQuote.snapshotVersion` surfaces the normalized snapshot version when available.
- `Provenance.titleQuote.quotedAt`, `capturedAt`, and `expiresAt` surface normalized quote-timing metadata when available and are otherwise `null`.
- `Provenance.titleQuote.sourceWarnings` surfaces deterministic source-quality warnings already known in the quote-response path, including stub use, fallback use, and legacy alias normalization.
- `Provenance.titleQuote.sourceWarningCodes` surfaces deterministic machine-usable warning codes such as `stub_provider_used`, `liberty_iframe_no_backend_api`, `fallback_stub_used`, `snapshot_missing_required_fields`, `snapshot_expired`, `legacy_quote_alias_normalized`, and `quote_source_unavailable` when those conditions are already known in the current response path.
- `Provenance.titleQuote.sourceWarningSeverities` surfaces positional machine-usable severities aligned to `sourceWarningCodes`, using `info`, `warning`, and `critical`.
- `Provenance.titleQuote.warningSummary` surfaces compact grouped warning state with `highestSeverity`, `hasCritical`, `hasWarning`, and `hasInfo`.
- `Provenance.titleQuote.warningCounts` surfaces deterministic grouped warning counts for `critical`, `warning`, `info`, and `total`.
- `Provenance.titleQuote.exportArtifactId` and `exportArtifactType` surface export-reference metadata when the normalized quote source provides it and are otherwise `null`.
- `Provenance.titleQuote.exportTraceKey` surfaces a deterministic trace key derived from `exportArtifactType` plus `exportArtifactId` when available, and otherwise falls back to a provider-plus-quote-reference key when one exists.
- `Provenance.titleQuote.sourceTraceKey` surfaces a compact deterministic provider-status-source trace reference for downstream audit and report joins.
- `Provenance.titleQuote.snapshotTraceKey` surfaces a deterministic provider-snapshot-reference trace key when snapshot metadata is available and is otherwise `null`.
- `Provenance.titleQuote.sourceEventRef` and `snapshotEventRef` surface audit-safe event-style references derived only from the existing normalized source and snapshot trace keys.
- `Provenance.scenario.profile` echoes the selected scenario profile.
- `Provenance.scenario.appliedPresetFields` and `Provenance.scenario.validationWarnings` repeat the normalized assumption path used for the calculation.
- `Provenance.trace.generatedAt` is returned as `null` in this slice to preserve deterministic responses while reserving the trace field for future additive timing metadata.
- When no approved live title-rate provider is configured, or when Liberty quote retrieval is unavailable, the route uses the deterministic stub quote path and therefore returns zero title-fee totals instead of synthetic manual title fees.

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
