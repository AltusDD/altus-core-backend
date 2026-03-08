# AUTONOMY CONTROL PLANE V1

## Purpose

Autonomy Control Plane V1 installs the first honest autonomous work layer for Altus.

What it does:

- structured task intake through GitHub issue forms
- normalized lane and agent routing labels
- workflow_dispatch manual task injection
- worker execution bridge claim/result packetization
- backend direct worker execution loop for `lane:be-core`
- status reconciliation for single status label enforcement
- proof artifact collection
- OIDC validation workflow for Azure posture

What it does **not** do yet:

- self-author code without an execution worker
- autonomously merge PRs
- autonomously deploy to production without an existing approved workflow
- replace CD governance

## Task Lifecycle

1. Task is opened through the `Autonomous Task` issue form.
2. `autonomy_router.yml` normalizes the task packet.
3. Router applies:
   - one `lane:*` label
   - one `status:*` label
   - zero or one `agent:*` label
4. Router comments back a normalized packet.
5. Execution proceeds outside the router using the assigned worker.
6. `lane:be-core` defaults to repo-native direct execution using:
   - `.github/workflows/worker_execute_backend.yml`
   - `.github/workflows/worker_finalize_backend.yml`
7. `worker_bridge.yml` remains available as relay fallback and compatibility bridge.
8. `task_status_reconcile.yml` enforces exactly one `status:*` label.
9. Proof artifacts are collected by `proofpack_collect.yml`.
10. Status progresses across `status:queued`, `status:running`, `status:blocked`, `status:proof-ready`, and `status:closed`.

## Backend Standard Execution Model

CD directive
↓
BE prepares backend execution packet
↓
repo-native worker execution loop runs
↓
proof artifacts collected
↓
BE validates result
↓
CD receives final validated result

### Backend Default Rule

- For `lane:be-core`, direct worker execution is the preferred path.
- Dion relay is fallback transport only.
- Manual relay is not the default backend path.
- Proof remains mandatory for completion.
- Direct backend proof path is deterministic and repo-relative: `docs/proofpacks/<YYYY-MM-DD>_be-core_issue-<issue_number>`
- AUTONOMY-04 milestone bundle path is deterministic and repo-relative: `docs/proofpacks/<YYYY-MM-DD>_be-core_<milestone>`
- Default route exercised for hardened backend proof emission: `GET /api/assets/metrics`
- Bundle and final return contract authorities:
   - `docs/governance/BE_ACCEPTANCE_BUNDLE_STANDARD_V1.md`
   - `docs/governance/BE_FINAL_RETURN_TEMPLATE_V1.md`
- Codex local worker role and operator setup authorities:
   - `docs/governance/CODEX_LOCAL_EXECUTION_ROLE_V1.md`
   - `docs/governance/CODEX_OPERATOR_SETUP_GUIDE_V1.md`

## Labels

### Lane Labels

- `lane:be-core`
- `lane:be-ecc`
- `lane:fe-ecc`
- `lane:fe-pe`
- `lane:fe-ih`
- `lane:cd`

### Status Labels

- `status:queued`
- `status:running`
- `status:blocked`
- `status:proof-ready`
- `status:closed`

### Agent Labels

- `agent:vs`
- `agent:supabase`
- `agent:antigravity`
- `agent:replit`
- `agent:none`

## Routing Rules

- `lane` is sourced from the issue form or workflow_dispatch input.
- `execution_agent` becomes an `agent:*` label when not `none`.
- `execution_agent: none` maps to `agent:none`.
- Router does not execute work.
- Router only normalizes labels and comments back the packet.
- Worker execution bridge performs claim/result packet comments and artifacts.
- For `lane:be-core`, router prefers direct backend execution workflow dispatch.

## Proof Pack Artifact Rules

The proof collector uploads, when present:

- `ci_proof.json`
- `ci_proof.txt`
- raw curl output
- raw SQL output
- diff scope files
- deterministic `docs/proofpacks/**` backend worker outputs

Proof collector is additive. It does not change deploy behavior.

## Human vs Agent Responsibilities

### Human

- opens structured task issues
- reviews proof
- decides whether to advance or close work

### CD / Governance

- authorizes scope
- accepts or rejects proof
- escalates blocked work

### Execution Agents

- perform the work
- return raw outputs
- do not redefine scope

## Azure Auth Posture

Preferred posture:

- GitHub Actions OIDC
- Azure federated credentials
- no long-lived publish profile when avoidable

Validation workflow:

- `.github/workflows/azure_oidc_validate.yml`

## Existing Deploy Safety

These autonomy workflows are additive only.
They must not modify or replace the current backend deploy workflows.

## Example Structured Task Issue Body

```markdown
### lane

be-core

### task_type

infra

### objective

Install autonomy router and proof collector.

### target_files

.github/workflows/autonomy_router.yml
.github/workflows/proofpack_collect.yml
docs/governance/AUTONOMY_CONTROL_PLANE_V1.md

### acceptance_criteria

Router applies normalized labels.
Proof artifact bundle uploads.

### proof_required

A-E

### environment

staging

### priority

p1

### execution_agent

vs
```

## Expected Labels

- `lane:be-core`
- `status:queued`
- `agent:vs`

## Expected Router Comment Output

<!-- autonomy-router:normalized-task -->
```markdown
## Autonomy Router Packet

lane: be-core
task_type: infra
objective: Install autonomy router and proof collector.
target_files: .github/workflows/autonomy_router.yml
.github/workflows/proofpack_collect.yml
docs/governance/AUTONOMY_CONTROL_PLANE_V1.md
acceptance_criteria: Router applies normalized labels.
Proof artifact bundle uploads.
proof_required: A-E
environment: staging
priority: p1
execution_agent: vs

## Expected Labels

- lane:be-core
- status:queued
- agent:vs
```
