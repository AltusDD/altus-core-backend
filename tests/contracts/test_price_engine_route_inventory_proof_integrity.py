from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE_INVENTORY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_route_inventory_proof.yml"
ROUTE_INVENTORY_INTEGRITY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_route_inventory_proof_integrity.yml"
TEST_MODULE = "tests/contracts/test_price_engine_route_inventory_proof.py"
INTEGRITY_TEST_MODULE = "tests/contracts/test_price_engine_route_inventory_proof_integrity.py"

EXPECTED_DEPENDENCY_PATHS = [
    "tests/contracts/test_price_engine_route_inventory_proof.py",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/contracts/PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md",
    "docs/architecture/ROUTE_MAP_V1.md",
    "azure/functions/asset_ingest/function_app.py",
    ".github/workflows/price_engine_route_inventory_proof.yml",
]


class PriceEngineRouteInventoryProofIntegrityTests(unittest.TestCase):
    def test_route_inventory_workflow_tracks_expected_dependencies(self) -> None:
        text = ROUTE_INVENTORY_WORKFLOW.read_text(encoding="utf-8")
        for path in EXPECTED_DEPENDENCY_PATHS:
            self.assertIn(f'"{path}"', text)

    def test_route_inventory_workflow_runs_route_inventory_test_module(self) -> None:
        text = ROUTE_INVENTORY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(TEST_MODULE, text)

    def test_route_inventory_workflow_writes_frontend_discovery_summary(self) -> None:
        text = ROUTE_INVENTORY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE ROUTE INVENTORY PROOF", text)
        self.assertIn("live price-engine decorators, route map, coverage index, and frontend entrypoint", text)

    def test_route_inventory_integrity_workflow_tracks_same_dependencies(self) -> None:
        text = ROUTE_INVENTORY_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(INTEGRITY_TEST_MODULE, text)
        self.assertIn('".github/workflows/price_engine_route_inventory_proof.yml"', text)
        for path in EXPECTED_DEPENDENCY_PATHS[:-1]:
            self.assertIn(f'"{path}"', text)

    def test_route_inventory_integrity_workflow_writes_summary(self) -> None:
        text = ROUTE_INVENTORY_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE ROUTE INVENTORY PROOF INTEGRITY", text)
        self.assertIn(
            "route inventory workflow coverage for live decorators, route map, coverage index, frontend entrypoint, and shared dependency triggers",
            text,
        )


if __name__ == "__main__":
    unittest.main()
