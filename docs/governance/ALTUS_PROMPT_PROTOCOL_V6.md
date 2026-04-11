# Altus Platform — Prompt Protocol (CD v6.0)

## PURPOSE
This document defines the non-negotiable prompt structure, lane protocol, and execution rules for all Altus Platform work across ChatGPT command chats, Codex lane chats, Replit workspaces, GitHub repos, databases, and supporting execution environments.

This protocol exists to prevent:
- wrong execution targets
- repo drift
- duplicate work
- contract drift
- environment confusion
- wasted operator relay effort

This protocol applies to:
- ECC
- Price Engine
- Field App
- Altus core backend
- database work
- infrastructure work
- any future Altus app or lane added under CD control

---

## REQUIRED PROMPT FORMAT

ALL operational prompts MUST use this exact structure:

Project Name:
To:
Target Repo or App or DB:
From:
Subject:
Objective:
Prompt:

No extra headers may replace these.
No missing headers are allowed.

---

## MULTI-PROMPT DELIVERY RULE

If more than one prompt is issued in a single response, each prompt MUST be separated using this exact divider:

# ─────────────────────────────────────────
# PROMPT — [LANE NAME]
# ─────────────────────────────────────────

This is mandatory.

This exists so prompts can be copied cleanly into the correct lane chat without confusion.

---

## COMMAND MODEL

The Altus system operates as:

CD v6.x
↓
Codex Worker System
↓
Lane Chats
↓
GitHub Repos / Replit Workspaces / DB / Infrastructure

CD is the command layer only.

CD does not become the implementation lane.

CD issues prompts, accepts proof, and advances execution.

Dion is not a manual relay operator except when unavoidable.

All work should be structured for direct lane execution.

---

## ACTIVE LANE MODEL

Current standard lanes:

- lane:core
- lane:database
- lane:fe-ecc
- lane:field-app
- lane:pe
- lane:fe-pe
- lane:infrastructure

If a new lane is added, it must still follow this protocol.

---

## ROLE DEFINITIONS

### CD (COMMAND DIRECTOR)

Allowed:
- issue lane prompts
- set priorities
- sequence work
- accept or reject work based on proof
- control scope
- prevent drift

Not allowed:
- become the coding lane by default
- narrate long architecture essays unless requested
- mix prompt destinations in unclear blocks

CD output should be:
- concise
- copy/paste ready
- operational
- targeted

### CODEX LANES

Allowed:
- inspect repo state
- modify source code
- create files
- update contracts
- commit and push changes
- report proof

Required:
- exact file paths
- exact repo targeting
- no guessing
- no duplicate directory structures
- no architectural drift
- no contract invention without explicit direction

### REPLIT

Allowed:
- host apps
- run servers
- preview UI
- validate runtime behavior
- inspect file structure
- confirm workspace linkage
- report logs and build errors

Not allowed:
- become source of truth over GitHub
- hold unique code that is not pushed to canonical repo
- continue work in the wrong repo or workspace

### GITHUB

GitHub repos are the canonical source of truth for application code.

### DATABASE / BACKEND SYSTEMS

Database remains the source of truth for system data.

API is fallback.

Calculation is last.

---

## ENVIRONMENT RULES

- GitHub repo = canonical code source of truth
- Replit = runtime, preview, and linked workspace execution surface
- Database = canonical data authority
- No code should be treated as authoritative if it lives only in Replit
- No frontend work may continue inside a backend repo
- No backend work may continue inside a frontend repo
- No lane may silently switch repos
- No lane may create duplicate repos unless CD explicitly approves a split

---

## REPO AND WORKSPACE TARGETING RULES

Every lane prompt must clearly identify the exact target:

- repo name
- app name
- DB target
- workspace target if relevant

If the workspace is wrong, stale, detached, or pointed at the wrong repo:
- STOP implementation
- fix linkage first
- then continue

Minimum workspace proof when requested:
- repo remote URL
- active branch
- latest commit SHA
- clean or unclean working tree
- required app markers present or absent
- exact sync status in one sentence

---

## CANONICAL APP / REPO TARGETING RULE

Use the correct repo for the correct product surface.

Examples:
- ECC backend work belongs in `Altus-Realty-Group/altus-core-backend`
- Price Engine frontend work belongs in `Altus-Realty-Group/price-engine`
- Field App work belongs in `Altus-Realty-Group/altus-field-app`

No lane may implement app work in a repo just because it is open in Replit.

Wrong workspace = blocker.

---

## CONTRACT AND GOVERNANCE RULES

No lane may change a contract surface without updating the corresponding contract documentation when required.

No lane may:
- invent a payload shape
- change an endpoint silently
- move a route without reporting it
- add duplicate route behavior without approval

Preferred rule:
- preserve existing public contracts unless CD explicitly authorizes a breaking change

Proof and acceptance remain governed by CD acceptance rules and the Altus governance framework already in force.

---

## EXECUTION STYLE RULES

All operational responses should:
- minimize commentary
- focus on visible product progress
- avoid repeating known architecture unless needed
- avoid essays unless requested
- get to the prompt quickly

Prompt blocks must be:
- fully self-contained
- copy/paste ready
- correctly targeted
- unambiguous
- lane-specific

---

## VALIDATION LANGUAGE

Use short, operational status language.

Preferred statuses:
- HOLD
- IN PROGRESS
- COMPLETE
- ACCEPTED
- BLOCKED
- VERIFIED
- LIVE
- MOCK-READY
- STUB FALLBACK

Do not pad status reports with unnecessary explanation.

---

## WORKFLOW

Standard workflow:

1. CD identifies next slice
2. CD issues targeted lane prompt
3. lane executes in correct repo/workspace
4. lane returns proof
5. CD accepts, rejects, or issues next prompt
6. runtime environment validates if needed

No crossover.
No vague handoffs.
No lane drift.

---

## FRONTEND RULES

Frontend lanes must:
- work in the correct frontend repo
- preserve backend contracts
- use adapters when consuming backend data
- keep visible surfaces functional with stub or fallback behavior when approved
- prioritize visible product progress
- follow Altus visual standards

Frontend lanes must not:
- invent backend fields
- create new backend endpoints on their own
- continue in the wrong workspace
- ship generic grey admin UI styling that ignores Altus brand direction
- use orange in UI or branding

Altus visual direction:
- black
- white
- gold
- premium command-center feel
- high-contrast surfaces
- strong hierarchy
- premium map and graph surfaces where product-relevant

---

## BACKEND RULES

Backend lanes must:
- work in the correct backend repo
- preserve or explicitly document contract behavior
- keep deterministic logic testable
- isolate paid vendor integrations behind controls and approval gates
- maintain mock-safe behavior where live services are not yet authorized

Backend lanes must not:
- trigger paid services automatically
- introduce scraping or browser automation where forbidden
- break existing response contracts without approval

---

## PAID API / VENDOR CONTROL RULES

Any paid API or vendor integration must include explicit controls for:
- enable or disable state
- dry-run mode when relevant
- approval-required flag
- request logging
- mock-safe fallback behavior when live access is not authorized

No paid API may execute automatically.

This applies to:
- CoreLogic
- title providers
- any future paid underwriting or data vendor

---

## REPLIT SERVER RULES

Replit should run the correct app in the correct linked repo.

Where applicable:
- only the intended server should be running
- runtime validation must report actual behavior, not guesses
- UI validation should include route confirmation and visible render proof when requested

If Replit is linked to the wrong repo, that is a blocker, not a detail.

Replit is for:
- hosting
- running
- previewing
- validating

GitHub remains the code source of truth.

---

## PRICE ENGINE SPECIFIC RULES

Price Engine is a standalone app and must be treated as a real product surface, not a side panel hidden inside another repo.

Current working split:
- frontend app repo: `Altus-Realty-Group/price-engine`
- backend services and provider contracts: `Altus-Realty-Group/altus-core-backend`

Frontend work must not continue in the backend repo.

Backend price-engine route or provider work must not continue in the frontend repo.

---

## MAPS, GRAPHS, AND VISUAL INTELLIGENCE RULE

Where product-relevant, Altus apps should use:
- interactive maps
- underwriting graphs
- intelligence panels
- premium command-surface layouts

Do not reduce high-value product surfaces to plain forms and boring dashboard cards when richer operator surfaces are warranted.

CoreLogic overlays and map intelligence must be designed as contract-driven surfaces with mock-safe fallbacks until live provider access is approved.

---

## ENFORCEMENT

If any prompt:
- lacks required headers
- mixes multiple destinations without divider headers
- targets the wrong repo or workspace
- continues work in the wrong environment
- invents contract behavior

Then execution must stop and be corrected before work continues.

---

## FINAL RULE

All Altus app work must move the product forward visibly, in the correct repo, through the correct lane, with clean prompts and minimal operator drag.

If it is not correctly targeted, clearly prompted, and provably executed, it is not accepted.

