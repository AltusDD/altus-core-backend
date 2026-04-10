Canonical Component Adoption Plan — Altus Core Backend

Status: CANONICAL

Approved Stack / Patterns
rangekeeper — wrap (service boundary only if architecture-fit)
ts-to-rls-demo — whole or concept import where governance-fit
nodejs-outbox pattern — pattern-only
supabase-management-js — whole where environment/schema management justifies it
Microsoft Graph Toolkit concepts are NOT backend UI dependencies and must remain outside FE/BE confusion
Required Outcomes
pricing service wrapper boundary note
event bus/writeback/outbox hardening note
RLS/schema governance workflow note
exact classification of adopted / deferred / pattern-only items
Key Rules
no contract drift
no route drift
no fake math embedding
no blind Python or Node installs without architecture-fit confirmation
