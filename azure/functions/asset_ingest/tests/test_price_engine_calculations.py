import pathlib
import sys
import unittest
from decimal import Decimal
import os

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
from price_engine_provenance import build_price_engine_provenance  # noqa: E402
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
                    "integrationArtifactType": None,
                    "integrationArtifactId": None,
                    "integrationTraceKey": None,
                    "integrationEventType": None,
                    "integrationEventRef": None,
                    "integrationMockProfile": None,
                    "integrationMockProfileLabel": None,
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
                "integrationArtifactType": None,
                "integrationArtifactId": None,
                "integrationTraceKey": None,
                "integrationEventType": None,
                "integrationEventRef": None,
                "integrationMockProfile": None,
                "integrationMockProfileLabel": None,
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
                "integrationArtifactType": None,
                "integrationArtifactId": None,
                "integrationTraceKey": None,
                "integrationEventType": None,
                "integrationEventRef": None,
                "integrationMockProfile": None,
                "integrationMockProfileLabel": None,
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
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactType"])
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactId"])
        self.assertIsNone(provenance["titleQuote"]["integrationTraceKey"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventType"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventRef"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfileLabel"])

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
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactType"])
        self.assertIsNone(provenance["titleQuote"]["integrationArtifactId"])
        self.assertIsNone(provenance["titleQuote"]["integrationTraceKey"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventType"])
        self.assertIsNone(provenance["titleQuote"]["integrationEventRef"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfile"])
        self.assertIsNone(provenance["titleQuote"]["integrationMockProfileLabel"])

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
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)
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
        self.assertEqual(scaffold.artifact_type, "corelogic_mock_payload")
        self.assertEqual(scaffold.artifact_id, "corelogic-mock-title-quote-v1")
        self.assertEqual(scaffold.trace_key, "corelogic:mock:corelogic-mock-title-quote-v1")
        self.assertEqual(scaffold.event_type, "corelogic_mock_title_quote")
        self.assertEqual(scaffold.event_ref, "integration-event:corelogic:mock:corelogic-mock-title-quote-v1")
        self.assertEqual(scaffold.mock_profile, "title_quote_baseline")
        self.assertEqual(scaffold.mock_profile_label, "Title Quote Baseline Mock")
        self.assertIsNotNone(scaffold.mock_payload)
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
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)

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
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)

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
        self.assertIsNone(scaffold.artifact_type)
        self.assertIsNone(scaffold.artifact_id)
        self.assertIsNone(scaffold.trace_key)
        self.assertIsNone(scaffold.event_type)
        self.assertIsNone(scaffold.event_ref)
        self.assertIsNone(scaffold.mock_profile)
        self.assertIsNone(scaffold.mock_profile_label)

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


if __name__ == "__main__":
    unittest.main()
