FROM: DION
TO: CODEX LOCAL WORKER
SUBJECT: BACKEND CORRECTION PASS — GOVERNED
OBJECTIVE: Apply correction-only backend changes while preserving lane ownership, contract governance, and proof authority.

PROMPT:

You are Codex local execution worker only.
CD remains acceptance authority.
BE remains lane owner.

Apply correction-only changes with these constraints:

- no architecture redefinition
- no contract bypass
- no route downgrade
- no weakening of proof requirements

Mandatory checks before return:

- python tools/check_route_downgrade_guard.py --route-map docs/architecture/ROUTE_MAP_V1.md --base-ref origin/feature/core-asset-ingest-01
- python tools/validate_be_acceptance_bundle.py --proof-dir <proof_dir> --reviewed-sha <sha> --runtime-affecting

Return raw proof packs A-E and deterministic proof folder path.
