# Contracts README

This folder holds contract-facing documentation for database-backed behavior.

## Rules

- Update contract docs when a DB change affects API-visible fields, source-of-truth ownership, or downstream consumer expectations.
- Update docs/architecture/DATA_MAP_V1.md whenever a DB task changes canonical data ownership, fallback authority, or contract-relevant data sources.
- Repo truth is authoritative. Dashboard-only schema edits are not authoritative until they are backfilled into repository artifacts.

## Inventory Authority

- Current schema inventory authority: docs/database/SCHEMA_INVENTORY_V1.md (staging baseline)

## Current Contracts

- docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md — missing on main; treated as unproven until reintroduced with proof.

## Database Autonomy Linkage

- Execution model: docs/database/DB_AUTONOMY_EXECUTION_MODEL_V1.md
- Change SOP: docs/database/DB_CHANGE_SOP_V1.md
- Proof requirements: docs/database/DB_PROOF_REQUIREMENTS_V1.md
