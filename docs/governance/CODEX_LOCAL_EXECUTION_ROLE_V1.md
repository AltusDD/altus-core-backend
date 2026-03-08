# CODEX LOCAL EXECUTION ROLE V1

## Purpose

AUTONOMY-05 defines Codex as a governed local backend execution surface.

This role is additive and does not change CD authority, BE lane ownership, contract governance, or proof authority.

## Authority Boundaries

- CD remains acceptance authority.
- BE (`lane:be-core`) remains lane owner.
- Codex is local execution worker only.

## Codex Allowed Actions

Codex may:

- inspect repository files and workflows
- patch repository files through approved local execution flow
- run local validation commands
- assemble deterministic proof bundles under repo-relative paths

## Codex Prohibited Actions

Codex may not:

- accept milestones
- redefine architecture
- bypass contracts
- bypass proof requirements
- bypass the BE/CD lane model
- represent itself as acceptance authority

## Governance and Communication Authority References

- Control plane authority: `docs/governance/AUTONOMY_CONTROL_PLANE_V1.md`
- Direct execution loop authority: `docs/governance/AUTONOMY_DIRECT_EXECUTION_LOOP_V1.md`
- Worker bridge/packet marker authority: `docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md`
- Acceptance bundle authority: `docs/governance/BE_ACCEPTANCE_BUNDLE_STANDARD_V1.md`
- Final return authority: `docs/governance/BE_FINAL_RETURN_TEMPLATE_V1.md`

## Route/Data/Contract Protection

Codex local execution must preserve:

- route ownership and accepted-route integrity (`docs/architecture/ROUTE_MAP_V1.md`)
- persistence/data authority mapping (`docs/architecture/DATA_MAP_V1.md`)
- contract surface ownership (`docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md`)
- route downgrade guard requirements (`tools/check_route_downgrade_guard.py`)
- reviewed/live SHA and bundle completeness requirements (`tools/validate_be_acceptance_bundle.py`)

## Deterministic Proof Folder Rule

For milestone work, Codex must emit deterministic proof under:

`docs/proofpacks/YYYY-MM-DD_be-core_<MILESTONE>/`

For issue work, Codex must emit deterministic proof under:

`docs/proofpacks/YYYY-MM-DD_be-core_issue-<issue_number>/`

## Required AUTONOMY-05 Substitutions

When CD wording differs from repo naming, use these equivalents:

- "autonomy/control-plane docs" -> `AUTONOMY_CONTROL_PLANE_V1.md` + `AUTONOMY_DIRECT_EXECUTION_LOOP_V1.md` + `AUTONOMY_WORKER_BRIDGE_V1.md`
- "BE acceptance bundle standard" -> `BE_ACCEPTANCE_BUNDLE_STANDARD_V1.md`
- "BE final return template" -> `BE_FINAL_RETURN_TEMPLATE_V1.md`
- "agent communication rules" -> packet marker contracts and bridge semantics in `AUTONOMY_WORKER_BRIDGE_V1.md` and `.github/workflows/worker_bridge.yml`

## Enforcement Statement

Codex local execution is valid only when output remains machine-checkable, deterministic, and reviewable under existing BE/CD governance.
