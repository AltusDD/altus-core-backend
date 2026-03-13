# DB AUTONOMY EXECUTION MODEL V1

## Purpose

Install a Supabase-first, database-agnostic execution model for governed database work in `altus-core-backend`.

## Model

GitHub issue
-> Codex execution against repo truth
-> proof-bearing PR
-> DB proof gate
-> staging-first apply workflow
-> optional production promotion under protected environment rules

## Scope

- Supabase is the first implemented engine.
- Future engines plug into the same task classes instead of replacing the control model.
- This install is governance and execution infrastructure only.

## Entry Point

DB tasks enter through:

- `.github/ISSUE_TEMPLATE/supabase-task.yml`
- `.github/ISSUE_TEMPLATE/database-task.yml`

Each task must declare:

- target environment
- database type
- target project/ref
- affected objects
- whether migration and verification SQL are required
- rollback note
- risk class
- whether contracts or maps must be updated
- unknowns and assumptions

## Artifact Classes

Database work is separated into five artifact classes:

1. Migration generation
   - Supabase now: `supabase/migrations/*.sql`
   - Future engines: engine-specific migration directories can be added without changing the issue, PR, or proof model.
2. Verification SQL
   - Supabase now: `supabase/verification/*.sql`
   - Future engines: verification directories should follow the same post-apply contract.
3. Apply workflow
   - Supabase now: `.github/workflows/supabase_apply.yml`
   - Future engines: add engine-specific apply workflows that preserve staging-first target controls and proof emission.
4. Proof collection
   - PR proof now: `.github/workflows/db_proof_gate.yml`
   - Apply proof now: uploaded workflow artifacts from `supabase_apply.yml`
5. Rollback notes
   - Required in issue intake and PR metadata for every DB task, even when the change is additive or docs-only.

## GitHub-Native Execution

- Codex works from repo artifacts, not dashboard state.
- PRs carry machine-checkable DB metadata in `.github/pull_request_template.md`.
- Proof is attached through CI artifacts and PR checks, not manual chat relay.
- Staging is the default apply target.
- Production apply is manual and must remain protected by GitHub environment controls.

## Truth Policy

- No direct dashboard-only schema change is authoritative unless it is backfilled into repository truth.
- Migration files, verification SQL, and contract/map docs are the durable source for governed DB work.
- Unknown live state must be labeled as unknown. Do not claim certainty without repo evidence or fresh proof.

## Future Engine Extension Points

The model explicitly reserves additive engine support for:

- Postgres outside Supabase
- SQL Server
- MySQL
- warehouse and analytics stores

Future engines must reuse the same control surfaces:

- issue intake contract
- PR proof metadata contract
- staging-first or lower-risk-first apply path
- rollback note requirement
- contract/data map update rules

They may add:

- engine-specific migration directories
- engine-specific verification runners
- engine-specific apply workflows

They must not remove:

- repo truth authority
- proof-bearing PR requirement
- staging-first governance
- explicit unknowns disclosure
