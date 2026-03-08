# CODEX OPERATOR SETUP GUIDE V1

## Purpose

Operator guide for Dion to run Codex locally as a governed backend execution worker under existing lane, proof, and contract controls.

## Required Local Prerequisites

- Local clone of `altus-core-backend`
- Python 3 available locally
- Local shell access with `git` and `python`
- Read/write access to repo working tree
- Network access only when runtime/telemetry checks are intentionally executed

## Folder, Worktree, and Branch Expectations

- Open folder: repository root (`altus-core-backend`)
- Run commands from repo root
- Use a non-`main` working branch for execution changes
- Keep changes scoped to requested milestone/issue only

## Proof Folder Expectations

- Milestone proof path: `docs/proofpacks/YYYY-MM-DD_be-core_<MILESTONE>/`
- Issue proof path: `docs/proofpacks/YYYY-MM-DD_be-core_issue-<issue_number>/`
- Required file semantics are governed by `docs/governance/BE_ACCEPTANCE_BUNDLE_STANDARD_V1.md`

## First-Run Tasks (Deterministic)

1. Confirm repository readability and branch context:
   - `git rev-parse --show-toplevel`
   - `git rev-parse --abbrev-ref HEAD`
2. Run local compatibility self-check:
   - `python tools/run_codex_local_compatibility_check.py`
3. Confirm route/contract authority files are present:
   - `docs/architecture/ROUTE_MAP_V1.md`
   - `docs/architecture/DATA_MAP_V1.md`
   - `docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md`

## Validation Command List

- Bundle validator:
  - `python tools/validate_be_acceptance_bundle.py --proof-dir <proof_dir> --reviewed-sha <sha> --runtime-affecting`
- Route downgrade guard:
  - `python tools/check_route_downgrade_guard.py --route-map docs/architecture/ROUTE_MAP_V1.md --base-ref origin/feature/core-asset-ingest-01`
- Combined local compatibility check:
  - `python tools/run_codex_local_compatibility_check.py --proof-dir docs/proofpacks/2026-03-08_be-core_AUTONOMY-04`

## Operator Usage Pattern for Dion

1. Select one deterministic prompt from `docs/ops/codex_prompt_pack/`.
2. Instruct Codex to follow lane and authority boundaries from `CODEX_LOCAL_EXECUTION_ROLE_V1.md`.
3. Require raw proof packs (A-E) and deterministic proof folder output.
4. Reject outputs that attempt acceptance decisions or weaken route/contract/proof gates.

## Non-Negotiable Constraints

- Codex does not accept milestones.
- Codex does not alter CD authority or BE ownership.
- Codex outputs must remain deterministic, repo-relative, and validator-runnable.
- Any runtime-affecting claim must retain reviewed/live SHA discipline.
