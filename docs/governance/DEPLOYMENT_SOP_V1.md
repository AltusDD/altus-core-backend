# DEPLOYMENT_SOP_V1

Status: documentation baseline

This SOP is the minimum deployment handoff for autonomous backend work in `altus-core-backend`. It does not change deploy targets. It exists so future backend PRs leave a consistent proof trail.

## 1. Classify The Change

Before merge, classify the PR as one of:

- docs/governance only
- contract/handler change
- calculation logic change
- durable write-path change
- infrastructure/config change

This classification determines the proof expected in the PR body and review notes.

## 2. Confirm Runtime Surface

- Identify the affected route family in [ROUTE_MAP_V1.md](../architecture/ROUTE_MAP_V1.md).
- Confirm whether the change touches:
  - Azure Functions runtime code
  - Supabase schema or policy files
  - Key Vault or secret name assumptions
  - documentation only

## 3. Confirm Data And Secret Impact

Use [DATA_MAP_V1.md](../architecture/DATA_MAP_V1.md) to answer:

- Does the change alter a durable write path?
- Does the change require a new secret, secret name, or credential source?
- Does the change rely on schema that is not yet proven by migrations?

If any answer is yes, the PR must include an operator-facing deployment note before merge.

## 4. Assemble The Proof Pack

Minimum PR proof should include:

- affected routes
- affected files
- sample request/response evidence for contract changes
- deploy impact statement
- explicit unknowns

For docs-only changes, the proof pack can be limited to file diffs and map alignment.

## 5. Merge Readiness Check

Before merge, verify:

- claimed scope matches changed files
- route/data maps are current
- contract changes include proof
- deploy-impact note is present
- unknowns are labeled

## 6. Post-Merge Expectations

- If the PR is docs-only, no deployment action should be taken.
- If the PR changes runtime behavior, the operator should verify the intended environment path separately from this SOP.
- If a new external dependency is introduced later, this SOP must be updated in the same PR.

## Current Repo-Specific Notes

- The only discovered durable runtime write path on `origin/main` is `POST /api/assets/ingest`.
- That path depends on Azure Managed Identity, Azure Key Vault, and Supabase REST credentials.
- ECC and price-engine routes are executable today, but most currently rely on in-code deterministic payload generation rather than proven persistent reads.
