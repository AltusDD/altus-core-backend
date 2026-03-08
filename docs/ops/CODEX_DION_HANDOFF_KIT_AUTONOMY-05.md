# CODEX DION HANDOFF KIT — AUTONOMY-05

## Open This Folder

`altus-core-backend` repository root.

## First Prompt To Run

`docs/ops/codex_prompt_pack/01_repo_inspection_prompt.md`

## What Success Looks Like

- Codex returns deterministic substitution mapping for current repo authorities.
- Codex confirms route/data/contract governance files are present.
- Codex confirms validators are runnable locally.
- Codex does not claim acceptance authority.

## What Artifacts Codex Should Return

- raw command outputs requested in prompt
- deterministic command list
- proof folder path when bundle assembly is requested
- final output shape aligned to `docs/governance/BE_FINAL_RETURN_TEMPLATE_V1.md` for execution milestones

## What Not To Let Codex Do

- do not allow "Codex accepts milestone" language
- do not allow contract bypass or route downgrade
- do not allow proof omission for runtime-affecting work
- do not allow CD authority or BE lane ownership changes

## Deterministic Operator Sequence

1. Run prompt 01 (inspection)
2. If correction needed, run prompt 02 (correction pass)
3. Run prompt 03 (bundle assembly)
4. Optionally run prompt 04 (no-modification audit)
5. Submit to BE validation

## Repo Substitutions (Required)

- control-plane docs: `AUTONOMY_CONTROL_PLANE_V1.md`, `AUTONOMY_DIRECT_EXECUTION_LOOP_V1.md`, `AUTONOMY_WORKER_BRIDGE_V1.md`
- acceptance bundle standard: `BE_ACCEPTANCE_BUNDLE_STANDARD_V1.md`
- final return template: `BE_FINAL_RETURN_TEMPLATE_V1.md`
- communication rules: packet markers and bridge workflow semantics in `AUTONOMY_WORKER_BRIDGE_V1.md` and `.github/workflows/worker_bridge.yml`
