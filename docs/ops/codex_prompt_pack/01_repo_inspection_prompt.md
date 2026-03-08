FROM: DION
TO: CODEX LOCAL WORKER
SUBJECT: BACKEND REPO INSPECTION — GOVERNED
OBJECTIVE: Inspect backend governance, route/data/contracts, and validation tooling without modifying files.

PROMPT:

You are Codex local execution worker only.
Do not accept milestones.
Do not redefine architecture.
Do not modify files.

Inspect and return raw evidence for:

- docs/governance/AUTONOMY_CONTROL_PLANE_V1.md
- docs/governance/AUTONOMY_DIRECT_EXECUTION_LOOP_V1.md
- docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
- docs/governance/BE_ACCEPTANCE_BUNDLE_STANDARD_V1.md
- docs/governance/BE_FINAL_RETURN_TEMPLATE_V1.md
- docs/architecture/ROUTE_MAP_V1.md
- docs/architecture/DATA_MAP_V1.md
- docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md
- tools/validate_be_acceptance_bundle.py
- tools/check_route_downgrade_guard.py

Return only:

- STATUS: COMPLETE or BLOCKED
- exact substitution map for equivalent repo paths
- deterministic command list for local validation
- no-modification confirmation
