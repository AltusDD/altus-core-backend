from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_INTEGRITY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_contract_artifact_integrity.yml"
ARTIFACT_INTEGRITY_PROOF_WORKFLOW = (
    ROOT / ".github" / "workflows" / "price_engine_contract_artifact_integrity_proof.yml"
)
TEST_MODULE = "tests/contracts/test_price_engine_contract_artifact_integrity.py"
PROOF_TEST_MODULE = "tests/contracts/test_price_engine_contract_artifact_integrity_proof.py"

EXPECTED_DEPENDENCY_PATHS = [
    "tests/contracts/test_price_engine_contract_artifact_integrity.py",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/contracts/PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md",
    "docs/contracts/PRICE_ENGINE_CALCULATE_CONTRACT_V1.md",
    "docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md",
    "docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md",
    ".github/workflows/price_engine_proof_gate.yml",
    ".github/workflows/price_engine_contract_artifact_integrity.yml",
]


class PriceEngineContractArtifactIntegrityProofTests(unittest.TestCase):
    def test_artifact_integrity_workflow_tracks_expected_dependencies(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        for path in EXPECTED_DEPENDENCY_PATHS:
            self.assertIn(f'"{path}"', text)

    def test_artifact_integrity_workflow_runs_expected_test_module(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(TEST_MODULE, text)

    def test_artifact_integrity_workflow_writes_summary(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE CONTRACT ARTIFACT INTEGRITY", text)
        self.assertIn(
            "coverage index and frontend entrypoint references must resolve to real route proof artifacts, route workflow integrity proofs, contract-artifact workflow integrity, and the aggregate proof gate",
            text,
        )

    def test_artifact_integrity_proof_workflow_tracks_same_dependencies(self) -> None:
        text = ARTIFACT_INTEGRITY_PROOF_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(PROOF_TEST_MODULE, text)
        self.assertIn('".github/workflows/price_engine_contract_artifact_integrity.yml"', text)
        for path in EXPECTED_DEPENDENCY_PATHS[:-1]:
            self.assertIn(f'"{path}"', text)

    def test_artifact_integrity_proof_workflow_writes_summary(self) -> None:
        text = ARTIFACT_INTEGRITY_PROOF_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE CONTRACT ARTIFACT INTEGRITY PROOF", text)
        self.assertIn(
            "contract artifact integrity workflow coverage for route proof artifacts, route workflow integrity proofs, aggregate proof gate references, and shared dependency triggers",
            text,
        )


if __name__ == "__main__":
    unittest.main()
