# AUTONOMY WORKER BRIDGE V1

## Purpose

AUTONOMY-02 installs the Worker Execution Bridge V1 for structured claim and result execution handoff.

Bridge capabilities:
- claim mode packetization for an existing structured task issue
- result mode completion packetization with deterministic outcome mapping
- deterministic artifact emission
- deterministic comment markers for downstream automation

## Scope

Working routes:
- workflow-only / no API route changes

The bridge is additive and does not replace deploy workflows.

## Lifecycle

1. Router normalizes task packet and applies queued status.
2. Worker bridge runs in `claim` mode.
3. Bridge validates one `lane:*` and one `agent:*`, requires status `queued|blocked`, then sets `status:running`.
4. Bridge emits packet artifact and packet marker comment.
5. Worker executes assigned scope.
6. Worker bridge runs in `result` mode with an explicit `outcome`.
7. Bridge maps outcome to status (`success|proof-ready -> status:proof-ready`, `blocked|failed -> status:blocked`).
8. Bridge emits result/handoff artifacts and posts result + conditional handoff comments.
9. Status reconcile workflow enforces a single `status:*` label.

## Contracts

### Workflow: worker_bridge.yml

Action modes:
- `claim`
- `result`

Inputs:
- `issue_number`
- `action_mode` (`claim|result`)
- `dry_run`
- `outcome` (`success|blocked|failed|proof-ready`)
- `summary`
- `changed_files`
- `commit_sha`
- `pr_url`
- `proof_artifacts`
- `blocker_reason`
- `next_required_action`

Required markers:
- `<!-- autonomy-worker-packet -->`
- `<!-- autonomy-worker-result -->`
- `<!-- autonomy-pr-handoff -->`

Required artifacts:
- `worker_packet.json`
- `worker_packet.txt`
- `worker_result.json`
- `worker_result.txt`
- `worker_handoff.txt`

Claim packet contract fields:
- `issue_number`
- `issue_title`
- `lane`
- `task_type`
- `objective`
- `target_files`
- `acceptance_criteria`
- `proof_required`
- `environment`
- `priority`
- `execution_agent`
- `current_labels`
- `requested_by`
- `commit_branch`
- `expected_result_mode`
- `proofpack_expectation`

Result contract fields:
- `issue_number`
- `outcome`
- `summary`
- `changed_files`
- `commit_sha`
- `pr_url`
- `proof_artifacts`
- `blocker_reason`
- `next_required_action`

### Workflow: task_status_reconcile.yml

Rules:
- enforce exactly one status label
- add `status:queued` when no status label exists
- post reconcile comment marker `<!-- autonomy-status-reconcile -->`

## Dry-Run (Manual)

1. Open a structured autonomous task issue.
2. Run worker_bridge.yml with `action_mode=claim` and `dry_run=true`.
3. Confirm bridge applies `status:running` and emits `worker_packet.*` plus `<!-- autonomy-worker-packet -->`.
4. Confirm honesty statement is explicit when no live worker exists (`execution_agent=none` / `agent:none`).
5. Run worker_bridge.yml with `action_mode=result` and selected `outcome`.
6. Verify `worker_result.*`, `worker_handoff.txt`, and marker comments are emitted.
7. Run task_status_reconcile.yml for the issue.
8. Verify one and only one status label remains.

Dry-run behavior:
- claim task
- apply `status:running`
- emit packet artifact + comment
- stop honestly if no live worker exists

## Example Input Issue Body

### lane
be-core

### task_type
infra

### objective
Install worker bridge and status reconcile workflows.

### target_files
.github/workflows/worker_bridge.yml
.github/workflows/task_status_reconcile.yml
docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md

### acceptance_criteria
Bridge emits packet/result/handoff artifacts.
Reconcile enforces single status label.

### proof_required
A-E

### environment
staging

### priority
p1

### execution_agent
vs

## Expected Labels Before Execution
- lane:be-core
- status:queued
- agent:vs

## Worker Packet Comment Output

<!-- autonomy-worker-packet -->
## Worker Packet
issue_number: 123
issue_title: [AUTO] Install worker bridge and status reconcile workflows.
lane: be-core
task_type: infra
objective: Install worker bridge and status reconcile workflows.
target_files: .github/workflows/worker_bridge.yml
.github/workflows/task_status_reconcile.yml
docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
acceptance_criteria: Bridge emits packet/result/handoff artifacts.
Reconcile enforces single status label.
proof_required: A-E
environment: staging
priority: p1
execution_agent: vs
current_labels: lane:be-core, status:running, agent:vs
requested_by: be-core
commit_branch: feature/core-asset-ingest-01
expected_result_mode: result
proofpack_expectation: docs/proofpacks/<YYYY-MM-DD>_be-core_autonomy-02

## Worker Result Comment Output

<!-- autonomy-worker-result -->
## Worker Result
issue_number: 123
outcome: success
summary: AUTONOMY-02A corrected worker bridge contract drift.
changed_files: .github/workflows/worker_bridge.yml, .github/workflows/task_status_reconcile.yml, docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
commit_sha: abcdef1234567890
pr_url: https://github.com/Altus-Realty-Group/altus-core-backend/pull/456
proof_artifacts: docs/proofpacks/2026-03-06_be-core_autonomy-02/AUTONOMY02A_CORRECTION_RAW.txt
blocker_reason:
next_required_action: BE-Core review and close if accepted.

## PR / Commit Handoff Comment Output

<!-- autonomy-pr-handoff -->
## PR / Commit Handoff
issue_number: 123
outcome: success
summary: AUTONOMY-02A corrected worker bridge contract drift.
changed_files: .github/workflows/worker_bridge.yml, .github/workflows/task_status_reconcile.yml, docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
commit_sha: abcdef1234567890
pr_url: https://github.com/Altus-Realty-Group/altus-core-backend/pull/456
proof_artifacts: docs/proofpacks/2026-03-06_be-core_autonomy-02/AUTONOMY02A_CORRECTION_RAW.txt
blocker_reason:
next_required_action: BE-Core review and close if accepted.

## Final Expected Status Labels
- status:proof-ready
