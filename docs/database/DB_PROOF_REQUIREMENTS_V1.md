# DB PROOF REQUIREMENTS V1

## Purpose

Define the minimum proof package for governed DB work.

## PR Gate Requirements

`db_proof_gate.yml` requires:

- machine-readable DB metadata in the PR body
- migration file present when schema change is claimed
- verification SQL present when schema change is claimed
- changed objects documented
- rollback note present
- `docs/architecture/DATA_MAP_V1.md` updated when contract or data-source ownership changes
- no fake certainty language in DB governance docs

## PR Metadata Contract

PRs must include the metadata block from `.github/pull_request_template.md`:

- `schema_change_claimed`
- `verification_sql_present`
- `changed_objects`
- `rollback_note`
- `contract_or_data_map_changed`
- `unknowns`

## Apply Proof Requirements

`supabase_apply.yml` must emit a proof artifact that contains:

- target environment
- project ref used
- verification glob used
- commit SHA
- workflow run ID
- verification query outputs

## Honesty Rules

- Unknown live schema facts must remain labeled as unknown until proven.
- Repo documents may define intended design, but must not claim unverified live certainty.
- Dashboard edits are operational events, not authoritative schema truth, until repo artifacts match them.

## Future Engine Compatibility

Future engines must keep the same proof classes:

- migration artifact
- verification artifact
- rollback note
- contract or data-map deltas when ownership changes
- CI-emitted proof artifact
