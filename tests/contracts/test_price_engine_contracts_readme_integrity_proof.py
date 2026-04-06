from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README_INTEGRITY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_contracts_readme_integrity.yml"
README_INTEGRITY_PROOF_WORKFLOW = (
    ROOT / ".github" / "workflows" / "price_engine_contracts_readme_integrity_proof.yml"
)
TEST_MODULE = "tests/contracts/test_price_engine_contracts_readme_integrity.py"
PROOF_TEST_MODULE = "tests/contracts/test_price_engine_contracts_readme_integrity_proof.py"

EXPECTED_DEPENDENCY_PATHS = [
    "docs/architecture/ROUTE_MAP_V1.md",
    "docs/contracts/README.md",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/contracts/PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md",
    ".github/workflows/price_engine_proof_gate.yml",
    ".github/workflows/price_engine_contracts_readme_integrity.yml",
    "tests/contracts/test_price_engine_contracts_readme_integrity.py",
]


class PriceEngineContractsReadmeIntegrityProofTests(unittest.TestCase):
    def test_readme_integrity_workflow_tracks_expected_dependencies(self) -> None:
        text = README_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        for path in EXPECTED_DEPENDENCY_PATHS:
            self.assertIn(f'"{path}"', text)

    def test_readme_integrity_workflow_runs_expected_test_module(self) -> None:
        text = README_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(TEST_MODULE, text)

    def test_readme_integrity_workflow_writes_summary(self) -> None:
        text = README_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE CONTRACTS README INTEGRITY", text)
        self.assertIn(
            "README discovery references for frontend entrypoint, route map, coverage index, and aggregate proof gate",
            text,
        )

    def test_readme_integrity_proof_workflow_tracks_same_dependencies(self) -> None:
        text = README_INTEGRITY_PROOF_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(PROOF_TEST_MODULE, text)
        self.assertIn('".github/workflows/price_engine_contracts_readme_integrity.yml"', text)
        for path in EXPECTED_DEPENDENCY_PATHS[:-1]:
            self.assertIn(f'"{path}"', text)

    def test_readme_integrity_proof_workflow_writes_summary(self) -> None:
        text = README_INTEGRITY_PROOF_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE CONTRACTS README INTEGRITY PROOF", text)
        self.assertIn(
            "contracts README integrity workflow coverage for frontend discovery references, aggregate proof gate references, and shared dependency triggers",
            text,
        )


if __name__ == "__main__":
    unittest.main()
