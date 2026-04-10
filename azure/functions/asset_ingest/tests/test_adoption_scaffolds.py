import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from adoption import (  # noqa: E402
    LocalPriceEngineGateway,
    build_governance_checks,
    build_outbox_record,
    create_outbox_message,
)
from adoption.pricing_boundary import (  # noqa: E402
    PricingRequestContext,
    PricingScenario,
    RangeKeeperGatewayDeferred,
)


class AdoptionScaffoldTests(unittest.TestCase):
    def test_local_gateway_uses_existing_price_engine_service(self) -> None:
        gateway = LocalPriceEngineGateway()
        result = gateway.calculate(
            PricingScenario(
                scenario_id="baseline",
                inputs={
                    "strategy": "flip",
                    "purchasePrice": 120000,
                    "afterRepairValue": 220000,
                    "rehabCost": 30000,
                    "holdingCosts": 8000,
                    "closingCosts": 7000,
                    "cashAvailable": 60000,
                },
            ),
            context=PricingRequestContext(correlation_id="test-correlation"),
        )

        self.assertIn("MAO", result)
        self.assertIn("CashToClose", result)
        self.assertIn("RiskScore", result)

    def test_outbox_record_exposes_replay_fields(self) -> None:
        message = create_outbox_message(
            topic="price-engine.requested",
            aggregate_type="pricing_scenario",
            aggregate_id="scenario-123",
            payload={"scenarioId": "scenario-123", "mode": "calculate"},
            dedupe_key="scenario-123:calculate",
        )

        record = build_outbox_record(message)

        self.assertEqual(record["topic"], "price-engine.requested")
        self.assertEqual(record["dedupe_key"], "scenario-123:calculate")
        self.assertEqual(record["status"], "pending")
        self.assertIn('"mode":"calculate"', record["payload_json"])

    def test_governance_checks_reference_repo_authorities(self) -> None:
        checks = build_governance_checks()

        self.assertGreaterEqual(len(checks), 5)
        self.assertTrue(any(check.path == "docs/architecture/ROUTE_MAP_V1.md" for check in checks))
        self.assertTrue(any(check.path == "docs/architecture/BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V2.md" for check in checks))
        self.assertTrue(any(check.path == "supabase/verification/README.md" for check in checks))

    def test_deferred_rangekeeper_gateway_is_non_executable(self) -> None:
        with self.assertRaises(NotImplementedError):
            RangeKeeperGatewayDeferred().calculate(
                PricingScenario(scenario_id="baseline", inputs={}),
                context=PricingRequestContext(correlation_id="test-correlation"),
            )


if __name__ == "__main__":
    unittest.main()
