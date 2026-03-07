AUTONOMY WORKER BRIDGE V1
Purpose

Autonomy Worker Bridge V1 extends the control plane from intake and routing into honest execution lifecycle management.

It supports:

task claim

task status transition

worker packet generation

worker result return

PR / commit handoff comments

dry-run mode when no live worker is attached

AUTONOMY-03 extends this with repo-native backend direct execution workflows:

`.github/workflows/worker_execute_backend.yml`

`.github/workflows/worker_finalize_backend.yml`

For `lane:be-core`, direct execution is standard. Dion relay is fallback transport only.

It does not claim full self-coding autonomy if no execution worker is actually wired.

Lifecycle

Router normalizes issue and applies:

one lane:*

one status:queued

one agent:*

Worker bridge claims a queued task.

Claim transitions:

status:queued -> status:running

Worker packet is emitted:

artifact

issue comment

Execution occurs outside or through a connected worker path.

Result packet is returned with one outcome:

success

blocked

failed

proof-ready

Result transitions:

status:running -> status:proof-ready

status:running -> status:blocked

status:running -> status:queued only by explicit retry

status:proof-ready -> status:closed

status:blocked -> status:queued by manual unblock path

Worker Packet Contract

Marker:
<!-- autonomy-worker-packet -->

Fields:

issue_number

issue_title

lane

task_type

objective

target_files

acceptance_criteria

proof_required

environment

priority

execution_agent

current_labels

requested_by

commit_branch

expected_result_mode

proofpack_expectation

repo

branch

expected_proofpack

route_tested (backend direct loop default: `/api/assets/metrics`)

execution_mode

Worker Result Contract

Marker:
<!-- autonomy-worker-result -->

Fields:

issue_number

outcome

summary

changed_files

commit_sha

pr_url

proof_artifacts

blocker_reason

next_required_action

execution_mode

PR / Commit Handoff Contract

Marker:
<!-- autonomy-pr-handoff -->

Fields:

branch

commit_sha

pr_url

changed_files

proofpack_artifacts

Supports:

commit-only mode

PR mode

Dry-Run Mode

Dry-run is mandatory for repos without a live coding worker.

Dry-run behavior:

task is claimed

status:running is applied

worker packet artifact is created

worker packet comment is created

workflow stops without pretending execution occurred

Dry-run still must emit deterministic repo-relative proof artifacts under:

`docs/proofpacks/<YYYY-MM-DD>_be-core_issue-<issue_number>`

Live Worker Mode

If a real worker is attached, result inputs can be returned through workflow_dispatch:

success

blocked

failed

proof-ready

Human / Operator Override

Operators may:

move status:blocked -> status:queued

close status:proof-ready tasks after review

use workflow_dispatch for claim or result simulation

Proof Binding

Proof artifacts bind to task lifecycle via:

worker bridge artifact uploads

proofpack collector

issue comments with markers

AUTONOMY-03 adds deterministic backend markers:

`<!-- autonomy-backend-execution-packet -->`

`<!-- autonomy-backend-result-packet -->`

`<!-- autonomy-backend-final-handoff -->`

AUTONOMY-03 also requires deterministic backend proof files:

- `proof_manifest.json`
- `route_and_commit.txt`
- `route_raw_response.txt`
- `telemetry_evidence.txt`
- `persistence_evidence.txt`

Example Lifecycle Packet Set
Example Input Issue Body
lane

be-core

task_type

infra

objective

Install worker bridge and status reconciliation.

target_files

.github/workflows/worker_bridge.yml
.github/workflows/task_status_reconcile.yml
docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md

acceptance_criteria

Queued task can be claimed.
Worker packet is emitted.
Result packet can move issue to proof-ready.

proof_required

A-E

environment

staging

priority

p1

execution_agent

vs

Expected Labels Before Execution

lane:be-core

status:queued

agent:vs

Worker Packet Comment Output
<!-- autonomy-worker-packet -->
Autonomy Worker Packet

issue_number: 123
issue_title: [AUTO] Install worker bridge
lane: be-core
task_type: infra
objective: Install worker bridge and status reconciliation.
target_files: .github/workflows/worker_bridge.yml
.github/workflows/task_status_reconcile.yml
docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
acceptance_criteria: Queued task can be claimed.
Worker packet is emitted.
Result packet can move issue to proof-ready.
proof_required: A-E
environment: staging
priority: p1
execution_agent: vs
current_labels: lane:be-core, status:running, agent:vs
requested_by: operator
commit_branch: autonomy/issue-123
expected_result_mode: success|blocked|failed|proof-ready
proofpack_expectation: docs/proofpacks/<YYYY-MM-DD>_be-core_autonomy-02
dry_run: true

Worker Result Comment Output
<!-- autonomy-worker-result -->
Autonomy Worker Result

issue_number: 123
outcome: proof-ready
summary: Worker packet generated and dry-run completed.
changed_files: .github/workflows/worker_bridge.yml, .github/workflows/task_status_reconcile.yml, docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
commit_sha: abc123def456
pr_url:
proof_artifacts: docs/proofpacks/2026-03-06_be-core_autonomy-02/AUTONOMY02A_CORRECTION_RAW.txt
blocker_reason:
next_required_action: review proof and close task

PR / Commit Handoff Comment Output
<!-- autonomy-pr-handoff -->
Autonomy PR / Commit Handoff

branch: autonomy/issue-123
commit_sha: abc123def456
pr_url:
changed_files: .github/workflows/worker_bridge.yml, .github/workflows/task_status_reconcile.yml, docs/governance/AUTONOMY_WORKER_BRIDGE_V1.md
proofpack_artifacts: docs/proofpacks/2026-03-06_be-core_autonomy-02/AUTONOMY02A_CORRECTION_RAW.txt

Final Expected Status Labels

lane:be-core

status:proof-ready

agent:vs
