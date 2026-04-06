from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT_INTEGRITY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_frontend_entrypoint_integrity.yml"
ENTRYPOINT_INTEGRITY_PROOF_WORKFLOW = (
    ROOT / ".github" / "workflows" / "price_engine_frontend_entrypoint_integrity_proof.yml"
)
TEST_MODULE = "tests/contracts/test_price_engine_frontend_entrypoint_integrity.py"
PROOF_TEST_MODULE = "tests/contracts/test_price_engine_frontend_entrypoint_integrity_proof.py"

EXPECTED_DEPENDENCY_PATHS = [
    "tests/contracts/test_price_engine_frontend_entrypoint_integrity.py",
    "docs/contracts/PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/architecture/ROUTE_MAP_V1.md",
    ".github/workflows/price_engine_proof_gate.yml",
    ".github/workflows/price_engine_frontend_entrypoint_integrity.yml",
]


class PriceEngineFrontendEntrypointIntegrityProofTests(unittest.TestCase):
    def test_entrypoint_integrity_workflow_tracks_expected_dependencies(self) -> None:
        text = ENTRYPOINT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        for path in EXPECTED_DEPENDENCY_PATHS:
            self.assertIn(f'"{path}"', text)

    def test_entrypoint_integrity_workflow_runs_expected_test_module(self) -> None:
        text = ENTRYPOINT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(TEST_MODULE, text)

    def test_entrypoint_integrity_workflow_writes_frontend_summary(self) -> None:
        text = ENTRYPOINT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE FRONTEND ENTRYPOINT INTEGRITY", text)
        self.assertIn(
            "PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md matches coverage index route artifacts, route map posture, and references the aggregate proof gate",
            text,
        )

    def test_entrypoint_integrity_proof_workflow_tracks_same_dependencies(self) -> None:
        text = ENTRYPOINT_INTEGRITY_PROOF_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(PROOF_TEST_MODULE, text)
        self.assertIn('".github/workflows/price_engine_frontend_entrypoint_integrity.yml"', text)
        for path in EXPECTED_DEPENDENCY_PATHS[:-1]:
            self.assertIn(f'"{path}"', text)

    def test_entrypoint_integrity_proof_workflow_writes_summary(self) -> None:
        text = ENTRYPOINT_INTEGRITY_PROOF_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE FRONTEND ENTRYPOINT INTEGRITY PROOF", text)
        self.assertIn(
            "frontend entrypoint integrity workflow coverage for route artifacts, route map posture, aggregate proof gate references, and shared dependency triggers",
            text,
        )


if __name__ == "__main__":
    unittest.main()
