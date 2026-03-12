# GATES_V1

Status: minimum governance baseline for autonomous backend work

These gates define the minimum proof requirements for autonomous PRs in `altus-core-backend`. They are intentionally lightweight, but they must prevent undocumented route drift and false certainty about data sources.

## Gate 1: Scope Integrity

- The PR must stay within the task scope it claims.
- Documentation-only tasks must not change runtime handlers, deploy targets, secrets, or environment configuration.
- If route, contract, or data behavior changes, the PR must say so explicitly.

## Gate 2: Route Map Integrity

- Any route add/remove/rename requires an update to [ROUTE_MAP_V1.md](../architecture/ROUTE_MAP_V1.md).
- The route map must identify the runtime entrypoint and the owning handler/service path where determinable.
- Unknown ownership must be labeled as unknown, not inferred.

## Gate 3: Data Map Integrity

- Any newly discovered store, queue, cache, or credential dependency requires an update to [DATA_MAP_V1.md](../architecture/DATA_MAP_V1.md).
- Write-path changes require explicit proof of the targeted tables or systems.
- If migrations drift from runtime assumptions, the PR must call that out.

## Gate 4: Contract Proof

- Changes to request validation, response shape, status codes, or domain headers require contract proof.
- Minimum contract proof:
  - route name
  - sample input
  - sample output or error
  - note on compatibility risk
- If no automated test exists, the PR must say what manual proof was used.

## Gate 5: Deployment Safety

- Every backend PR must state whether deploy-time coordination is required.
- If runtime secrets, Key Vault names, Supabase schema, or infrastructure bindings are affected, the PR must include an operator handoff note.
- If none of those are affected, the PR should explicitly say `deploy impact: none`.

## Gate 6: Unknowns Must Stay Visible

- Unknowns, gaps, and assumptions must be listed plainly.
- Placeholder implementations may be documented as executable today, but not promoted to production truth without proof.
- Autonomous tasks should prefer "not yet proven" over speculative certainty.

## Minimum Proof Pack By Change Type

| Change Type | Minimum Proof |
|---|---|
| Docs/governance only | Diff review plus map consistency confirmation |
| Handler validation/response change | Sample request/response and affected route list |
| Calculation logic change | Representative input/output proof and compatibility note |
| Durable write-path change | Contract proof plus storage target proof and deploy impact note |
| New secret/dependency path | Data map update plus operator handoff note |
