# GATES V1

## Purpose

Summarize the governed gates that apply to DB-backed work in this repo.

## DB Gates

1. Issue intake gate
   - DB work enters through structured issue templates.
2. PR metadata gate
   - `.github/pull_request_template.md` carries machine-readable DB proof metadata.
3. DB proof gate
   - `.github/workflows/db_proof_gate.yml`
   - Enforced by `tools/db_proof_guard.py`
4. Staging apply gate
   - `.github/workflows/supabase_apply.yml`
   - Default target is staging.
5. Production promotion gate
   - Manual only.
   - Protected by GitHub environment rules and reviewers.

## Required Outcomes

- Repo truth remains authoritative.
- Proof accompanies the PR and apply run.
- Contract and data ownership docs stay in sync with DB changes.
- Unknowns are disclosed instead of invented away.
