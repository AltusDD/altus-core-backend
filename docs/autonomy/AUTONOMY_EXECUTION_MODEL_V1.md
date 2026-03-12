# AUTONOMY_EXECUTION_MODEL_V1

## Purpose

This document defines the backend autonomy execution model for `Altus-Realty-Group/altus-core-backend`.

The operating path is:

`GitHub Issue -> task_router -> codex_worker -> branch / commit / PR -> proof_gate -> merge decision`

The goal is to let backend work execute through GitHub-native issue routing with proof-bearing pull requests, not manual prompt relays.

## Supported Routing Labels

The router dispatches work when an issue carries one of these labels:

- `backend`
- `infra`
- `docs`
- `tests`

These labels define the execution class used by the worker in this backend repo.

## Backend Execution Flow

### 1. Issue-driven task intake

An operator opens or updates a GitHub issue using the backend or infra task templates and applies one supported routing label.

The issue should capture:

- objective
- scope
- target files when known
- proof expectations
- risk notes

### 2. Router role

`.github/workflows/task_router.yml` listens for:

- `issues`
- `workflow_run` from `create-autonomy-test-issue`
- `workflow_dispatch`

The router resolves the issue number safely, loads issue context from the repository, logs the trigger source, and dispatches `.github/workflows/codex_worker.yml` only when the issue carries a supported backend repo label.

### 3. Worker role

`.github/workflows/codex_worker.yml` checks out the default branch, builds a backend-scoped task prompt from the issue context, and runs `openai/codex-action@v1` in non-interactive CI mode.

The worker is responsible for:

- translating issue context into repository-grounded backend changes
- avoiding deploy-target, runtime-secret, and production-handler changes unless explicitly requested
- writing results to a `codex/issue-<number>-<class>` branch
- opening or updating a PR
- posting a status comment back to the source issue

### 4. Proof gate role

`.github/workflows/proof_gate.yml` can run from:

- `pull_request`
- `workflow_run` from `codex_worker`
- `workflow_dispatch`

It resolves the PR context, generates proof artifacts, and uploads at minimum:

- `changed_files.txt`
- `diff_summary.txt`
- `proof_status.json`
- `proof_summary.md`

These artifacts provide the minimum merge-proof bundle for autonomous backend work.

## Secret Requirements

The worker resolves the OpenAI API key using this order:

1. `OPENAI_API_KEY`
2. `ALTUS_OPENAI_API_KEY`
3. `ORG_OPENAI_API_KEY`
4. `OPENAI_API_KEY_ALTUS`

If no supported key is available, the worker exits gracefully, records the reason in the workflow summary, and comments the final disposition on the issue.

GitHub reads repository and organization secrets when the workflow run is queued. If a key is added after queue time, rerun is required.

## How This Repo Differs From `altus-core-ops`

`altus-core-ops` is the control-plane repo. This backend repo is an execution target with real route, data, and deployment-adjacent surfaces.

That means backend autonomy must stay grounded in repository evidence:

- route changes must align with `docs/architecture/ROUTE_MAP_V1.md`
- data-source claims must align with `docs/architecture/DATA_MAP_V1.md`
- contract changes must remain proof-bearing
- workflow changes must not be used as cover for runtime or deploy changes outside issue scope

This repo intentionally does not install a frontend issue template because it is not a frontend execution target.

## Proof-Bearing Backend Rules

Backend tasks must remain proof-bearing and repo-grounded.

At minimum, proof means:

- a PR exists for the routed issue unless the worker explicitly reports a safe skip
- the proof gate resolves the PR context and runs
- proof artifacts are uploaded
- claims about routes, contracts, data sources, or deploy impact are backed by repository evidence

When backend tasks affect live route behavior, stronger proof should be attached in the PR body or follow-up review notes.

## Optional Bootstrap Workflows

This repo may also use:

- `.github/workflows/bootstrap_labels.yml` to create routing labels automatically
- `.github/workflows/create_autonomy_test_issue.yml` to generate the first backend validation issue

These workflows are supporting infrastructure only. They do not replace issue review, proof artifacts, or merge judgment.
