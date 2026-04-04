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
      "warningFamilies": [],
      "warningFamilySummary": [],
      "warningFamilySummaryLabel": null,
      "warningFamilyDisplayPriority": null,
      "warningFamilyDisplayLabel": null,
      "warningFamilyDisplaySeverity": null,
      "warningFamilyDisplayCount": 0,
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
      "warningFamilyCounts": {
        "provider": 0,
        "snapshot": 0,
        "fallback": 0,
        "compatibility": 0,
        "availability": 0
      },
      "exportArtifactId": null,
      "exportArtifactType": null,
      "exportTraceKey": null,
      "sourceTraceKey": "string",
      "snapshotTraceKey": null,
      "sourceEventType": "string",
      "snapshotEventType": null,
      "sourceEventRef": "string",
      "snapshotEventRef": null,
      "sourceEventBundle": {
        "sourceEventType": "string",
        "sourceEventRef": "string",
        "snapshotEventType": null,
        "snapshotEventRef": null,
        "status": "partial",
        "statusLabel": "Partial Event Bundle",
        "hasSourceEvent": true,
        "hasSnapshotEvent": false,
        "isComplete": false
      },
      "integrationProvider": "corelogic",
      "integrationMode": "disabled",
      "integrationState": "inactive",
      "integrationStateLabel": "Integration Inactive",
      "integrationReasonCodes": [],
      "integrationLiveReady": false,
      "integrationLiveReadyLabel": "Live Integration Not Ready",
      "integrationCredentialState": "missing",
      "integrationCredentialStateLabel": "Credentials Missing",
      "integrationGuardSummary": "disabled",
      "integrationArtifactType": null,
      "integrationArtifactId": null,
      "integrationTraceKey": null,
      "integrationEventType": null,
      "integrationEventRef": null,
      "integrationMockProfile": null,
      "integrationMockProfileLabel": null,
      "integrationResultType": null,
      "integrationExecutionState": null,
      "integrationQuoteReference": null,
      "integrationSnapshotVersion": null,
      "integrationPayloadProfile": null,
      "integrationEstimatedTotalTitleCost": null,
      "integrationCurrency": null,
      "integrationEstimatedTitleFee": null,
      "integrationEstimatedSettlementFee": null,
      "integrationEstimatedRecordingFee": null,
      "integrationEstimatedSearchFee": null,
      "integrationEstimatedMiscFee": null,
      "integrationFeeLineSum": null,
      "integrationFeeDelta": null,
      "integrationFeeReconciliationStatus": null,
      "integrationFeeReconciliationLabel": null,
      "integrationFeeReconciliationMatch": null,
      "integrationBundleStatus": null,
      "integrationBundleStatusLabel": null,
      "integrationHasArtifact": null,
      "integrationHasTrace": null,
      "integrationHasEvent": null,
      "integrationIsExportReady": null,
      "integrationExportReadiness": null,
      "integrationExportReadinessLabel": null,
      "integrationExportReasonCodes": null,
      "integrationAuditCompleteness": null,
      "integrationAuditCompletenessLabel": null,
      "integrationSummaryStatus": null,
      "integrationSummaryStatusLabel": null,
      "integrationSummaryPriority": null,
      "integrationSummaryPriorityLabel": null,
      "integrationSummaryReasonCodes": null,
      "integrationDisplayBadge": null,
      "integrationDisplayBadgeLabel": null,
      "integrationDisplaySeverity": null,
      "integrationDisplayOrder": null,
      "integrationDisplayReason": null,
      "integrationOperatorAction": null,
      "integrationOperatorActionLabel": null,
      "integrationOperatorActionPriority": null,
      "integrationOperatorActionReasonCodes": null,
      "integrationOperatorActionBlocking": null,
      "integrationOperatorSnapshotStatus": null,
      "integrationOperatorSnapshotLabel": null,
      "integrationOperatorSnapshotSeverity": null,
      "integrationOperatorSnapshotOrder": null,
      "integrationOperatorSnapshotReasonCodes": null,
      "integrationOperatorCardStatus": null,
      "integrationOperatorCardLabel": null,
      "integrationOperatorCardSeverity": null,
      "integrationOperatorCardOrder": null,
      "integrationOperatorCardReasonCodes": null,
      "integrationExportPacketStatus": null,
      "integrationExportPacketLabel": null,
      "integrationExportPacketCompleteness": null,
      "integrationExportPacketMissing": null,
      "integrationExportPacketReady": null,
      "integrationExportPacketSummaryStatus": null,
      "integrationExportPacketSummaryLabel": null,
      "integrationExportPacketSummaryPriority": null,
      "integrationExportPacketSummaryReasonCodes": null,
      "integrationExportPacketSummaryBlocking": null,
      "exportReadiness": "blocked",
      "exportReadinessLabel": "Export Blocked",
      "exportReadinessReasonCodes": [],
      "auditCompleteness": "partial",
      "auditCompletenessLabel": "Audit Partial"
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
- `Provenance.titleQuote.warningFamilies` surfaces deterministic family rollups such as `provider`, `snapshot`, `fallback`, `compatibility`, and `availability` for the warning codes present in the response.
- `Provenance.titleQuote.warningFamilySummary` surfaces the active family list in compact deterministic form, and `warningFamilySummaryLabel` surfaces a human-readable label derived only from that active family list.
- `Provenance.titleQuote.warningFamilyDisplayPriority` selects a single display family using the fixed priority order `fallback`, `availability`, `provider`, `compatibility`, `snapshot`.
- `Provenance.titleQuote.warningFamilyDisplayLabel` surfaces the compact label for the selected display family using `Fallback Warning`, `Availability Warning`, `Provider Warning`, `Compatibility Warning`, or `Snapshot Warning`.
- `Provenance.titleQuote.warningFamilyDisplaySeverity` surfaces the highest applicable severity for the selected display family using existing warning state only, and otherwise falls back to the overall warning-summary severity.
- `Provenance.titleQuote.warningFamilyDisplayCount` surfaces the selected display family's count from `warningFamilyCounts`, or `0` when no family is active.
- `Provenance.titleQuote.warningSummary` surfaces compact grouped warning state with `highestSeverity`, `hasCritical`, `hasWarning`, and `hasInfo`.
- `Provenance.titleQuote.warningCounts` surfaces deterministic grouped warning counts for `critical`, `warning`, `info`, and `total`.
- `Provenance.titleQuote.warningFamilyCounts` surfaces deterministic counts for the current warning families `provider`, `snapshot`, `fallback`, `compatibility`, and `availability`.
- `Provenance.titleQuote.exportArtifactId` and `exportArtifactType` surface export-reference metadata when the normalized quote source provides it and are otherwise `null`.
- `Provenance.titleQuote.exportTraceKey` surfaces a deterministic trace key derived from `exportArtifactType` plus `exportArtifactId` when available, and otherwise falls back to a provider-plus-quote-reference key when one exists.
- `Provenance.titleQuote.sourceTraceKey` surfaces a compact deterministic provider-status-source trace reference for downstream audit and report joins.
- `Provenance.titleQuote.snapshotTraceKey` surfaces a deterministic provider-snapshot-reference trace key when snapshot metadata is available and is otherwise `null`.
- `Provenance.titleQuote.sourceEventType` and `snapshotEventType` surface deterministic event labels derived from the normalized status and snapshot availability.
- `Provenance.titleQuote.sourceEventRef` and `snapshotEventRef` surface audit-safe event-style references derived only from the existing normalized source and snapshot trace keys.
- `Provenance.titleQuote.sourceEventBundle` groups the current source and snapshot event labels plus refs into one compact deterministic object for downstream display and filtering.
- `Provenance.titleQuote.sourceEventBundle.hasSourceEvent` is `true` only when both `sourceEventType` and `sourceEventRef` are present and non-empty.
- `Provenance.titleQuote.sourceEventBundle.hasSnapshotEvent` is `true` only when both `snapshotEventType` and `snapshotEventRef` are present and non-empty.
- `Provenance.titleQuote.sourceEventBundle.isComplete` is `true` only when both source and snapshot events are present.
- `Provenance.titleQuote.sourceEventBundle.status` is `complete`, `partial`, or `missing`, derived only from source/snapshot event presence.
- `Provenance.titleQuote.sourceEventBundle.statusLabel` is derived only from `status` using `Complete Event Bundle`, `Partial Event Bundle`, or `Missing Event Bundle`.
- `Provenance.titleQuote.integrationProvider` surfaces the scaffolded integration provider key and is `corelogic` in this slice.
- `Provenance.titleQuote.integrationMode` surfaces the normalized scaffold mode using `disabled`, `mock`, or `live`.
- `Provenance.titleQuote.integrationState` is `inactive`, `mock_ready`, `live_blocked`, or `live_ready`, derived only from deterministic CoreLogic scaffold config state.
- `Provenance.titleQuote.integrationStateLabel` is derived only from `integrationState` using `Integration Inactive`, `Mock Integration Ready`, `Live Integration Blocked`, or `Live Integration Ready`.
- `Provenance.titleQuote.integrationReasonCodes` surfaces unique deterministic config-derived reason codes in fixed order from this set only: `integration_disabled`, `mode_disabled`, `mode_mock`, `live_calls_not_allowed`, `live_credentials_missing`, and `live_mode_enabled`.
- `Provenance.titleQuote.integrationLiveReady` is `true` only when the CoreLogic scaffold is configured for live mode, live calls are explicitly allowed, and all required credential-presence checks pass; otherwise it is `false`.
- `Provenance.titleQuote.integrationLiveReadyLabel` is derived only from `integrationLiveReady` using `Live Integration Ready` or `Live Integration Not Ready`.
- `Provenance.titleQuote.integrationCredentialState` is `missing`, `partial`, or `present`, derived only from presence checks on `CORELOGIC_API_BASE_URL`, `CORELOGIC_CLIENT_ID`, and `CORELOGIC_CLIENT_SECRET`.
- `Provenance.titleQuote.integrationCredentialStateLabel` is derived only from `integrationCredentialState` using `Credentials Missing`, `Credentials Partial`, or `Credentials Present`.
- `Provenance.titleQuote.integrationGuardSummary` is `disabled`, `mock`, `blocked_missing_credentials`, `blocked_live_calls_not_allowed`, or `ready_for_live`, derived only from deterministic CoreLogic config and credential guard evaluation.
- `Provenance.titleQuote.integrationArtifactType`, `integrationArtifactId`, `integrationTraceKey`, `integrationEventType`, `integrationEventRef`, `integrationMockProfile`, and `integrationMockProfileLabel` are additive CoreLogic scaffold fields and remain `null` unless the scaffold resolves to `mock` mode.
- In `mock` mode, those fields are populated deterministically with `corelogic_mock_payload`, `corelogic-mock-title-quote-v1`, `corelogic:mock:corelogic-mock-title-quote-v1`, `corelogic_mock_title_quote`, `integration-event:corelogic:mock:corelogic-mock-title-quote-v1`, `title_quote_baseline`, and `Title Quote Baseline Mock`.
- `Provenance.titleQuote.integrationResultType`, `integrationExecutionState`, `integrationQuoteReference`, `integrationSnapshotVersion`, `integrationPayloadProfile`, `integrationEstimatedTotalTitleCost`, and `integrationCurrency` are bridged only from the internal normalized CoreLogic envelope and remain `null` unless that envelope represents a `mock_executed` result.
- In `mock` mode, those bridged fields resolve deterministically to `mock_title_quote`, `mock_executed`, `CORELOGIC-MOCK-QUOTE-001`, `mock-v1`, `title_quote_baseline`, `3700.0`, and `USD`.
- `Provenance.titleQuote.integrationEstimatedTitleFee`, `integrationEstimatedSettlementFee`, `integrationEstimatedRecordingFee`, `integrationEstimatedSearchFee`, and `integrationEstimatedMiscFee` are bridged only from the internal normalized CoreLogic envelope payload and remain `null` unless that envelope represents a `mock_executed` result.
- In `mock` mode, those fee-line bridge fields resolve deterministically to `1850.0`, `950.0`, `150.0`, `450.0`, and `300.0`.
- `Provenance.titleQuote.integrationFeeLineSum`, `integrationFeeDelta`, `integrationFeeReconciliationStatus`, `integrationFeeReconciliationLabel`, and `integrationFeeReconciliationMatch` are derived only from the existing route-visible CoreLogic fee-line bridge fields plus `integrationEstimatedTotalTitleCost`.
- In `mock` mode, those reconciliation fields resolve deterministically to `3700.0`, `0.0`, `matched`, `Fee Reconciliation Matched`, and `true`.
- `Provenance.titleQuote.integrationBundleStatus`, `integrationBundleStatusLabel`, `integrationHasArtifact`, `integrationHasTrace`, `integrationHasEvent`, and `integrationIsExportReady` are derived only from the existing route-visible CoreLogic integration bridge fields and remain `null` unless a `mock_executed` integration envelope exists.
- In `mock` mode, those bundle-utility fields resolve deterministically to `complete`, `Integration Bundle Complete`, `true`, `true`, `true`, and `true`.
- `Provenance.titleQuote.integrationExportReadiness`, `integrationExportReadinessLabel`, `integrationExportReasonCodes`, `integrationAuditCompleteness`, and `integrationAuditCompletenessLabel` are derived only from the existing route-visible CoreLogic integration bridge, bundle, and fee-reconciliation fields and remain `null` unless a `mock_executed` integration envelope exists.
- In `mock` mode, those export/audit utility fields resolve deterministically to `ready`, `Integration Export Ready`, `[]`, `complete`, and `Integration Audit Complete`.
- `Provenance.titleQuote.integrationSummaryStatus`, `integrationSummaryStatusLabel`, `integrationSummaryPriority`, `integrationSummaryPriorityLabel`, and `integrationSummaryReasonCodes` are derived only from the existing route-visible CoreLogic integration readiness, export, and audit fields and remain `null` unless a `mock_executed` integration envelope exists.
- In `mock` mode, those summary fields resolve deterministically to `ready`, `Integration Summary Ready`, `mock_ready`, `Mock Ready`, and `["summary_mock_ready"]`.
- `Provenance.titleQuote.integrationDisplayBadge`, `integrationDisplayBadgeLabel`, `integrationDisplaySeverity`, `integrationDisplayOrder`, and `integrationDisplayReason` are derived only from the existing route-visible CoreLogic integration summary, export, audit, and fee-reconciliation fields and remain `null` unless a `mock_executed` integration envelope exists.
- In `mock` mode, those display fields resolve deterministically to `mock_ready`, `Integration Mock Ready`, `info`, `5`, and `mock_ready`.
- `Provenance.titleQuote.integrationOperatorAction`, `integrationOperatorActionLabel`, `integrationOperatorActionPriority`, `integrationOperatorActionReasonCodes`, and `integrationOperatorActionBlocking` are derived only from the existing route-visible CoreLogic integration export, audit, display, and fee-reconciliation fields and remain `null` unless a `mock_executed` integration envelope exists.
- In `mock` mode, those operator-action fields resolve deterministically to `monitor_mock_state`, `Monitor Mock State`, `5`, `["operator_mock_monitor"]`, and `false`.
- `Provenance.titleQuote.integrationOperatorSnapshotStatus`, `integrationOperatorSnapshotLabel`, `integrationOperatorSnapshotSeverity`, `integrationOperatorSnapshotOrder`, and `integrationOperatorSnapshotReasonCodes` are derived only from the existing route-visible CoreLogic integration operator-action, export, audit, display, and fee-reconciliation fields and remain `null` unless an integration execution envelope exists.
- In `mock` mode, those operator-snapshot fields resolve deterministically to `monitor`, `Operator Snapshot Monitor`, `info`, `4`, and `["snapshot_monitor_only"]`.
- `Provenance.titleQuote.integrationOperatorCardStatus`, `integrationOperatorCardLabel`, `integrationOperatorCardSeverity`, `integrationOperatorCardOrder`, and `integrationOperatorCardReasonCodes` are derived only from the existing route-visible CoreLogic integration operator snapshot, action, export, audit, and fee-reconciliation fields and remain `null` unless an integration execution envelope exists.
- In `mock` mode, those operator-card fields resolve deterministically to `monitor`, `Operator Card Monitor`, `info`, `4`, and `["card_monitor_only"]`.
- `Provenance.titleQuote.integrationExportPacketStatus`, `integrationExportPacketLabel`, `integrationExportPacketCompleteness`, `integrationExportPacketMissing`, and `integrationExportPacketReady` are derived only from the existing route-visible CoreLogic integration export, bundle, operator-card, and fee-reconciliation fields and remain `null` unless an integration execution envelope exists.
- In `mock` mode, those export-packet fields resolve deterministically to `ready`, `Integration Export Packet Ready`, `complete`, `[]`, and `true`.
- `Provenance.titleQuote.integrationExportPacketSummaryStatus`, `integrationExportPacketSummaryLabel`, `integrationExportPacketSummaryPriority`, `integrationExportPacketSummaryReasonCodes`, and `integrationExportPacketSummaryBlocking` are derived only from the existing route-visible CoreLogic export-packet and operator-card fields and remain `null` unless an integration execution envelope exists.
- In `mock` mode, those export-packet summary fields resolve deterministically to `ready`, `Export Packet Summary Ready`, `3`, `["packet_summary_ready"]`, and `false`.
- `Provenance.titleQuote.exportReadiness` is `ready`, `conditional`, or `blocked`, derived only from deterministic provenance completeness and warning-state checks.
- `Provenance.titleQuote.exportReadinessLabel` is derived only from `exportReadiness` using `Export Ready`, `Conditionally Export Ready`, or `Export Blocked`.
- `Provenance.titleQuote.exportReadinessReasonCodes` surfaces unique deterministic reason codes in fixed order from this set only: `missing_export_artifact`, `missing_export_trace`, `missing_quote_reference`, `missing_snapshot_version`, `missing_source_trace`, `missing_snapshot_trace`, `missing_source_event`, `missing_snapshot_event`, `critical_warning_present`, and `warning_present`.
- `Provenance.titleQuote.auditCompleteness` is `complete`, `partial`, or `minimal`, derived only from deterministic trace, event, and snapshot-reference presence checks.
- `Provenance.titleQuote.auditCompletenessLabel` is derived only from `auditCompleteness` using `Audit Complete`, `Audit Partial`, or `Audit Minimal`.
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
