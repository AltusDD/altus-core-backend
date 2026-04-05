from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ENTRYPOINT = ROOT / "docs" / "contracts" / "PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md"
COVERAGE_INDEX = ROOT / "docs" / "contracts" / "PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md"
PROOF_GATE_WORKFLOW = ".github/workflows/price_engine_proof_gate.yml"

EXPECTED_ROUTE_ROWS = [
    {
        "route": "POST /api/price-engine/calculate",
        "contract": "docs/contracts/PRICE_ENGINE_CALCULATE_CONTRACT_V1.md",
        "fixtures": "docs/contracts/fixtures/price_engine_calculate/",
        "test": "tests/contracts/test_price_engine_calculate_contract.py",
        "workflow": ".github/workflows/price_engine_contract_proof.yml",
    },
    {
        "route": "GET /api/price-engine/calculations-preview",
        "contract": "docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md",
        "fixtures": "docs/contracts/fixtures/price_engine_calculations_preview/",
        "test": "tests/contracts/test_price_engine_calculations_preview_contract.py",
        "workflow": ".github/workflows/price_engine_calculations_preview_contract_proof.yml",
    },
    {
        "route": "POST /api/price-engine/title-rate-quote",
        "contract": "docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md",
        "fixtures": "docs/contracts/fixtures/title_rate_quote/",
        "test": "tests/contracts/test_title_rate_quote_contract.py",
        "workflow": ".github/workflows/title_rate_quote_contract_proof.yml",
    },
]


class PriceEngineFrontendEntrypointIntegrityTests(unittest.TestCase):
    def test_frontend_entrypoint_contains_expected_route_rows(self) -> None:
        text = FRONTEND_ENTRYPOINT.read_text(encoding="utf-8")
        lines = text.splitlines()
        for row in EXPECTED_ROUTE_ROWS:
            matching_line = next(
                (line for line in lines if f"| `{row['route']}` |" in line),
                None,
            )
            self.assertIsNotNone(matching_line, msg=f"Missing entrypoint row for {row['route']}")
            self.assertIn(f"`{row['contract']}`", matching_line)
            self.assertIn(f"`{row['fixtures']}`", matching_line)
            self.assertIn(f"`{row['test']}`", matching_line)
            self.assertIn(f"`{row['workflow']}`", matching_line)

    def test_coverage_index_contains_matching_route_artifact_rows(self) -> None:
        text = COVERAGE_INDEX.read_text(encoding="utf-8")
        for row in EXPECTED_ROUTE_ROWS:
            expected_fragment = (
                f"| `{row['route']}` |"
                f" `{row['contract']}` |"
                f" `{row['fixtures']}` |"
                f" `{row['test']}` |"
                f" `{row['workflow']}` |"
            )
            self.assertIn(expected_fragment, text)

    def test_frontend_entrypoint_references_aggregate_proof_gate(self) -> None:
        text = FRONTEND_ENTRYPOINT.read_text(encoding="utf-8")
        self.assertIn(f"`{PROOF_GATE_WORKFLOW}`", text)


if __name__ == "__main__":
    unittest.main()
