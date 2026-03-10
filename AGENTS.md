## Purpose
`altus-core-backend` is the canonical backend contract layer for shared Altus entities and backend services. It provides the shared API and data contract surface that other Altus applications depend on.

## What Codex May Change
- Repo-local documentation, templates, and workflow metadata
- Non-destructive scaffolding that improves task intake, review, and handoff
- Low-risk developer workflow files that are manual-only and read-safe
- Product code only when a task explicitly requests backend changes

## What Codex Must Not Touch
- Deployment target retargeting, Azure configuration, or runtime ownership
- Legacy empire/ecc runtime behavior unless explicitly instructed
- Cross-repo automation or any workflow that mutates other repositories
- Push-triggered or scheduled write workflows
- Casual API response-envelope, route contract, or shared entity contract mutations
- Non-additive backend changes when an additive path is possible
- Supabase migrations, staging deploy flows, or scheduled operations unless explicitly requested
- Shared integration wiring unless explicitly requested
- Secrets, environment configuration, or repo visibility/settings unless explicitly requested

## Branch Naming
- Use `codex/*` branches for all Codex-authored changes
- Keep each branch limited to one task or one safe scaffold increment

## Validation Expectations
- Read the affected files before editing
- Prefer additive changes over rewrites
- Keep changes ASCII unless the file already requires otherwise
- Validate workflow YAML for obvious syntax mistakes
- Prefer repo-local checks relevant to the touched area and summarize what was and was not validated in the PR

## Secrets And Deploy Guardrails
- Never print, rotate, or rewrite secrets
- Never add workflows that require production credentials unless explicitly approved
- Prefer `workflow_dispatch` for new coordination workflows in this repo
- Do not add scheduled or push-triggered jobs that can change infrastructure, data, or product state
- Treat Supabase migrations, staging deploy flows, shared integrations, and scheduled backend operations as guarded surfaces

## Pull Request Expectations
- Keep PRs narrow and reversible
- Describe scope boundaries and any systems intentionally left untouched
- Call out contract, workflow, runtime, integration, or migration impact explicitly
- Include rollback notes for any scaffold or workflow change
