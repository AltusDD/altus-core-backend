from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_calculations_preview_contract_proof.yml"

EXPECTED_PATHS = [
    "tests/contracts/test_price_engine_calculations_preview_contract.py",
    "docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/contracts/fixtures/price_engine_calculations_preview/**",
    "docs/architecture/ROUTE_MAP_V1.md",
    "azure/functions/asset_ingest/price_engine_calculations_preview_handler.py",
    "azure/functions/asset_ingest/price_engine_calculations.py",
    ".github/workflows/price_engine_calculations_preview_contract_proof.yml",
]


class PriceEngineCalculationsPreviewContractProofIntegrityTests(unittest.TestCase):
    def test_workflow_tracks_expected_preview_dependencies(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        for path in EXPECTED_PATHS:
            self.assertIn(path, text)

    def test_workflow_runs_expected_test_module(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_price_engine_calculations_preview_contract.py", text)

    def test_workflow_writes_route_summary(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE CALCULATIONS PREVIEW CONTRACT PROOF", text)
        self.assertIn("GET /api/price-engine/calculations-preview", text)


if __name__ == "__main__":
    unittest.main()
