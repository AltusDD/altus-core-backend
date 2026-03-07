# AUTONOMY DIRECT EXECUTION LOOP V1

## Purpose

AUTONOMY-03 installs a repo-native backend execution loop for `lane:be-core` tasks so work can be claimed, executed, proof-packed, and finalized without using Dion as the default transport.

## Standard Backend Execution Model

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

## Policy

- Backend lane prefers direct worker execution path.
- Dion is fallback transport only.
- Manual relay is not the default path.
- Proof remains mandatory.

## Workflows

- `.github/workflows/worker_execute_backend.yml`
- `.github/workflows/worker_finalize_backend.yml`
- `.github/workflows/autonomy_router.yml`
- `.github/workflows/worker_bridge.yml` (fallback bridge)
- `.github/workflows/proofpack_collect.yml`

## Task Claim Contract

A backend task is claimable when all are true:

- exactly one `lane:*` label and it is `lane:be-core`
- exactly one `agent:*` label
- current status includes `status:queued`

Claim transition:

- `status:queued` -> `status:running`

Only one `status:*` label may exist after transition.

## Backend Execution Packet Contract

Marker:

`<!-- autonomy-backend-execution-packet -->`

Fields:

- issue_number
- issue_title
- lane
- objective
- target_files
- acceptance_criteria
- proof_required
- environment
- priority
- execution_agent
- branch
- repo
- expected_proofpack
- execution_mode

Artifact names (deterministic):

- `backend_execution_packet_issue_<issue_number>.json`
- `backend_execution_packet_issue_<issue_number>.txt`
- `worker_execution_packet.json`
- `worker_execution_packet.txt`

## Direct Execution Modes

### `dry_run=true`

Simulation mode:

- claims task
- moves status to running
- emits execution packet artifact
- posts execution packet issue comment

### `dry_run=false`

Real execution mode:

- requires repository
- requires branch
- requires target_files
- requires execution objective
- requires proof requirements

## Backend Result Packet Contract

Marker:

`<!-- autonomy-backend-result-packet -->`

Fields:

- issue_number
- outcome
- summary
- changed_files
- commit_sha
- pr_url
- proof_artifacts
- blocker_reason
- next_required_action
- execution_mode

Artifact names (deterministic):

- `backend_result_packet_issue_<issue_number>.json`
- `backend_result_packet_issue_<issue_number>.txt`
- `worker_result_packet.json`
- `worker_result_packet.txt`

## Final Handoff Packet Contract

Marker:

`<!-- autonomy-backend-final-handoff -->`

Fields:

- issue_number
- final_status
- outcome
- summary
- changed_files
- commit_sha
- pr_url
- proof_artifacts
- blocker_reason
- next_required_action
- execution_mode

Artifact names (deterministic):

- `backend_final_handoff_issue_<issue_number>.json`
- `backend_final_handoff_issue_<issue_number>.txt`
- `worker_final_handoff_packet.json`
- `worker_final_handoff_packet.txt`

## Finalization Status Rules

- `status:running` -> `status:proof-ready`
- `status:running` -> `status:blocked`
- `status:proof-ready` -> `status:closed`

Finalization must preserve exactly one `status:*` label.

## Proof Collection Requirements

`proofpack_collect.yml` must include:

- worker execution packet
- worker result packet
- final handoff packet

## Deterministic Proof Folder Contract

- Repo-relative proof folder is required: `docs/proofpacks/<YYYY-MM-DD>_be-core_issue-<issue_number>`.
- `worker_execute_backend.yml` must emit, at minimum:
	- `proof_manifest.json`
	- `route_and_commit.txt`
	- `route_raw_response.txt`
	- `telemetry_evidence.txt`
	- `persistence_evidence.txt`
- Route proof target defaults to: `GET /api/assets/metrics`.

## Dry-Run Honesty Rule

- If `dry_run=true`, proof folder artifacts are still required.
- Dry-run artifacts must explicitly state that live route/persistence/telemetry collection was skipped.

## Backend Milestone Compatibility

This loop is additive infrastructure and supports backend milestones such as:

- ASSET-RESTORE-01 correction pass
- backend `function_app.py` milestone execution

## Non-Goals

- No replacement of existing deploy workflows
- No removal of AUTONOMY-01/AUTONOMY-02 paths
- No relaxation of proof requirements
