from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROOF_GATE_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_proof_gate.yml"
PROOF_GATE_INTEGRITY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_proof_gate_integrity.yml"

EXPECTED_TEST_MODULES = [
    "test_price_engine_calculate_contract.py",
    "test_price_engine_contract_proof_integrity.py",
    "test_price_engine_calculations_preview_contract.py",
    "test_title_rate_quote_contract.py",
    "test_title_rate_quote_contract_proof_integrity.py",
    "test_price_engine_route_inventory_proof.py",
    "test_price_engine_contract_artifact_integrity.py",
    "test_price_engine_frontend_entrypoint_integrity.py",
    "test_price_engine_contracts_readme_integrity.py",
]

EXPECTED_WORKFLOW_DEPENDENCIES = [
    ".github/workflows/price_engine_contract_proof.yml",
    ".github/workflows/price_engine_contract_proof_integrity.yml",
    ".github/workflows/price_engine_calculations_preview_contract_proof.yml",
    ".github/workflows/title_rate_quote_contract_proof.yml",
    ".github/workflows/title_rate_quote_contract_proof_integrity.yml",
    ".github/workflows/price_engine_route_inventory_proof.yml",
    ".github/workflows/price_engine_contract_artifact_integrity.yml",
    ".github/workflows/price_engine_frontend_entrypoint_integrity.yml",
    ".github/workflows/price_engine_contracts_readme_integrity.yml",
    ".github/workflows/price_engine_proof_gate_integrity.yml",
]

EXPECTED_DOC_DEPENDENCIES = [
    "docs/contracts/README.md",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/contracts/PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md",
    "docs/architecture/ROUTE_MAP_V1.md",
]


class PriceEngineProofGateIntegrityTests(unittest.TestCase):
    def test_proof_gate_runs_full_expected_test_suite(self) -> None:
        text = PROOF_GATE_WORKFLOW.read_text(encoding="utf-8")
        for module_name in EXPECTED_TEST_MODULES:
            self.assertIn(module_name, text)

    def test_proof_gate_tracks_shared_workflow_dependencies(self) -> None:
        text = PROOF_GATE_WORKFLOW.read_text(encoding="utf-8")
        for workflow_path in EXPECTED_WORKFLOW_DEPENDENCIES:
            self.assertIn(workflow_path, text)

    def test_proof_gate_tracks_shared_governance_docs(self) -> None:
        text = PROOF_GATE_WORKFLOW.read_text(encoding="utf-8")
        for doc_path in EXPECTED_DOC_DEPENDENCIES:
            self.assertIn(doc_path, text)

    def test_dedicated_proof_gate_integrity_workflow_tracks_same_dependencies(self) -> None:
        text = PROOF_GATE_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_price_engine_proof_gate_integrity.py", text)
        self.assertIn(".github/workflows/price_engine_proof_gate.yml", text)
        for workflow_path in EXPECTED_WORKFLOW_DEPENDENCIES:
            self.assertIn(workflow_path, text)
        for doc_path in EXPECTED_DOC_DEPENDENCIES:
            self.assertIn(doc_path, text)

    def test_dedicated_proof_gate_integrity_workflow_writes_summary(self) -> None:
        text = PROOF_GATE_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRICE ENGINE PROOF GATE INTEGRITY", text)
        self.assertIn(
            "aggregate proof gate coverage for route proofs, calculate workflow integrity, title-rate workflow integrity, governance proofs, and shared dependency triggers",
            text,
        )


if __name__ == "__main__":
    unittest.main()
