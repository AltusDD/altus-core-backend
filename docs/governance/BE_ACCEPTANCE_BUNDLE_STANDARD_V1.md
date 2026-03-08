# BE ACCEPTANCE BUNDLE STANDARD V1

## Purpose

AUTONOMY-04 standardizes deterministic backend acceptance bundles so BE execution proof is repo-native, machine-checkable, and CD-ready without hand assembly.

## Deterministic Folder Contract

Required folder shape:

`docs/proofpacks/YYYY-MM-DD_be-core_<milestone>/`

Where `<milestone>` is an uppercase backend milestone token (example: `ASSET-CONTRACT-01R`, `AUTONOMY-04`).

## Required Files

Every backend acceptance bundle must contain:

- `README.md`
- `proof_manifest.json`
- `route_and_commit.txt`
- `git_scope.txt`
- `runtime_http_raw.txt` **or** route-specific HTTP raw files (`*_http_raw.txt`)
- `telemetry_evidence.txt`
- `validation.txt`
- `persistence_evidence.txt` (required when milestone affects persistence semantics)

## Canonical File Semantics

### `README.md`

Human-readable summary of scope, milestone, reviewed commit, live build proof status, and bundle file index.

### `proof_manifest.json`

Minimum fields:

- `milestone`
- `reviewed_commit_sha`
- `live_build_sha`
- `proof_folder`
- `routes_tested[]`
- `generated_at_utc`
- `execution_mode`

### `route_and_commit.txt`

Minimum keys:

- `milestone`
- `reviewed_commit_sha`
- `live_build_sha`
- `route_tested` (single or comma-separated)
- `proof_folder`

### `git_scope.txt`

Minimum content:

- branch
- reviewed commit
- base commit used for diff
- changed files list

### `validation.txt`

Must include raw outputs from:

- bundle completeness check
- reviewed/live SHA consistency check
- route downgrade guard check
- any runtime proof gate checks

## Self-Check Gate Requirements

Bundle is invalid if any are true:

- reviewed commit SHA != live build SHA
- accepted route downgraded to reserved / N/A / non-exposed / deprecated without explicit change control
- required proof files missing
- runtime-affecting milestone has no raw runtime route proof

## Integration Requirements

- Worker execution workflow emits bundle deterministically under required folder shape.
- Finalization references emitted bundle path.
- Proof collector uploads full deterministic folder.
- Validation scripts must be repo-native and runnable without external manual processing.

## Asset Contract Negative-Proof Addendum

For runtime-affecting asset contract milestones, include deterministic negative-proof artifacts in the same proof folder.

Required additive files for negative-proof execution:

- `negative_proof_results.json`
- `negative_<route>_<case>_http_raw.txt` artifacts (deterministic, lowercase, underscore-separated)

Required negative-proof metadata per case:

- route + method
- expected status and actual status
- JSON body-shape check result
- reviewed/live SHA continuity check (`x-altus-build-sha` must match reviewed SHA lineage)
- pass/fail result
- raw artifact filename

`validation.txt` must include raw output from the negative-proof execution script and indicate whether each case passed or failed.

This addendum is strictly additive and does not relax any required files or gates defined above.
