FROM: DION
TO: CODEX LOCAL WORKER
SUBJECT: ACCEPTANCE BUNDLE ASSEMBLY — DETERMINISTIC
OBJECTIVE: Assemble deterministic backend proof bundle aligned to BE bundle standard and final return template.

PROMPT:

Assemble proof only.
Do not change CD authority or BE lane ownership.

Bundle path format:

- docs/proofpacks/YYYY-MM-DD_be-core_<MILESTONE>/

Required files:

- README.md
- proof_manifest.json
- route_and_commit.txt
- git_scope.txt
- runtime_http_raw.txt or *_http_raw.txt
- telemetry_evidence.txt
- validation.txt
- persistence_evidence.txt when applicable

Validation required:

- python tools/validate_be_acceptance_bundle.py --proof-dir <proof_dir> --reviewed-sha <sha> --runtime-affecting
- python tools/check_route_downgrade_guard.py --route-map docs/architecture/ROUTE_MAP_V1.md --base-ref origin/feature/core-asset-ingest-01

Return format must follow docs/governance/BE_FINAL_RETURN_TEMPLATE_V1.md.
