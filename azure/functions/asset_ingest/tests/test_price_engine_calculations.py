import pathlib
import sys
import unittest
from dataclasses import replace
from decimal import Decimal
import os
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_calculations import (  # noqa: E402
    build_deal_inputs,
    calculate_cash_paid_transaction_costs,
    calculate_cash_on_cash,
    calculate_financed_transaction_costs,
    calculate_irr,
    calculate_mao,
    calculate_total_points,
    calculate_total_lender_fees,
    calculate_total_title_fees,
    calculate_total_transaction_costs,
)
from price_engine_corelogic_scaffold import resolve_corelogic_integration_scaffold  # noqa: E402
from price_engine_provenance import (  # noqa: E402
    _build_integration_display_badge,
    _build_integration_display_order,
    _build_integration_display_reason,
    _build_integration_display_severity,
    _build_integration_export_packet_completeness,
    _build_integration_export_packet_missing,
    _build_integration_export_packet_ready,
    _build_integration_export_packet_summary_blocking,
    _build_integration_export_packet_summary_priority,
    _build_integration_export_packet_summary_reason_codes,
    _build_integration_export_packet_summary_status,
    _build_integration_export_packet_status,
    _build_integration_operator_action,
    _build_integration_operator_action_blocking,
    _build_integration_operator_action_priority,
    _build_integration_operator_action_reason_codes,
    _build_integration_operator_card_order,
    _build_integration_operator_card_reason_codes,
    _build_integration_operator_card_severity,
    _build_integration_operator_card_status,
    _build_integration_operator_snapshot_order,
    _build_integration_operator_snapshot_reason_codes,
    _build_integration_operator_snapshot_severity,
    _build_integration_operator_snapshot_status,
    _build_integration_summary_priority,
    _build_integration_summary_reason_codes,
    _build_integration_summary_status,
    build_price_engine_provenance,
)
from price_engine_service import calculate_price_engine  # noqa: E402
from price_engine_title_quote_context import PriceEngineTitleQuoteContext  # noqa: E402


class PriceEngineCalculationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_provider = os.environ.get("PRICE_ENGINE_TITLE_RATE_PROVIDER")
        self._original_corelogic_enabled = os.environ.get("PRICE_ENGINE_CORELOGIC_ENABLED")
        self._original_corelogic_mode = os.environ.get("PRICE_ENGINE_CORELOGIC_MODE")
        self._original_corelogic_allow_live_calls = os.environ.get("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS")
        self._original_corelogic_api_key = os.environ.get("PRICE_ENGINE_CORELOGIC_API_KEY")
        self._original_corelogic_client_id = os.environ.get("PRICE_ENGINE_CORELOGIC_CLIENT_ID")
        self._original_corelogic_api_base_url = os.environ.get("CORELOGIC_API_BASE_URL")
        self._original_corelogic_env_client_id = os.environ.get("CORELOGIC_CLIENT_ID")
        self._original_corelogic_client_secret = os.environ.get("CORELOGIC_CLIENT_SECRET")

    def tearDown(self) -> None:
        if self._original_provider is None:
            os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)
        else:
            os.environ["PRICE_ENGINE_TITLE_RATE_PROVIDER"] = self._original_provider
        if self._original_corelogic_enabled is None:
            os.environ.pop("PRICE_ENGINE_CORELOGIC_ENABLED", None)
        else:
            os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = self._original_corelogic_enabled
        if self._original_corelogic_mode is None:
            os.environ.pop("PRICE_ENGINE_CORELOGIC_MODE", None)
        else:
            os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = self._original_corelogic_mode
        if self._original_corelogic_allow_live_calls is None:
            os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)
        else:
            os.environ["PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS"] = self._original_corelogic_allow_live_calls
        if self._original_corelogic_api_key is None:
            os.environ.pop("PRICE_ENGINE_CORELOGIC_API_KEY", None)
        else:
            os.environ["PRICE_ENGINE_CORELOGIC_API_KEY"] = self._original_corelogic_api_key
        if self._original_corelogic_client_id is None:
            os.environ.pop("PRICE_ENGINE_CORELOGIC_CLIENT_ID", None)
        else:
            os.environ["PRICE_ENGINE_CORELOGIC_CLIENT_ID"] = self._original_corelogic_client_id
        if self._original_corelogic_api_base_url is None:
            os.environ.pop("CORELOGIC_API_BASE_URL", None)
        else:
            os.environ["CORELOGIC_API_BASE_URL"] = self._original_corelogic_api_base_url
        if self._original_corelogic_env_client_id is None:
            os.environ.pop("CORELOGIC_CLIENT_ID", None)
        else:
            os.environ["CORELOGIC_CLIENT_ID"] = self._original_corelogic_env_client_id
        if self._original_corelogic_client_secret is None:
            os.environ.pop("CORELOGIC_CLIENT_SECRET", None)
        else:
            os.environ["CORELOGIC_CLIENT_SECRET"] = self._original_corelogic_client_secret

    def test_core_formulas_produce_expected_outputs(self) -> None:
        inputs = build_deal_inputs(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "targetProfitMargin": 0.12,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "pointsRate": 0.02,
                "financeLenderFees": True,
                "financeTitleFees": False,
                "financePoints": True,
                "titlePremium": 1800,
                "settlementFee": 850,
                "recordingFee": 225,
                "ownerPolicy": 450,
                "lenderPolicy": 375,
                "annualInterestRate": 0.08,
                "holdingMonths": 12,
                "interestOnly": False,
                "amortizationMonths": 360,
                "exitSalePrice": 225000,
                "saleCommissionRate": 0.06,
                "sellerClosingCostRate": 0.02,
                "dispositionFee": 1500,
                "sellerConcessions": 2500,
                "otherExitCosts": 1000,
            }
        )

        self.assertEqual(calculate_total_lender_fees(inputs).quantize(Decimal("0.01")), Decimal("3825.00"))
        self.assertEqual(calculate_total_title_fees(inputs).quantize(Decimal("0.01")), Decimal("3700.00"))
        self.assertEqual(calculate_total_points(inputs).quantize(Decimal("0.01")), Decimal("1920.00"))
        self.assertEqual(calculate_total_transaction_costs(inputs).quantize(Decimal("0.01")), Decimal("16445.00"))
        self.assertEqual(calculate_cash_paid_transaction_costs(inputs).quantize(Decimal("0.01")), Decimal("3700.00"))
        self.assertEqual(calculate_financed_transaction_costs(inputs).quantize(Decimal("0.01")), Decimal("5745.00"))
        self.assertEqual(inputs.monthly_debt_service.quantize(Decimal("0.01")), Decimal("746.57"))
        self.assertEqual(inputs.total_interest_carry.quantize(Decimal("0.01")), Decimal("8108.88"))
        self.assertEqual(inputs.gross_sale_proceeds.quantize(Decimal("0.01")), Decimal("225000.00"))
        self.assertEqual(inputs.total_exit_costs.quantize(Decimal("0.01")), Decimal("23000.00"))
        self.assertEqual(inputs.net_disposition_proceeds.quantize(Decimal("0.01")), Decimal("101104.94"))
        self.assertEqual(calculate_mao(inputs).quantize(Decimal("0.01")), Decimal("112446.12"))
        self.assertEqual(calculate_cash_on_cash(inputs).quantize(Decimal("0.01")), Decimal("15.83"))
        self.assertEqual(calculate_irr(inputs).quantize(Decimal("0.01")), Decimal("77.12"))

    def test_service_uses_stub_title_quote_when_provider_is_unavailable(self) -> None:
        os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)

        metrics = calculate_price_engine(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "targetProfitMargin": 0.12,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "pointsRate": 0.02,
                "financeLenderFees": True,
                "financeTitleFees": True,
                "financePoints": True,
                "propertyState": "MO",
                "county": "Jackson",
                "city": "Kansas City",
                "postalCode": "64108",
                "endorsements": ["CPL", "T-19"],
                "transactionDate": "2026-03-18",
                "annualInterestRate": 0.08,
                "holdingMonths": 12,
                "interestOnly": False,
                "amortizationMonths": 360,
                "exitSalePrice": 225000,
                "saleCommissionRate": 0.06,
                "sellerClosingCostRate": 0.02,
                "dispositionFee": 1500,
                "sellerConcessions": 2500,
                "otherExitCosts": 1000,
            }
        )

        self.assertEqual(metrics["TotalLenderFees"], 3825.0)
        self.assertEqual(metrics["TotalTitleFees"], 0.0)
        self.assertEqual(metrics["TotalPoints"], 1920.0)
        self.assertEqual(metrics["CashPaidTransactionCosts"], 0.0)
        self.assertEqual(metrics["FinancedTransactionCosts"], 5745.0)
        self.assertEqual(metrics["TotalTransactionCosts"], 12745.0)
        self.assertEqual(metrics["CashToClose"], 61000.0)
        self.assertEqual(metrics["MonthlyDebtService"], 746.57)
        self.assertEqual(metrics["TotalInterestCarry"], 8108.88)
        self.assertEqual(metrics["DebtServiceType"], "amortized")
        self.assertEqual(metrics["GrossSaleProceeds"], 225000.0)
        self.assertEqual(metrics["TotalExitCosts"], 23000.0)
        self.assertEqual(metrics["ExitLoanPayoff"], 100895.06)
        self.assertEqual(metrics["NetDispositionProceeds"], 101104.94)
        self.assertEqual(metrics["ScenarioProfile"], "flip")
        self.assertEqual(metrics["AppliedPresetFields"], [])
        self.assertEqual(metrics["ValidationWarnings"], [])
        self.assertEqual(
            metrics["Disclaimers"]["calculation"]["message"],
            "Calculated outputs are deterministic underwriting estimates based on the inputs and modeled assumptions provided to this backend response.",
        )
        self.assertEqual(
            metrics["Disclaimers"]["dataSources"]["warnings"],
            [],
        )
        self.assertIn(
            "decision-support output only",
            metrics["Disclaimers"]["useDecision"]["message"],
        )
        self.assertEqual(
            metrics["Provenance"],
            {
                "titleQuote": {
                    "provider": "stub",
                    "status": "stub",
                    "source": "stub",
                    "quoteReference": None,
                    "snapshotVersion": None,
                    "quotedAt": None,
                    "capturedAt": None,
                    "expiresAt": None,
                    "sourceWarnings": [
                        "Stub response only. Vendor implementation remains disabled pending an approved API or documented embed bridge."
                    ],
                    "sourceWarningCodes": [
                        "stub_provider_used",
                    ],
                    "sourceWarningSeverities": [
                        "info",
                    ],
                    "warningFamilies": [
                        "provider",
                    ],
                    "warningFamilySummary": [
                        "provider",
                    ],
                    "warningFamilySummaryLabel": "provider",
                    "warningFamilyDisplayPriority": "provider",
                    "warningFamilyDisplayLabel": "Provider Warning",
                    "warningFamilyDisplaySeverity": "info",
                    "warningFamilyDisplayCount": 1,
                    "warningSummary": {
                        "highestSeverity": "info",
                        "hasCritical": False,
                        "hasWarning": False,
                        "hasInfo": True,
                    },
                    "warningCounts": {
                        "critical": 0,
                        "warning": 0,
                        "info": 1,
                        "total": 1,
                    },
                    "warningFamilyCounts": {
                        "provider": 1,
                        "snapshot": 0,
                        "fallback": 0,
                        "compatibility": 0,
                        "availability": 0,
                    },
                    "exportArtifactId": None,
                    "exportArtifactType": None,
                    "exportTraceKey": None,
                    "sourceTraceKey": "stub:stub:stub",
                    "snapshotTraceKey": None,
                    "sourceEventType": "title_quote_stub",
                    "snapshotEventType": None,
                    "sourceEventRef": "source-event:stub:stub:stub",
                    "snapshotEventRef": None,
                    "sourceEventBundle": {
                        "sourceEventType": "title_quote_stub",
                        "sourceEventRef": "source-event:stub:stub:stub",
                        "snapshotEventType": None,
                        "snapshotEventRef": None,
                        "status": "partial",
                        "statusLabel": "Partial Event Bundle",
                        "hasSourceEvent": True,
                        "hasSnapshotEvent": False,
                        "isComplete": False,
                    },
                    "integrationProvider": "corelogic",
                    "integrationMode": "disabled",
                    "integrationState": "inactive",
                    "integrationStateLabel": "Integration Inactive",
                    "integrationReasonCodes": [
                        "integration_disabled",
                        "mode_disabled",
                    ],
                    "integrationLiveReady": False,
                    "integrationLiveReadyLabel": "Live Integration Not Ready",
                    "integrationCredentialState": "missing",
                    "integrationCredentialStateLabel": "Credentials Missing",
                    "integrationGuardSummary": "disabled",
                    "integrationArtifactType": None,
                    "integrationArtifactId": None,
                    "integrationTraceKey": None,
                    "integrationEventType": None,
                    "integrationEventRef": None,
                    "integrationMockProfile": None,
                    "integrationMockProfileLabel": None,
                    "integrationResultType": None,
                    "integrationExecutionState": None,
                    "integrationQuoteReference": None,
                    "integrationSnapshotVersion": None,
                    "integrationPayloadProfile": None,
                    "integrationEstimatedTotalTitleCost": None,
                    "integrationCurrency": None,
                    "integrationEstimatedTitleFee": None,
                    "integrationEstimatedSettlementFee": None,
                    "integrationEstimatedRecordingFee": None,
                    "integrationEstimatedSearchFee": None,
                    "integrationEstimatedMiscFee": None,
                    "integrationFeeLineSum": None,
                    "integrationFeeDelta": None,
                    "integrationFeeReconciliationStatus": None,
                    "integrationFeeReconciliationLabel": None,
                    "integrationFeeReconciliationMatch": None,
                    "integrationBundleStatus": None,
                    "integrationBundleStatusLabel": None,
                    "integrationHasArtifact": None,
                    "integrationHasTrace": None,
                    "integrationHasEvent": None,
                    "integrationIsExportReady": None,
                    "integrationExportReadiness": None,
                    "integrationExportReadinessLabel": None,
                    "integrationExportReasonCodes": None,
                    "integrationAuditCompleteness": None,
                    "integrationAuditCompletenessLabel": None,
                    "integrationSummaryStatus": None,
                    "integrationSummaryStatusLabel": None,
                    "integrationSummaryPriority": None,
                    "integrationSummaryPriorityLabel": None,
                    "integrationSummaryReasonCodes": None,
                    "integrationDisplayBadge": None,
                    "integrationDisplayBadgeLabel": None,
                    "integrationDisplaySeverity": None,
                    "integrationDisplayOrder": None,
                    "integrationDisplayReason": None,
                    "integrationOperatorAction": None,
                    "integrationOperatorActionLabel": None,
                    "integrationOperatorActionPriority": None,
                    "integrationOperatorActionReasonCodes": None,
                    "integrationOperatorActionBlocking": None,
                    "integrationOperatorSnapshotStatus": None,
                    "integrationOperatorSnapshotLabel": None,
                    "integrationOperatorSnapshotSeverity": None,
                    "integrationOperatorSnapshotOrder": None,
                    "integrationOperatorSnapshotReasonCodes": None,
                    "integrationOperatorCardStatus": None,
                    "integrationOperatorCardLabel": None,
                    "integrationOperatorCardSeverity": None,
                    "integrationOperatorCardOrder": None,
                    "integrationOperatorCardReasonCodes": None,
                    "integrationExportPacketStatus": None,
                    "integrationExportPacketLabel": None,
                    "integrationExportPacketCompleteness": None,
                    "integrationExportPacketMissing": None,
                    "integrationExportPacketReady": None,
                    "integrationExportPacketSummaryStatus": None,
                    "integrationExportPacketSummaryLabel": None,
                    "integrationExportPacketSummaryPriority": None,
                    "integrationExportPacketSummaryReasonCodes": None,
                    "integrationExportPacketSummaryBlocking": None,
                    "exportReadiness": "blocked",
                    "exportReadinessLabel": "Export Blocked",
                    "exportReadinessReasonCodes": [
                        "missing_export_artifact",
                        "missing_export_trace",
                        "missing_quote_reference",
                        "missing_snapshot_version",
                        "missing_snapshot_trace",
                        "missing_snapshot_event",
                        "warning_present",
                    ],
                    "auditCompleteness": "partial",
                    "auditCompletenessLabel": "Audit Partial",
                },
                "scenario": {
                    "profile": "flip",
                    "appliedPresetFields": [],
                    "validationWarnings": [],
                },
                "trace": {
                    "generatedAt": None,
                },
            },
        )

    def test_service_applies_missing_preset_fields_without_overriding_explicit_values(self) -> None:
        os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)

        metrics = calculate_price_engine(
            {
                "strategy": "brrrr",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "pointsRate": 0.02,
                "financeLenderFees": True,
                "financeTitleFees": True,
                "financePoints": True,
                "propertyState": "MO",
                "county": "Jackson",
                "city": "Kansas City",
                "postalCode": "64108",
                "endorsements": ["CPL", "T-19"],
                "transactionDate": "2026-03-18",
                "annualInterestRate": 0.09,
            }
        )

        self.assertEqual(metrics["ScenarioProfile"], "brrrr")
        self.assertIn("holdingMonths", metrics["AppliedPresetFields"])
        self.assertIn("interestOnly", metrics["AppliedPresetFields"])
        self.assertIn("amortizationMonths", metrics["AppliedPresetFields"])
        self.assertIn("saleCommissionRate", metrics["AppliedPresetFields"])
        self.assertNotIn("annualInterestRate", metrics["AppliedPresetFields"])
        self.assertTrue(metrics["ValidationWarnings"])
        self.assertTrue(metrics["Disclaimers"]["calculation"]["warnings"])
        self.assertTrue(metrics["Disclaimers"]["useDecision"]["warnings"])
        self.assertEqual(metrics["Provenance"]["scenario"]["profile"], "brrrr")
        self.assertTrue(metrics["Provenance"]["scenario"]["appliedPresetFields"])
        self.assertTrue(metrics["Provenance"]["scenario"]["validationWarnings"])

    def test_service_uses_liberty_quote_when_selected(self) -> None:
        os.environ["PRICE_ENGINE_TITLE_RATE_PROVIDER"] = "liberty"

        metrics = calculate_price_engine(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "targetProfitMargin": 0.12,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "pointsRate": 0.02,
                "financeLenderFees": True,
                "financeTitleFees": True,
                "financePoints": True,
                "propertyState": "MO",
                "county": "Jackson",
                "city": "Kansas City",
                "postalCode": "64108",
                "endorsements": ["CPL", "T-19"],
                "transactionDate": "2026-03-18",
                "annualInterestRate": 0.08,
                "holdingMonths": 12,
                "interestOnly": False,
                "amortizationMonths": 360,
                "exitSalePrice": 225000,
                "saleCommissionRate": 0.06,
                "sellerClosingCostRate": 0.02,
                "dispositionFee": 1500,
                "sellerConcessions": 2500,
                "otherExitCosts": 1000,
                "providerContext": {
                    "requestedProvider": "liberty",
                    "libertySnapshot": {
                        "quoteReference": "LIA-QUOTE-001",
                        "snapshotVersion": "v1",
                        "quotedAt": "2026-03-18T15:45:00Z",
                        "capturedAt": "2026-03-18T15:46:00Z",
                        "source": "liberty_iframe_snapshot",
                        "exportArtifactId": "liberty-export-001",
                        "exportArtifactType": "title_quote_snapshot",
                        "fees": {
                            "titlePremium": 1800,
                            "settlementFee": 850,
                            "recordingFee": 225,
                            "ownerPolicy": 450,
                            "lenderPolicy": 375,
                        },
                    },
                },
            }
        )

        self.assertEqual(metrics["TotalTitleFees"], 3700.0)
        self.assertEqual(metrics["TotalTransactionCosts"], 16445.0)
        self.assertEqual(metrics["CashPaidTransactionCosts"], 0.0)
        self.assertEqual(metrics["FinancedTransactionCosts"], 9445.0)
        self.assertEqual(metrics["ScenarioProfile"], "flip")
        self.assertEqual(metrics["AppliedPresetFields"], [])
        self.assertEqual(metrics["Disclaimers"]["dataSources"]["warnings"], [])
        self.assertEqual(
            metrics["Provenance"]["titleQuote"],
            {
                "provider": "liberty",
                "status": "quoted",
                "source": "liberty_iframe_snapshot",
                "quoteReference": "LIA-QUOTE-001",
                "snapshotVersion": "v1",
                "quotedAt": "2026-03-18T15:45:00Z",
                "capturedAt": "2026-03-18T15:46:00Z",
                "expiresAt": None,
                "sourceWarnings": [
                    "Liberty public iframe currently exposes a tokenized app launch rather than a documented backend quote API."
                ],
                "sourceWarningCodes": [
                    "liberty_iframe_no_backend_api",
                ],
                "sourceWarningSeverities": [
                    "warning",
                ],
                "warningFamilies": [
                    "provider",
                ],
                "warningFamilySummary": [
                    "provider",
                ],
                "warningFamilySummaryLabel": "provider",
                "warningFamilyDisplayPriority": "provider",
                "warningFamilyDisplayLabel": "Provider Warning",
                "warningFamilyDisplaySeverity": "warning",
                "warningFamilyDisplayCount": 1,
                "warningSummary": {
                    "highestSeverity": "warning",
                    "hasCritical": False,
                    "hasWarning": True,
                    "hasInfo": False,
                },
                "warningCounts": {
                    "critical": 0,
                    "warning": 1,
                    "info": 0,
                    "total": 1,
                },
                "warningFamilyCounts": {
                    "provider": 1,
                    "snapshot": 0,
                    "fallback": 0,
                    "compatibility": 0,
                    "availability": 0,
                },
                "exportArtifactId": "liberty-export-001",
                "exportArtifactType": "title_quote_snapshot",
                "exportTraceKey": "liberty:title_quote_snapshot:liberty-export-001",
                "sourceTraceKey": "liberty:quoted:liberty_iframe_snapshot",
                "snapshotTraceKey": "liberty:v1:LIA-QUOTE-001",
                "sourceEventType": "title_quote_source",
                "snapshotEventType": "title_quote_snapshot",
                "sourceEventRef": "source-event:liberty:quoted:liberty_iframe_snapshot",
                "snapshotEventRef": "snapshot-event:liberty:v1:LIA-QUOTE-001",
                "sourceEventBundle": {
                    "sourceEventType": "title_quote_source",
                    "sourceEventRef": "source-event:liberty:quoted:liberty_iframe_snapshot",
                    "snapshotEventType": "title_quote_snapshot",
                    "snapshotEventRef": "snapshot-event:liberty:v1:LIA-QUOTE-001",
                    "status": "complete",
                    "statusLabel": "Complete Event Bundle",
                    "hasSourceEvent": True,
                    "hasSnapshotEvent": True,
                    "isComplete": True,
                },
                "integrationProvider": "corelogic",
                "integrationMode": "disabled",
                "integrationState": "inactive",
                "integrationStateLabel": "Integration Inactive",
                "integrationReasonCodes": [
                    "integration_disabled",
                    "mode_disabled",
                ],
                "integrationLiveReady": False,
                "integrationLiveReadyLabel": "Live Integration Not Ready",
                "integrationCredentialState": "missing",
                "integrationCredentialStateLabel": "Credentials Missing",
                "integrationGuardSummary": "disabled",
                "integrationArtifactType": None,
                "integrationArtifactId": None,
                "integrationTraceKey": None,
                "integrationEventType": None,
                "integrationEventRef": None,
                "integrationMockProfile": None,
                "integrationMockProfileLabel": None,
                "integrationResultType": None,
                "integrationExecutionState": None,
                "integrationQuoteReference": None,
                "integrationSnapshotVersion": None,
                "integrationPayloadProfile": None,
                "integrationEstimatedTotalTitleCost": None,
                "integrationCurrency": None,
                "integrationEstimatedTitleFee": None,
                "integrationEstimatedSettlementFee": None,
                "integrationEstimatedRecordingFee": None,
                "integrationEstimatedSearchFee": None,
                "integrationEstimatedMiscFee": None,
                "integrationFeeLineSum": None,
                "integrationFeeDelta": None,
                "integrationFeeReconciliationStatus": None,
                "integrationFeeReconciliationLabel": None,
                "integrationFeeReconciliationMatch": None,
                "integrationBundleStatus": None,
                "integrationBundleStatusLabel": None,
                "integrationHasArtifact": None,
                "integrationHasTrace": None,
                "integrationHasEvent": None,
                "integrationIsExportReady": None,
                "integrationExportReadiness": None,
                "integrationExportReadinessLabel": None,
                "integrationExportReasonCodes": None,
                "integrationAuditCompleteness": None,
                "integrationAuditCompletenessLabel": None,
                "integrationSummaryStatus": None,
                "integrationSummaryStatusLabel": None,
                "integrationSummaryPriority": None,
                "integrationSummaryPriorityLabel": None,
                "integrationSummaryReasonCodes": None,
                "integrationDisplayBadge": None,
                "integrationDisplayBadgeLabel": None,
                "integrationDisplaySeverity": None,
                "integrationDisplayOrder": None,
                "integrationDisplayReason": None,
                "integrationOperatorAction": None,
                "integrationOperatorActionLabel": None,
                "integrationOperatorActionPriority": None,
                "integrationOperatorActionReasonCodes": None,
                "integrationOperatorActionBlocking": None,
                "integrationOperatorSnapshotStatus": None,
                "integrationOperatorSnapshotLabel": None,
                "integrationOperatorSnapshotSeverity": None,
                "integrationOperatorSnapshotOrder": None,
                "integrationOperatorSnapshotReasonCodes": None,
                "integrationOperatorCardStatus": None,
                "integrationOperatorCardLabel": None,
                "integrationOperatorCardSeverity": None,
                "integrationOperatorCardOrder": None,
                "integrationOperatorCardReasonCodes": None,
                "integrationExportPacketStatus": None,
                "integrationExportPacketLabel": None,
                "integrationExportPacketCompleteness": None,
                "integrationExportPacketMissing": None,
                "integrationExportPacketReady": None,
                "integrationExportPacketSummaryStatus": None,
                "integrationExportPacketSummaryLabel": None,
                "integrationExportPacketSummaryPriority": None,
                "integrationExportPacketSummaryReasonCodes": None,
                "integrationExportPacketSummaryBlocking": None,
                "exportReadiness": "conditional",
                "exportReadinessLabel": "Conditionally Export Ready",
                "exportReadinessReasonCodes": [
                    "warning_present",
                ],
                "auditCompleteness": "complete",
                "auditCompletenessLabel": "Audit Complete",
            },
        )
        self.assertEqual(metrics["Provenance"]["trace"]["generatedAt"], None)

    def test_service_amplifies_disclaimer_warning_when_liberty_fallback_stub_is_used(self) -> None:
        os.environ["PRICE_ENGINE_TITLE_RATE_PROVIDER"] = "liberty"

        metrics = calculate_price_engine(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "targetProfitMargin": 0.12,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "pointsRate": 0.02,
                "financeLenderFees": True,
                "financeTitleFees": True,
                "financePoints": True,
                "propertyState": "MO",
                "county": "Jackson",
                "city": "Kansas City",
                "postalCode": "64108",
                "endorsements": ["CPL", "T-19"],
                "transactionDate": "2026-03-18",
                "annualInterestRate": 0.08,
                "holdingMonths": 12,
                "interestOnly": False,
                "amortizationMonths": 360,
                "exitSalePrice": 225000,
                "saleCommissionRate": 0.06,
                "sellerClosingCostRate": 0.02,
                "dispositionFee": 1500,
                "sellerConcessions": 2500,
                "otherExitCosts": 1000,
                "providerContext": {
                    "requestedProvider": "liberty",
                },
            }
        )

        self.assertEqual(metrics["TotalTitleFees"], 0.0)
        self.assertTrue(metrics["Disclaimers"]["dataSources"]["warnings"])
        self.assertTrue(metrics["Disclaimers"]["useDecision"]["warnings"])
        self.assertEqual(
            metrics["Provenance"]["titleQuote"],
            {
                "provider": "liberty",
                "status": "fallback_stub",
                "source": "liberty_iframe_snapshot",
                "quoteReference": None,
                "snapshotVersion": None,
                "quotedAt": None,
                "capturedAt": None,
                "expiresAt": None,
                "sourceWarnings": [
                    "Liberty quote retrieval is unavailable because no approved Liberty snapshot was provided to the ingest path.",
                    "No order was placed and no unsupported browser automation or scraping was attempted.",
                ],
                "sourceWarningCodes": [
                    "fallback_stub_used",
                    "quote_source_unavailable",
                ],
                "sourceWarningSeverities": [
                    "warning",
                    "critical",
                ],
                "warningFamilies": [
                    "fallback",
                    "availability",
                ],
                "warningFamilySummary": [
                    "fallback",
                    "availability",
                ],
                "warningFamilySummaryLabel": "fallback, availability",
                "warningFamilyDisplayPriority": "fallback",
                "warningFamilyDisplayLabel": "Fallback Warning",
                "warningFamilyDisplaySeverity": "warning",
                "warningFamilyDisplayCount": 1,
                "warningSummary": {
                    "highestSeverity": "critical",
                    "hasCritical": True,
                    "hasWarning": True,
                    "hasInfo": False,
                },
                "warningCounts": {
                    "critical": 1,
                    "warning": 1,
                    "info": 0,
                    "total": 2,
                },
                "warningFamilyCounts": {
                    "provider": 0,
                    "snapshot": 0,
                    "fallback": 1,
                    "compatibility": 0,
                    "availability": 1,
                },
                "exportArtifactId": None,
                "exportArtifactType": None,
                "exportTraceKey": None,
                "sourceTraceKey": "liberty:fallback_stub:liberty_iframe_snapshot",
                "snapshotTraceKey": None,
                "sourceEventType": "title_quote_fallback",
                "snapshotEventType": None,
                "sourceEventRef": "source-event:liberty:fallback_stub:liberty_iframe_snapshot",
                "snapshotEventRef": None,
                "sourceEventBundle": {
                    "sourceEventType": "title_quote_fallback",
                    "sourceEventRef": "source-event:liberty:fallback_stub:liberty_iframe_snapshot",
                    "snapshotEventType": None,
                    "snapshotEventRef": None,
                    "status": "partial",
                    "statusLabel": "Partial Event Bundle",
                    "hasSourceEvent": True,
                    "hasSnapshotEvent": False,
                    "isComplete": False,
                },
                "integrationProvider": "corelogic",
                "integrationMode": "disabled",
                "integrationState": "inactive",
                "integrationStateLabel": "Integration Inactive",
                "integrationReasonCodes": [
                    "integration_disabled",
                    "mode_disabled",
                ],
                "integrationLiveReady": False,
                "integrationLiveReadyLabel": "Live Integration Not Ready",
                "integrationCredentialState": "missing",
                "integrationCredentialStateLabel": "Credentials Missing",
                "integrationGuardSummary": "disabled",
                "integrationArtifactType": None,
                "integrationArtifactId": None,
                "integrationTraceKey": None,
                "integrationEventType": None,
                "integrationEventRef": None,
                "integrationMockProfile": None,
                "integrationMockProfileLabel": None,
                "integrationResultType": None,
                "integrationExecutionState": None,
                "integrationQuoteReference": None,
                "integrationSnapshotVersion": None,
                "integrationPayloadProfile": None,
                "integrationEstimatedTotalTitleCost": None,
                "integrationCurrency": None,
                "integrationEstimatedTitleFee": None,
                "integrationEstimatedSettlementFee": None,
                "integrationEstimatedRecordingFee": None,
                "integrationEstimatedSearchFee": None,
                "integrationEstimatedMiscFee": None,
                "integrationFeeLineSum": None,
                "integrationFeeDelta": None,
                "integrationFeeReconciliationStatus": None,
                "integrationFeeReconciliationLabel": None,
                "integrationFeeReconciliationMatch": None,
                "integrationBundleStatus": None,
                "integrationBundleStatusLabel": None,
                "integrationHasArtifact": None,
                "integrationHasTrace": None,
                "integrationHasEvent": None,
                "integrationIsExportReady": None,
                "integrationExportReadiness": None,
                "integrationExportReadinessLabel": None,
                "integrationExportReasonCodes": None,
                "integrationAuditCompleteness": None,
                "integrationAuditCompletenessLabel": None,
                "integrationSummaryStatus": None,
                "integrationSummaryStatusLabel": None,
                "integrationSummaryPriority": None,
                "integrationSummaryPriorityLabel": None,
                "integrationSummaryReasonCodes": None,
                "integrationDisplayBadge": None,
                "integrationDisplayBadgeLabel": None,
                "integrationDisplaySeverity": None,
                "integrationDisplayOrder": None,
                "integrationDisplayReason": None,
                "integrationOperatorAction": None,
                "integrationOperatorActionLabel": None,
                "integrationOperatorActionPriority": None,
                "integrationOperatorActionReasonCodes": None,
                "integrationOperatorActionBlocking": None,
                "integrationOperatorSnapshotStatus": None,
                "integrationOperatorSnapshotLabel": None,
                "integrationOperatorSnapshotSeverity": None,
                "integrationOperatorSnapshotOrder": None,
                "integrationOperatorSnapshotReasonCodes": None,
                "integrationOperatorCardStatus": None,
                "integrationOperatorCardLabel": None,
                "integrationOperatorCardSeverity": None,
                "integrationOperatorCardOrder": None,
                "integrationOperatorCardReasonCodes": None,
                "integrationExportPacketStatus": None,
                "integrationExportPacketLabel": None,
                "integrationExportPacketCompleteness": None,
                "integrationExportPacketMissing": None,
                "integrationExportPacketReady": None,
                "integrationExportPacketSummaryStatus": None,
                "integrationExportPacketSummaryLabel": None,
                "integrationExportPacketSummaryPriority": None,
                "integrationExportPacketSummaryReasonCodes": None,
                "integrationExportPacketSummaryBlocking": None,
                "exportReadiness": "blocked",
                "exportReadinessLabel": "Export Blocked",
                "exportReadinessReasonCodes": [
                    "missing_export_artifact",
                    "missing_export_trace",
                    "missing_quote_reference",
                    "missing_snapshot_version",
                    "missing_snapshot_trace",
                    "missing_snapshot_event",
                    "critical_warning_present",
                ],
                "auditCompleteness": "partial",
                "auditCompletenessLabel": "Audit Partial",
            },
        )

    def test_source_event_bundle_status_is_partial_when_only_snapshot_event_exists(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="not_requested",
                quote_reference="LIA-QUOTE-ONLY",
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={
                    "snapshotVersion": "v1",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayPriority"], None)
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayLabel"], None)
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplaySeverity"], None)
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayCount"], 0)
        self.assertEqual(
            provenance["titleQuote"]["sourceEventBundle"],
            {
                "sourceEventType": None,
                "sourceEventRef": None,
                "snapshotEventType": "title_quote_snapshot",
                "snapshotEventRef": "snapshot-event:liberty:v1:LIA-QUOTE-ONLY",
                "status": "partial",
                "statusLabel": "Partial Event Bundle",
                "hasSourceEvent": False,
                "hasSnapshotEvent": True,
                "isComplete": False,
            },
        )
        self.assertEqual(provenance["titleQuote"]["exportReadiness"], "blocked")
        self.assertEqual(provenance["titleQuote"]["auditCompleteness"], "partial")
        self.assertEqual(provenance["titleQuote"]["integrationState"], "inactive")
        self.assertFalse(provenance["titleQuote"]["integrationLiveReady"])
        self.assertEqual(provenance["titleQuote"]["integrationGuardSummary"], "disabled")
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactType"])
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactId"])
        self.assertIsNone(provenance["titleQuote"]["integrationTraceKey"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventType"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventRef"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfileLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationResultType"])
        self.assertIsNone(provenance["titleQuote"]["integrationExecutionState"])
        self.assertIsNone(provenance["titleQuote"]["integrationQuoteReference"])
        self.assertIsNone(provenance["titleQuote"]["integrationSnapshotVersion"])
        self.assertIsNone(provenance["titleQuote"]["integrationPayloadProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedTotalTitleCost"])
        self.assertIsNone(provenance["titleQuote"]["integrationCurrency"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedTitleFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedSettlementFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedRecordingFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedSearchFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedMiscFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeLineSum"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeDelta"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationMatch"])
        self.assertIsNone(provenance["titleQuote"]["integrationBundleStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationBundleStatusLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasTrace"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasEvent"])
        self.assertIsNone(provenance["titleQuote"]["integrationIsExportReady"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReadiness"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReadinessLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationAuditCompleteness"])
        self.assertIsNone(provenance["titleQuote"]["integrationAuditCompletenessLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryStatusLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryPriorityLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayBadge"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayBadgeLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplaySeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayReason"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorAction"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionBlocking"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotSeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardSeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketCompleteness"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketMissing"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketReady"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryBlocking"])

    def test_source_event_bundle_status_is_missing_when_no_events_exist(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key=None,
                status="not_requested",
                quote_reference=None,
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={},
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayPriority"], None)
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayLabel"], None)
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplaySeverity"], None)
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayCount"], 0)
        self.assertEqual(
            provenance["titleQuote"]["sourceEventBundle"],
            {
                "sourceEventType": None,
                "sourceEventRef": None,
                "snapshotEventType": None,
                "snapshotEventRef": None,
                "status": "missing",
                "statusLabel": "Missing Event Bundle",
                "hasSourceEvent": False,
                "hasSnapshotEvent": False,
                "isComplete": False,
            },
        )
        self.assertEqual(provenance["titleQuote"]["exportReadiness"], "blocked")
        self.assertEqual(provenance["titleQuote"]["auditCompleteness"], "partial")
        self.assertEqual(
            provenance["titleQuote"]["integrationReasonCodes"],
            ["integration_disabled", "mode_disabled"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationCredentialState"], "missing")
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactType"])
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactId"])
        self.assertIsNone(provenance["titleQuote"]["integrationTraceKey"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventType"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventRef"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfileLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationResultType"])
        self.assertIsNone(provenance["titleQuote"]["integrationExecutionState"])
        self.assertIsNone(provenance["titleQuote"]["integrationQuoteReference"])
        self.assertIsNone(provenance["titleQuote"]["integrationSnapshotVersion"])
        self.assertIsNone(provenance["titleQuote"]["integrationPayloadProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedTotalTitleCost"])
        self.assertIsNone(provenance["titleQuote"]["integrationCurrency"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedTitleFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedSettlementFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedRecordingFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedSearchFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedMiscFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeLineSum"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeDelta"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationMatch"])
        self.assertIsNone(provenance["titleQuote"]["integrationBundleStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationBundleStatusLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasTrace"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasEvent"])
        self.assertIsNone(provenance["titleQuote"]["integrationIsExportReady"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReadiness"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReadinessLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationAuditCompleteness"])
        self.assertIsNone(provenance["titleQuote"]["integrationAuditCompletenessLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryStatusLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryPriorityLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayBadge"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayBadgeLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplaySeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayReason"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorAction"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionBlocking"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotSeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardSeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketCompleteness"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketMissing"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketReady"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryBlocking"])

    def test_warning_family_display_priority_honors_exact_priority_order(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="fallback_stub",
                quote_reference=None,
                expires_at=None,
                warnings=[
                    "Legacy Liberty quote alias was normalized into the canonical snapshot ingest shape.",
                    "Liberty quote retrieval is unavailable because no approved Liberty snapshot was provided to the ingest path.",
                ],
                assumptions=[],
                provider_context={
                    "source": "liberty_iframe_snapshot",
                    "snapshotVersion": "legacy-v0",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(
            provenance["titleQuote"]["warningFamilies"],
            ["fallback", "availability", "compatibility"],
        )
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayPriority"], "fallback")
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayLabel"], "Fallback Warning")
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplaySeverity"], "warning")
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayCount"], 1)

    def test_warning_family_display_severity_uses_selected_family_severity(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="quoted",
                quote_reference="LIA-SNAPSHOT-1",
                expires_at="2026-03-18T15:00:00Z",
                warnings=[],
                assumptions=[],
                provider_context={
                    "source": "liberty_iframe_snapshot",
                    "snapshotVersion": "v1",
                    "quotedAt": "2026-03-18T15:45:00Z",
                    "capturedAt": "2026-03-18T15:46:00Z",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["warningFamilies"], ["snapshot"])
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayPriority"], "snapshot")
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayLabel"], "Snapshot Warning")
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplaySeverity"], "critical")
        self.assertEqual(provenance["titleQuote"]["warningFamilyDisplayCount"], 1)

    def test_export_readiness_is_ready_when_provenance_is_fully_populated_without_warnings(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="quoted",
                quote_reference="LIA-QUOTE-READY",
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={
                    "source": "provider_quote",
                    "snapshotVersion": "v2",
                    "quotedAt": "2026-03-18T15:45:00Z",
                    "capturedAt": "2026-03-18T15:46:00Z",
                    "exportArtifactId": "artifact-123",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["exportReadiness"], "ready")
        self.assertEqual(provenance["titleQuote"]["exportReadinessLabel"], "Export Ready")
        self.assertEqual(provenance["titleQuote"]["exportReadinessReasonCodes"], [])
        self.assertEqual(provenance["titleQuote"]["auditCompleteness"], "complete")
        self.assertEqual(provenance["titleQuote"]["auditCompletenessLabel"], "Audit Complete")

    def test_export_readiness_is_blocked_when_export_artifact_or_trace_is_missing(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="quoted",
                quote_reference="LIA-QUOTE-BLOCKED",
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={
                    "source": "provider_quote",
                    "snapshotVersion": "v2",
                    "quotedAt": "2026-03-18T15:45:00Z",
                    "capturedAt": "2026-03-18T15:46:00Z",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["exportReadiness"], "blocked")
        self.assertEqual(
            provenance["titleQuote"]["exportReadinessReasonCodes"],
            [
                "missing_export_artifact",
            ],
        )

    def test_export_readiness_is_blocked_when_critical_warning_is_present(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="quoted",
                quote_reference="LIA-QUOTE-EXPIRED",
                expires_at="2026-03-18T15:00:00Z",
                warnings=[],
                assumptions=[],
                provider_context={
                    "source": "provider_quote",
                    "snapshotVersion": "v1",
                    "quotedAt": "2026-03-18T15:45:00Z",
                    "capturedAt": "2026-03-18T15:46:00Z",
                    "exportArtifactId": "artifact-123",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["exportReadiness"], "blocked")
        self.assertIn("critical_warning_present", provenance["titleQuote"]["exportReadinessReasonCodes"])

    def test_export_readiness_is_conditional_when_source_or_snapshot_event_is_missing(self) -> None:
        source_only = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="stub",
                status="stub",
                quote_reference=None,
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={
                    "source": "stub",
                    "exportArtifactId": "artifact-123",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )
        snapshot_only = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="not_requested",
                quote_reference="LIA-QUOTE-SNAPSHOT",
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={
                    "snapshotVersion": "v1",
                    "capturedAt": "2026-03-18T15:46:00Z",
                    "exportArtifactId": "artifact-123",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(source_only["titleQuote"]["sourceEventBundle"]["status"], "partial")
        self.assertEqual(snapshot_only["titleQuote"]["sourceEventBundle"]["status"], "partial")
        self.assertEqual(source_only["titleQuote"]["exportReadiness"], "blocked")
        self.assertEqual(snapshot_only["titleQuote"]["exportReadiness"], "conditional")
        self.assertIn("missing_source_event", snapshot_only["titleQuote"]["exportReadinessReasonCodes"])

    def test_export_readiness_is_conditional_when_only_non_critical_warning_exists(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="quoted",
                quote_reference="LIA-QUOTE-WARN",
                expires_at=None,
                warnings=[
                    "Liberty public iframe currently exposes a tokenized app launch rather than a documented backend quote API."
                ],
                assumptions=[],
                provider_context={
                    "source": "liberty_iframe_snapshot",
                    "snapshotVersion": "v1",
                    "quotedAt": "2026-03-18T15:45:00Z",
                    "capturedAt": "2026-03-18T15:46:00Z",
                    "exportArtifactId": "artifact-123",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["exportReadiness"], "conditional")
        self.assertEqual(provenance["titleQuote"]["exportReadinessReasonCodes"], ["warning_present"])

    def test_audit_completeness_is_partial_when_only_some_audit_signals_exist(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="liberty",
                status="quoted",
                quote_reference="LIA-QUOTE-PARTIAL",
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={
                    "source": "provider_quote",
                    "exportArtifactId": "artifact-123",
                    "exportArtifactType": "title_quote_snapshot",
                },
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["auditCompleteness"], "partial")

    def test_export_readiness_reason_codes_use_exact_deterministic_order(self) -> None:
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key=None,
                status="not_requested",
                quote_reference=None,
                expires_at=None,
                warnings=["Stub response only. Vendor implementation remains disabled pending an approved API or documented embed bridge."],
                assumptions=[],
                provider_context={},
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(
            provenance["titleQuote"]["exportReadinessReasonCodes"],
            [
                "missing_export_artifact",
                "missing_export_trace",
                "missing_quote_reference",
                "missing_snapshot_version",
                "missing_snapshot_trace",
                "missing_source_event",
                "missing_snapshot_event",
            ],
        )

    def test_corelogic_scaffold_defaults_to_inactive_and_never_executes_provider(self) -> None:
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ENABLED", None)
        os.environ.pop("PRICE_ENGINE_CORELOGIC_MODE", None)
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)

        probe = {"called": 0}

        def _live_executor() -> None:
            probe["called"] += 1

        scaffold = resolve_corelogic_integration_scaffold({}, live_executor=_live_executor)

        self.assertEqual(scaffold.mode, "disabled")
        self.assertEqual(scaffold.state, "inactive")
        self.assertEqual(scaffold.reason_codes, ["integration_disabled", "mode_disabled"])
        self.assertFalse(scaffold.live_ready)
        self.assertEqual(scaffold.live_ready_label, "Live Integration Not Ready")
        self.assertEqual(scaffold.credential_state, "missing")
        self.assertEqual(scaffold.credential_state_label, "Credentials Missing")
        self.assertEqual(scaffold.guard_summary, "disabled")
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)
        self.assertEqual(
            scaffold.normalized_result,
            {
                "provider": "corelogic",
                "mode": "disabled",
                "executionState": "not_executed",
                "resultType": "none",
                "artifactType": None,
                "artifactId": None,
                "traceKey": None,
                "eventType": None,
                "eventRef": None,
                "quoteReference": None,
                "snapshotVersion": None,
                "warnings": [],
                "warningCodes": [],
                "warningSeverities": [],
                "warningFamilies": [],
                "payload": None,
            },
        )
        self.assertEqual(probe["called"], 0)

    def test_corelogic_scaffold_mock_mode_is_ready_without_network_calls(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)

        probe = {"called": 0}

        def _live_executor() -> None:
            probe["called"] += 1

        scaffold = resolve_corelogic_integration_scaffold({}, live_executor=_live_executor)

        self.assertEqual(scaffold.mode, "mock")
        self.assertEqual(scaffold.state, "mock_ready")
        self.assertEqual(scaffold.reason_codes, ["mode_mock"])
        self.assertFalse(scaffold.live_ready)
        self.assertEqual(scaffold.live_ready_label, "Live Integration Not Ready")
        self.assertEqual(scaffold.credential_state, "missing")
        self.assertEqual(scaffold.credential_state_label, "Credentials Missing")
        self.assertEqual(scaffold.guard_summary, "mock")
        self.assertEqual(scaffold.artifact_type, "corelogic_mock_payload")
        self.assertEqual(scaffold.artifact_id, "corelogic-mock-title-quote-v1")
        self.assertEqual(scaffold.trace_key, "corelogic:mock:corelogic-mock-title-quote-v1")
        self.assertEqual(scaffold.event_type, "corelogic_mock_title_quote")
        self.assertEqual(scaffold.event_ref, "integration-event:corelogic:mock:corelogic-mock-title-quote-v1")
        self.assertEqual(scaffold.mock_profile, "title_quote_baseline")
        self.assertEqual(scaffold.mock_profile_label, "Title Quote Baseline Mock")
        self.assertIsNotNone(scaffold.mock_payload)
        self.assertEqual(
            scaffold.normalized_result,
            {
                "provider": "corelogic",
                "mode": "mock",
                "executionState": "mock_executed",
                "resultType": "mock_title_quote",
                "artifactType": "corelogic_mock_payload",
                "artifactId": "corelogic-mock-title-quote-v1",
                "traceKey": "corelogic:mock:corelogic-mock-title-quote-v1",
                "eventType": "corelogic_mock_title_quote",
                "eventRef": "integration-event:corelogic:mock:corelogic-mock-title-quote-v1",
                "quoteReference": "CORELOGIC-MOCK-QUOTE-001",
                "snapshotVersion": "mock-v1",
                "warnings": [],
                "warningCodes": [],
                "warningSeverities": [],
                "warningFamilies": [],
                "payload": {
                    "estimatedTitleFee": 1850.0,
                    "estimatedSettlementFee": 950.0,
                    "estimatedRecordingFee": 150.0,
                    "estimatedSearchFee": 450.0,
                    "estimatedMiscFee": 300.0,
                    "estimatedTotalTitleCost": 3700.0,
                    "currency": "USD",
                    "profile": "title_quote_baseline",
                },
            },
        )
        self.assertEqual(probe["called"], 0)

    def test_corelogic_scaffold_live_mode_without_allow_live_calls_is_blocked(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "live"
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)

        scaffold = resolve_corelogic_integration_scaffold({})

        self.assertEqual(scaffold.state, "live_blocked")
        self.assertEqual(
            scaffold.reason_codes,
            ["live_calls_not_allowed", "live_mode_enabled"],
        )
        self.assertFalse(scaffold.live_ready)
        self.assertEqual(scaffold.guard_summary, "blocked_live_calls_not_allowed")
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)
        self.assertEqual(
            scaffold.normalized_result,
            {
                "provider": "corelogic",
                "mode": "live",
                "executionState": "live_blocked",
                "resultType": "blocked",
                "artifactType": None,
                "artifactId": None,
                "traceKey": None,
                "eventType": None,
                "eventRef": None,
                "quoteReference": None,
                "snapshotVersion": None,
                "warnings": [],
                "warningCodes": [],
                "warningSeverities": [],
                "warningFamilies": [],
                "payload": None,
            },
        )

    def test_corelogic_scaffold_live_mode_with_allow_live_calls_false_remains_blocked(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "live"
        os.environ["PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS"] = "false"

        scaffold = resolve_corelogic_integration_scaffold({})

        self.assertEqual(scaffold.state, "live_blocked")
        self.assertEqual(
            scaffold.reason_codes,
            ["live_calls_not_allowed", "live_mode_enabled"],
        )
        self.assertFalse(scaffold.live_ready)
        self.assertEqual(scaffold.guard_summary, "blocked_live_calls_not_allowed")
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)
        self.assertEqual(scaffold.normalized_result["executionState"], "live_blocked")
        self.assertEqual(scaffold.normalized_result["resultType"], "blocked")
        self.assertIsNone(scaffold.normalized_result["payload"])

    def test_corelogic_scaffold_live_mode_with_missing_credentials_remains_blocked(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "live"
        os.environ["PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS"] = "true"
        os.environ.pop("PRICE_ENGINE_CORELOGIC_API_KEY", None)
        os.environ.pop("PRICE_ENGINE_CORELOGIC_CLIENT_ID", None)

        scaffold = resolve_corelogic_integration_scaffold({})

        self.assertEqual(scaffold.state, "live_blocked")
        self.assertEqual(
            scaffold.reason_codes,
            ["live_credentials_missing", "live_mode_enabled"],
        )
        self.assertFalse(scaffold.live_ready)
        self.assertEqual(scaffold.credential_state, "missing")
        self.assertEqual(scaffold.credential_state_label, "Credentials Missing")
        self.assertEqual(scaffold.guard_summary, "blocked_missing_credentials")
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)
        self.assertEqual(scaffold.normalized_result["executionState"], "live_blocked")
        self.assertEqual(scaffold.normalized_result["resultType"], "blocked")
        self.assertIsNone(scaffold.normalized_result["payload"])

    def test_provenance_populates_mock_integration_enrichment_only_in_mock_mode(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)

        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="stub",
                status="stub",
                quote_reference=None,
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={},
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(provenance["titleQuote"]["integrationMode"], "mock")
        self.assertEqual(provenance["titleQuote"]["integrationState"], "mock_ready")
        self.assertFalse(provenance["titleQuote"]["integrationLiveReady"])
        self.assertEqual(provenance["titleQuote"]["integrationLiveReadyLabel"], "Live Integration Not Ready")
        self.assertEqual(provenance["titleQuote"]["integrationCredentialState"], "missing")
        self.assertEqual(provenance["titleQuote"]["integrationCredentialStateLabel"], "Credentials Missing")
        self.assertEqual(provenance["titleQuote"]["integrationGuardSummary"], "mock")
        self.assertEqual(provenance["titleQuote"]["integrationArtifactType"], "corelogic_mock_payload")
        self.assertEqual(provenance["titleQuote"]["integrationArtifactId"], "corelogic-mock-title-quote-v1")
        self.assertEqual(provenance["titleQuote"]["integrationTraceKey"], "corelogic:mock:corelogic-mock-title-quote-v1")
        self.assertEqual(provenance["titleQuote"]["integrationEventType"], "corelogic_mock_title_quote")
        self.assertEqual(
            provenance["titleQuote"]["integrationEventRef"],
            "integration-event:corelogic:mock:corelogic-mock-title-quote-v1",
        )
        self.assertEqual(provenance["titleQuote"]["integrationMockProfile"], "title_quote_baseline")
        self.assertEqual(provenance["titleQuote"]["integrationMockProfileLabel"], "Title Quote Baseline Mock")
        self.assertEqual(provenance["titleQuote"]["integrationResultType"], "mock_title_quote")
        self.assertEqual(provenance["titleQuote"]["integrationExecutionState"], "mock_executed")
        self.assertEqual(provenance["titleQuote"]["integrationQuoteReference"], "CORELOGIC-MOCK-QUOTE-001")
        self.assertEqual(provenance["titleQuote"]["integrationSnapshotVersion"], "mock-v1")
        self.assertEqual(provenance["titleQuote"]["integrationPayloadProfile"], "title_quote_baseline")
        self.assertEqual(provenance["titleQuote"]["integrationEstimatedTotalTitleCost"], 3700.0)
        self.assertEqual(provenance["titleQuote"]["integrationCurrency"], "USD")
        self.assertEqual(provenance["titleQuote"]["integrationEstimatedTitleFee"], 1850.0)
        self.assertEqual(provenance["titleQuote"]["integrationEstimatedSettlementFee"], 950.0)
        self.assertEqual(provenance["titleQuote"]["integrationEstimatedRecordingFee"], 150.0)
        self.assertEqual(provenance["titleQuote"]["integrationEstimatedSearchFee"], 450.0)
        self.assertEqual(provenance["titleQuote"]["integrationEstimatedMiscFee"], 300.0)
        self.assertEqual(provenance["titleQuote"]["integrationFeeLineSum"], 3700.0)
        self.assertEqual(provenance["titleQuote"]["integrationFeeDelta"], 0.0)
        self.assertEqual(provenance["titleQuote"]["integrationFeeReconciliationStatus"], "matched")
        self.assertEqual(provenance["titleQuote"]["integrationFeeReconciliationLabel"], "Fee Reconciliation Matched")
        self.assertTrue(provenance["titleQuote"]["integrationFeeReconciliationMatch"])
        self.assertEqual(provenance["titleQuote"]["integrationBundleStatus"], "complete")
        self.assertEqual(provenance["titleQuote"]["integrationBundleStatusLabel"], "Integration Bundle Complete")
        self.assertTrue(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertTrue(provenance["titleQuote"]["integrationHasTrace"])
        self.assertTrue(provenance["titleQuote"]["integrationHasEvent"])
        self.assertTrue(provenance["titleQuote"]["integrationIsExportReady"])
        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "ready")
        self.assertEqual(provenance["titleQuote"]["integrationExportReadinessLabel"], "Integration Export Ready")
        self.assertEqual(provenance["titleQuote"]["integrationExportReasonCodes"], [])
        self.assertEqual(provenance["titleQuote"]["integrationAuditCompleteness"], "complete")
        self.assertEqual(provenance["titleQuote"]["integrationAuditCompletenessLabel"], "Integration Audit Complete")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryStatus"], "ready")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryStatusLabel"], "Integration Summary Ready")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryPriority"], "mock_ready")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryPriorityLabel"], "Mock Ready")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryReasonCodes"], ["summary_mock_ready"])
        self.assertEqual(provenance["titleQuote"]["integrationDisplayBadge"], "mock_ready")
        self.assertEqual(provenance["titleQuote"]["integrationDisplayBadgeLabel"], "Integration Mock Ready")
        self.assertEqual(provenance["titleQuote"]["integrationDisplaySeverity"], "info")
        self.assertEqual(provenance["titleQuote"]["integrationDisplayOrder"], 5)
        self.assertEqual(provenance["titleQuote"]["integrationDisplayReason"], "mock_ready")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorAction"], "monitor_mock_state")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionLabel"], "Monitor Mock State")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionPriority"], 5)
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionReasonCodes"], ["operator_mock_monitor"])
        self.assertFalse(provenance["titleQuote"]["integrationOperatorActionBlocking"])
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotStatus"], "monitor")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotLabel"], "Operator Snapshot Monitor")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotSeverity"], "info")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotOrder"], 4)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorSnapshotReasonCodes"],
            ["snapshot_monitor_only"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardStatus"], "monitor")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardLabel"], "Operator Card Monitor")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardSeverity"], "info")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardOrder"], 4)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorCardReasonCodes"],
            ["card_monitor_only"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketStatus"], "ready")
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketLabel"],
            "Integration Export Packet Ready",
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketCompleteness"], "complete")
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketMissing"], [])
        self.assertTrue(provenance["titleQuote"]["integrationExportPacketReady"])
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketSummaryStatus"], "ready")
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketSummaryLabel"],
            "Export Packet Summary Ready",
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketSummaryPriority"], 3)
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketSummaryReasonCodes"],
            ["packet_summary_ready"],
        )
        self.assertFalse(provenance["titleQuote"]["integrationExportPacketSummaryBlocking"])

    def test_corelogic_scaffold_live_mode_with_partial_credentials_reports_partial_state(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "live"
        os.environ["PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS"] = "true"
        os.environ["CORELOGIC_API_BASE_URL"] = "https://example.test"
        os.environ["CORELOGIC_CLIENT_ID"] = "client-id"
        os.environ["CORELOGIC_CLIENT_SECRET"] = "   "

        scaffold = resolve_corelogic_integration_scaffold({})

        self.assertEqual(scaffold.credential_state, "partial")
        self.assertEqual(scaffold.credential_state_label, "Credentials Partial")
        self.assertFalse(scaffold.live_ready)
        self.assertEqual(scaffold.guard_summary, "blocked_missing_credentials")
        self.assertEqual(scaffold.normalized_result["executionState"], "live_blocked")
        self.assertEqual(scaffold.normalized_result["resultType"], "blocked")

        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="stub",
                status="stub",
                quote_reference=None,
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={},
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )
        self.assertIsNone(provenance["titleQuote"]["integrationResultType"])
        self.assertIsNone(provenance["titleQuote"]["integrationExecutionState"])
        self.assertIsNone(provenance["titleQuote"]["integrationQuoteReference"])
        self.assertIsNone(provenance["titleQuote"]["integrationSnapshotVersion"])
        self.assertIsNone(provenance["titleQuote"]["integrationPayloadProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedTotalTitleCost"])
        self.assertIsNone(provenance["titleQuote"]["integrationCurrency"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedTitleFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedSettlementFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedRecordingFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedSearchFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedMiscFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeLineSum"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeDelta"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationMatch"])
        self.assertIsNone(provenance["titleQuote"]["integrationBundleStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationBundleStatusLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasTrace"])
        self.assertIsNone(provenance["titleQuote"]["integrationHasEvent"])
        self.assertIsNone(provenance["titleQuote"]["integrationIsExportReady"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReadiness"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReadinessLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationAuditCompleteness"])
        self.assertIsNone(provenance["titleQuote"]["integrationAuditCompletenessLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryStatusLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryPriorityLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationSummaryReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayBadge"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayBadgeLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplaySeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationDisplayReason"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorAction"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorActionBlocking"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotSeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorSnapshotReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardSeverity"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardOrder"])
        self.assertIsNone(provenance["titleQuote"]["integrationOperatorCardReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketCompleteness"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketMissing"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketReady"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryPriority"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryReasonCodes"])
        self.assertIsNone(provenance["titleQuote"]["integrationExportPacketSummaryBlocking"])

    def test_corelogic_scaffold_live_mode_with_all_credentials_present_reports_ready_state(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "live"
        os.environ["PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS"] = "true"
        os.environ["CORELOGIC_API_BASE_URL"] = "https://example.test"
        os.environ["CORELOGIC_CLIENT_ID"] = "client-id"
        os.environ["CORELOGIC_CLIENT_SECRET"] = "client-secret"

        probe = {"called": 0}

        def _live_executor() -> None:
            probe["called"] += 1

        scaffold = resolve_corelogic_integration_scaffold({}, live_executor=_live_executor)

        self.assertEqual(scaffold.credential_state, "present")
        self.assertEqual(scaffold.credential_state_label, "Credentials Present")
        self.assertTrue(scaffold.live_ready)
        self.assertEqual(scaffold.live_ready_label, "Live Integration Ready")
        self.assertEqual(scaffold.guard_summary, "ready_for_live")
        self.assertEqual(scaffold.normalized_result["executionState"], "not_executed")
        self.assertEqual(scaffold.normalized_result["resultType"], "none")
        self.assertIsNone(scaffold.normalized_result["payload"])
        self.assertEqual(probe["called"], 0)

    def test_provenance_bridge_fields_match_normalized_envelope_values_exactly(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)

        scaffold = resolve_corelogic_integration_scaffold({})
        provenance = build_price_engine_provenance(
            title_quote_context=PriceEngineTitleQuoteContext(
                fee_inputs={},
                provider_key="stub",
                status="stub",
                quote_reference=None,
                expires_at=None,
                warnings=[],
                assumptions=[],
                provider_context={},
            ),
            scenario_profile="flip",
            applied_preset_fields=[],
            validation_warnings=[],
        )

        self.assertEqual(
            provenance["titleQuote"]["integrationResultType"],
            scaffold.normalized_result["resultType"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationExecutionState"],
            scaffold.normalized_result["executionState"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationQuoteReference"],
            scaffold.normalized_result["quoteReference"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationSnapshotVersion"],
            scaffold.normalized_result["snapshotVersion"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationPayloadProfile"],
            scaffold.normalized_result["payload"]["profile"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationEstimatedTotalTitleCost"],
            scaffold.normalized_result["payload"]["estimatedTotalTitleCost"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationCurrency"],
            scaffold.normalized_result["payload"]["currency"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationEstimatedTitleFee"],
            scaffold.normalized_result["payload"]["estimatedTitleFee"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationEstimatedSettlementFee"],
            scaffold.normalized_result["payload"]["estimatedSettlementFee"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationEstimatedRecordingFee"],
            scaffold.normalized_result["payload"]["estimatedRecordingFee"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationEstimatedSearchFee"],
            scaffold.normalized_result["payload"]["estimatedSearchFee"],
        )
        self.assertEqual(
            provenance["titleQuote"]["integrationEstimatedMiscFee"],
            scaffold.normalized_result["payload"]["estimatedMiscFee"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationFeeLineSum"], 3700.0)
        self.assertEqual(provenance["titleQuote"]["integrationFeeDelta"], 0.0)
        self.assertEqual(provenance["titleQuote"]["integrationFeeReconciliationStatus"], "matched")
        self.assertEqual(provenance["titleQuote"]["integrationBundleStatus"], "complete")
        self.assertTrue(provenance["titleQuote"]["integrationIsExportReady"])
        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "ready")
        self.assertEqual(provenance["titleQuote"]["integrationAuditCompleteness"], "complete")

    def test_reconciliation_fields_return_null_when_one_required_fee_line_is_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"
        os.environ.pop("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS", None)

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_payload = dict(scaffold.normalized_result["payload"])
        incomplete_payload.pop("estimatedMiscFee", None)
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["payload"] = incomplete_payload
        incomplete_scaffold = replace(scaffold, normalized_result=incomplete_envelope)

        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=incomplete_scaffold,
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertIsNone(provenance["titleQuote"]["integrationEstimatedMiscFee"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeLineSum"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeDelta"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationStatus"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationLabel"])
        self.assertIsNone(provenance["titleQuote"]["integrationFeeReconciliationMatch"])

    def test_integration_export_readiness_degrades_when_artifact_is_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, artifact_type=None),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "blocked")
        self.assertIn("missing_integration_artifact", provenance["titleQuote"]["integrationExportReasonCodes"])

    def test_integration_export_readiness_degrades_when_trace_is_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, trace_key=None),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "blocked")
        self.assertIn("missing_integration_trace", provenance["titleQuote"]["integrationExportReasonCodes"])

    def test_integration_export_readiness_degrades_when_event_is_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, event_type=None),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "blocked")
        self.assertIn("missing_integration_event", provenance["titleQuote"]["integrationExportReasonCodes"])

    def test_integration_export_readiness_degrades_to_conditional_when_payload_profile_is_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_payload = dict(scaffold.normalized_result["payload"])
        incomplete_payload["profile"] = None
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["payload"] = incomplete_payload
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, normalized_result=incomplete_envelope),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "conditional")
        self.assertIn("missing_integration_payload_profile", provenance["titleQuote"]["integrationExportReasonCodes"])

    def test_integration_export_readiness_degrades_to_conditional_when_reconciliation_mismatches(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_payload = dict(scaffold.normalized_result["payload"])
        incomplete_payload["estimatedMiscFee"] = 200.0
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["payload"] = incomplete_payload
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, normalized_result=incomplete_envelope),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "conditional")
        self.assertIn("fee_reconciliation_mismatch", provenance["titleQuote"]["integrationExportReasonCodes"])

    def test_integration_audit_completeness_degrades_to_partial_when_one_required_field_is_removed(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["quoteReference"] = None
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, normalized_result=incomplete_envelope),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationAuditCompleteness"], "partial")

    def test_integration_audit_completeness_is_minimal_when_no_execution_envelope_backed_fields_exist(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        empty_envelope = dict(scaffold.normalized_result)
        empty_envelope["executionState"] = "mock_executed"
        empty_envelope["resultType"] = "mock_title_quote"
        empty_envelope["quoteReference"] = None
        empty_envelope["snapshotVersion"] = None
        empty_envelope["artifactType"] = None
        empty_envelope["artifactId"] = None
        empty_envelope["traceKey"] = None
        empty_envelope["eventType"] = None
        empty_envelope["eventRef"] = None
        empty_envelope["payload"] = {}
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(
                scaffold,
                artifact_type=None,
                artifact_id=None,
                trace_key=None,
                event_type=None,
                event_ref=None,
                normalized_result=empty_envelope,
            ),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationExportReadiness"], "blocked")
        self.assertEqual(provenance["titleQuote"]["integrationAuditCompleteness"], "minimal")

    def test_integration_summary_degrades_to_blocked_when_export_is_blocked(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, artifact_type=None),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationSummaryStatus"], "blocked")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryPriority"], "export_blocked")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryReasonCodes"], ["summary_export_blocked"])
        self.assertEqual(provenance["titleQuote"]["integrationDisplayBadge"], "blocked")
        self.assertEqual(provenance["titleQuote"]["integrationDisplayBadgeLabel"], "Integration Blocked")
        self.assertEqual(provenance["titleQuote"]["integrationDisplaySeverity"], "critical")
        self.assertEqual(provenance["titleQuote"]["integrationDisplayOrder"], 1)
        self.assertEqual(provenance["titleQuote"]["integrationDisplayReason"], "export_blocked")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorAction"], "resolve_export_blockers")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionLabel"], "Resolve Export Blockers")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionPriority"], 1)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorActionReasonCodes"],
            ["operator_export_blocked"],
        )
        self.assertTrue(provenance["titleQuote"]["integrationOperatorActionBlocking"])
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotStatus"], "blocked")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotLabel"], "Operator Snapshot Blocked")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotSeverity"], "critical")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotOrder"], 1)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorSnapshotReasonCodes"],
            ["snapshot_export_blocked"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardStatus"], "blocked")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardLabel"], "Operator Card Blocked")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardSeverity"], "critical")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardOrder"], 1)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorCardReasonCodes"],
            ["card_export_blocked"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketStatus"], "blocked")
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketLabel"],
            "Integration Export Packet Blocked",
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketSummaryStatus"], "blocked")
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketSummaryPriority"], 1)
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketSummaryReasonCodes"],
            ["packet_summary_blocked"],
        )
        self.assertTrue(provenance["titleQuote"]["integrationExportPacketSummaryBlocking"])

    def test_integration_summary_degrades_to_conditional_when_export_is_conditional(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_payload = dict(scaffold.normalized_result["payload"])
        incomplete_payload["profile"] = None
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["payload"] = incomplete_payload
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(scaffold, normalized_result=incomplete_envelope),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationSummaryStatus"], "conditional")
        self.assertEqual(provenance["titleQuote"]["integrationSummaryPriority"], "export_conditional")
        self.assertEqual(
            provenance["titleQuote"]["integrationSummaryReasonCodes"],
            ["summary_export_conditional"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationDisplayBadge"], "conditional")
        self.assertEqual(provenance["titleQuote"]["integrationDisplayBadgeLabel"], "Integration Conditional")
        self.assertEqual(provenance["titleQuote"]["integrationDisplaySeverity"], "warning")
        self.assertEqual(provenance["titleQuote"]["integrationDisplayOrder"], 2)
        self.assertEqual(provenance["titleQuote"]["integrationDisplayReason"], "export_conditional")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorAction"], "resolve_export_warnings")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionLabel"], "Resolve Export Warnings")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorActionPriority"], 3)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorActionReasonCodes"],
            ["operator_export_conditional"],
        )
        self.assertFalse(provenance["titleQuote"]["integrationOperatorActionBlocking"])
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotStatus"], "conditional")
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorSnapshotLabel"],
            "Operator Snapshot Conditional",
        )
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotSeverity"], "warning")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorSnapshotOrder"], 2)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorSnapshotReasonCodes"],
            ["snapshot_export_conditional"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardStatus"], "conditional")
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorCardLabel"],
            "Operator Card Conditional",
        )
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardSeverity"], "warning")
        self.assertEqual(provenance["titleQuote"]["integrationOperatorCardOrder"], 2)
        self.assertEqual(
            provenance["titleQuote"]["integrationOperatorCardReasonCodes"],
            ["card_export_conditional"],
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketStatus"], "conditional")
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketLabel"],
            "Integration Export Packet Conditional",
        )
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketSummaryStatus"], "conditional")
        self.assertEqual(provenance["titleQuote"]["integrationExportPacketSummaryPriority"], 2)
        self.assertEqual(
            provenance["titleQuote"]["integrationExportPacketSummaryReasonCodes"],
            ["packet_summary_conditional"],
        )
        self.assertFalse(provenance["titleQuote"]["integrationExportPacketSummaryBlocking"])

    def test_integration_summary_priority_can_classify_audit_partial(self) -> None:
        self.assertEqual(
            _build_integration_summary_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_guard_summary="mock",
                integration_audit_completeness="partial",
            ),
            "conditional",
        )
        self.assertEqual(
            _build_integration_summary_priority(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_live_ready=False,
                integration_guard_summary="mock",
                integration_export_readiness="ready",
                integration_audit_completeness="partial",
            ),
            "audit_partial",
        )
        self.assertEqual(
            _build_integration_summary_reason_codes(
                integration_summary_priority="audit_partial",
            ),
            ["summary_audit_partial"],
        )
        self.assertEqual(
            _build_integration_display_badge(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_summary_priority="audit_partial",
                integration_fee_reconciliation_status="matched",
            ),
            "audit_partial",
        )
        self.assertEqual(_build_integration_display_severity("audit_partial"), "warning")
        self.assertEqual(_build_integration_display_order("audit_partial"), 3)
        self.assertEqual(_build_integration_display_reason("audit_partial"), "audit_partial")
        self.assertEqual(
            _build_integration_operator_action(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_live_ready=False,
                integration_export_readiness="ready",
                integration_audit_completeness="partial",
                integration_fee_reconciliation_status="matched",
                integration_fee_reconciliation_match=True,
            ),
            "complete_audit_data",
        )
        self.assertEqual(_build_integration_operator_action_priority("complete_audit_data"), 4)
        self.assertEqual(
            _build_integration_operator_action_reason_codes("complete_audit_data"),
            ["operator_audit_incomplete"],
        )
        self.assertFalse(_build_integration_operator_action_blocking("complete_audit_data"))
        self.assertEqual(
            _build_integration_operator_snapshot_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_operator_action="complete_audit_data",
                integration_operator_action_blocking=False,
                integration_export_readiness="ready",
                integration_audit_completeness="partial",
                integration_fee_reconciliation_status="matched",
            ),
            "review",
        )
        self.assertEqual(_build_integration_operator_snapshot_severity("review"), "warning")
        self.assertEqual(_build_integration_operator_snapshot_order("review"), 3)
        self.assertEqual(
            _build_integration_operator_snapshot_reason_codes("review"),
            ["snapshot_review_required"],
        )
        self.assertEqual(
            _build_integration_operator_card_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_audit_completeness="partial",
                integration_operator_action="complete_audit_data",
                integration_operator_action_blocking=False,
                integration_operator_snapshot_status="review",
                integration_fee_reconciliation_status="matched",
            ),
            "review",
        )
        self.assertEqual(_build_integration_operator_card_severity("review"), "warning")
        self.assertEqual(_build_integration_operator_card_order("review"), 3)
        self.assertEqual(
            _build_integration_operator_card_reason_codes("review"),
            ["card_review_required"],
        )
        self.assertEqual(
            _build_integration_export_packet_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_operator_card_status="review",
                integration_export_packet_missing=["fee_reconciliation"],
            ),
            "conditional",
        )
        self.assertEqual(
            _build_integration_export_packet_missing(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_quote_reference="CORELOGIC-MOCK-QUOTE-001",
                integration_snapshot_version="mock-v1",
                integration_currency="USD",
                integration_estimated_total_title_cost=3700.0,
                integration_fee_reconciliation_status="mismatched",
                integration_fee_reconciliation_match=False,
            ),
            ["fee_reconciliation"],
        )
        self.assertEqual(
            _build_integration_export_packet_summary_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_packet_status="conditional",
                integration_export_packet_completeness="partial",
                integration_export_packet_missing=["fee_reconciliation"],
                integration_export_packet_ready=False,
                integration_operator_card_status="review",
            ),
            "conditional",
        )
        self.assertEqual(_build_integration_export_packet_summary_priority("conditional"), 2)
        self.assertEqual(
            _build_integration_export_packet_summary_reason_codes("conditional"),
            ["packet_summary_conditional"],
        )

    def test_integration_summary_priority_can_classify_audit_minimal(self) -> None:
        self.assertEqual(
            _build_integration_summary_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_guard_summary="mock",
                integration_audit_completeness="minimal",
            ),
            "conditional",
        )
        self.assertEqual(
            _build_integration_summary_priority(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_live_ready=False,
                integration_guard_summary="mock",
                integration_export_readiness="ready",
                integration_audit_completeness="minimal",
            ),
            "audit_minimal",
        )
        self.assertEqual(
            _build_integration_summary_reason_codes(
                integration_summary_priority="audit_minimal",
            ),
            ["summary_audit_minimal"],
        )
        self.assertEqual(
            _build_integration_display_badge(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_summary_priority="audit_minimal",
                integration_fee_reconciliation_status="matched",
            ),
            "audit_minimal",
        )
        self.assertEqual(_build_integration_display_severity("audit_minimal"), "warning")
        self.assertEqual(_build_integration_display_order("audit_minimal"), 4)
        self.assertEqual(_build_integration_display_reason("audit_minimal"), "audit_minimal")

    def test_integration_display_badge_can_classify_ready_state(self) -> None:
        self.assertEqual(
            _build_integration_display_badge(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_summary_priority="ready",
                integration_fee_reconciliation_status="matched",
            ),
            "ready",
        )
        self.assertEqual(_build_integration_display_severity("ready"), "info")
        self.assertEqual(_build_integration_display_order("ready"), 6)
        self.assertEqual(_build_integration_display_reason("ready"), "live_ready")
        self.assertEqual(
            _build_integration_operator_action(
                integration_mode="live",
                integration_execution_state="mock_executed",
                integration_live_ready=True,
                integration_export_readiness="ready",
                integration_audit_completeness="complete",
                integration_fee_reconciliation_status="matched",
                integration_fee_reconciliation_match=True,
            ),
            "ready_no_action",
        )
        self.assertEqual(_build_integration_operator_action_priority("ready_no_action"), 6)
        self.assertEqual(
            _build_integration_operator_action_reason_codes("ready_no_action"),
            ["operator_ready"],
        )
        self.assertFalse(_build_integration_operator_action_blocking("ready_no_action"))
        self.assertEqual(
            _build_integration_operator_snapshot_status(
                integration_mode="live",
                integration_execution_state="mock_executed",
                integration_operator_action="ready_no_action",
                integration_operator_action_blocking=False,
                integration_export_readiness="ready",
                integration_audit_completeness="complete",
                integration_fee_reconciliation_status="matched",
            ),
            "ready",
        )
        self.assertEqual(_build_integration_operator_snapshot_severity("ready"), "info")
        self.assertEqual(_build_integration_operator_snapshot_order("ready"), 5)
        self.assertEqual(
            _build_integration_operator_snapshot_reason_codes("ready"),
            ["snapshot_ready"],
        )
        self.assertEqual(
            _build_integration_operator_card_status(
                integration_mode="live",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_audit_completeness="complete",
                integration_operator_action="ready_no_action",
                integration_operator_action_blocking=False,
                integration_operator_snapshot_status="ready",
                integration_fee_reconciliation_status="matched",
            ),
            "ready",
        )
        self.assertEqual(_build_integration_operator_card_severity("ready"), "info")
        self.assertEqual(_build_integration_operator_card_order("ready"), 5)
        self.assertEqual(
            _build_integration_operator_card_reason_codes("ready"),
            ["card_ready"],
        )
        self.assertEqual(
            _build_integration_export_packet_status(
                integration_mode="live",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_operator_card_status="ready",
                integration_export_packet_missing=[],
            ),
            "ready",
        )
        self.assertEqual(
            _build_integration_export_packet_completeness(
                integration_mode="live",
                integration_execution_state="mock_executed",
                integration_bundle_status="complete",
                integration_quote_reference="CORELOGIC-MOCK-QUOTE-001",
                integration_snapshot_version="mock-v1",
                integration_currency="USD",
                integration_estimated_total_title_cost=3700.0,
                integration_fee_reconciliation_status="matched",
                integration_fee_reconciliation_match=True,
            ),
            "complete",
        )
        self.assertTrue(
            _build_integration_export_packet_ready(
                integration_export_packet_status="ready",
                integration_export_packet_completeness="complete",
                integration_export_packet_missing=[],
            )
        )
        self.assertEqual(
            _build_integration_export_packet_summary_status(
                integration_mode="live",
                integration_execution_state="mock_executed",
                integration_export_packet_status="ready",
                integration_export_packet_completeness="complete",
                integration_export_packet_missing=[],
                integration_export_packet_ready=True,
                integration_operator_card_status="ready",
            ),
            "ready",
        )
        self.assertEqual(_build_integration_export_packet_summary_priority("ready"), 3)
        self.assertEqual(
            _build_integration_export_packet_summary_reason_codes("ready"),
            ["packet_summary_ready"],
        )
        self.assertFalse(_build_integration_export_packet_summary_blocking("ready"))

    def test_integration_operator_action_prioritizes_fee_mismatch(self) -> None:
        self.assertEqual(
            _build_integration_operator_action(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_live_ready=False,
                integration_export_readiness="ready",
                integration_audit_completeness="complete",
                integration_fee_reconciliation_status="mismatched",
                integration_fee_reconciliation_match=False,
            ),
            "review_fee_mismatch",
        )
        self.assertEqual(_build_integration_operator_action_priority("review_fee_mismatch"), 2)
        self.assertEqual(
            _build_integration_operator_action_reason_codes("review_fee_mismatch"),
            ["operator_fee_mismatch"],
        )
        self.assertTrue(_build_integration_operator_action_blocking("review_fee_mismatch"))
        self.assertEqual(
            _build_integration_operator_snapshot_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_operator_action="review_fee_mismatch",
                integration_operator_action_blocking=True,
                integration_export_readiness="ready",
                integration_audit_completeness="complete",
                integration_fee_reconciliation_status="mismatched",
            ),
            "review",
        )
        self.assertEqual(
            _build_integration_operator_card_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_readiness="ready",
                integration_audit_completeness="complete",
                integration_operator_action="review_fee_mismatch",
                integration_operator_action_blocking=True,
                integration_operator_snapshot_status="review",
                integration_fee_reconciliation_status="mismatched",
            ),
            "review",
        )
        self.assertEqual(
            _build_integration_export_packet_completeness(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_bundle_status="complete",
                integration_quote_reference="CORELOGIC-MOCK-QUOTE-001",
                integration_snapshot_version="mock-v1",
                integration_currency="USD",
                integration_estimated_total_title_cost=3700.0,
                integration_fee_reconciliation_status="mismatched",
                integration_fee_reconciliation_match=False,
            ),
            "partial",
        )
        self.assertFalse(
            _build_integration_export_packet_ready(
                integration_export_packet_status="conditional",
                integration_export_packet_completeness="partial",
                integration_export_packet_missing=["fee_reconciliation"],
            )
        )
        self.assertEqual(
            _build_integration_export_packet_summary_status(
                integration_mode="mock",
                integration_execution_state="mock_executed",
                integration_export_packet_status="conditional",
                integration_export_packet_completeness="partial",
                integration_export_packet_missing=["fee_reconciliation"],
                integration_export_packet_ready=False,
                integration_operator_card_status="review",
            ),
            "conditional",
        )

    def test_integration_bundle_status_degrades_when_artifact_fields_are_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["artifactType"] = None
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(
                scaffold,
                artifact_type=None,
                normalized_result=incomplete_envelope,
            ),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationBundleStatus"], "partial")
        self.assertFalse(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertTrue(provenance["titleQuote"]["integrationHasTrace"])
        self.assertTrue(provenance["titleQuote"]["integrationHasEvent"])
        self.assertFalse(provenance["titleQuote"]["integrationIsExportReady"])

    def test_integration_bundle_status_degrades_when_trace_field_is_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["traceKey"] = None
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(
                scaffold,
                trace_key=None,
                normalized_result=incomplete_envelope,
            ),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationBundleStatus"], "partial")
        self.assertTrue(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertFalse(provenance["titleQuote"]["integrationHasTrace"])
        self.assertTrue(provenance["titleQuote"]["integrationHasEvent"])
        self.assertFalse(provenance["titleQuote"]["integrationIsExportReady"])

    def test_integration_bundle_status_degrades_when_event_fields_are_missing(self) -> None:
        os.environ["PRICE_ENGINE_CORELOGIC_ENABLED"] = "true"
        os.environ["PRICE_ENGINE_CORELOGIC_MODE"] = "mock"

        scaffold = resolve_corelogic_integration_scaffold({})
        incomplete_envelope = dict(scaffold.normalized_result)
        incomplete_envelope["eventType"] = None
        with patch(
            "price_engine_provenance.resolve_corelogic_integration_scaffold",
            return_value=replace(
                scaffold,
                event_type=None,
                normalized_result=incomplete_envelope,
            ),
        ):
            provenance = build_price_engine_provenance(
                title_quote_context=PriceEngineTitleQuoteContext(
                    fee_inputs={},
                    provider_key="stub",
                    status="stub",
                    quote_reference=None,
                    expires_at=None,
                    warnings=[],
                    assumptions=[],
                    provider_context={},
                ),
                scenario_profile="flip",
                applied_preset_fields=[],
                validation_warnings=[],
            )

        self.assertEqual(provenance["titleQuote"]["integrationBundleStatus"], "partial")
        self.assertTrue(provenance["titleQuote"]["integrationHasArtifact"])
        self.assertTrue(provenance["titleQuote"]["integrationHasTrace"])
        self.assertFalse(provenance["titleQuote"]["integrationHasEvent"])
        self.assertFalse(provenance["titleQuote"]["integrationIsExportReady"])


if __name__ == "__main__":
    unittest.main()
