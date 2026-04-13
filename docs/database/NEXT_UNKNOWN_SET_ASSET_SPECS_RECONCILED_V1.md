# NEXT UNKNOWN SET: `public.asset_specs_reconciled` Extra Live Columns

## Why This Unknown Set Comes Next

This is the final unresolved Database-lane unknown set after the canonical baseline, link-authority, hash-equivalence, and source-record-identity questions were proven and documented.

`public.asset_specs_reconciled` is already proven to exist in staging, but staging also exposes extra live columns beyond what any single repository migration currently proves. That means the remaining uncertainty is not table existence, but semantic intent and canonical ownership of the broader live column shape.

This comes next because future DB changes touching reconciled asset specifications should not proceed until we can distinguish:

- which extra live columns are currently present in staging
- whether those columns are materially populated or mostly empty
- whether they reflect intentional live authority or historical drift
- whether the repo should eventually adopt, tolerate, or replace that broader shape

## Proof Required Before Any Change

Before any schema or documentation canonicalization, staging proof should establish:

- the exact extra live columns currently present on `public.asset_specs_reconciled`
- each extra column's data type, nullability, and default value if any
- whether the extra columns are materially populated in non-sensitive staging rows
- whether indexes, constraints, or policies materially depend on those extra columns
- whether the extra columns appear to support current reconciled-spec persistence or are inert historical carry-forward fields

## Likely Next Move

The likely next move is **additional staging proof**.

Reason:

- repo truth already acknowledges that staging has a broader `asset_specs_reconciled` shape than any single migration proves
- no safe canonicalization decision should be made until we inspect the live extra columns directly
- the first narrow step is to add non-destructive verification SQL, not to change schema or rewrite canonical docs

## Explicit Non-Goals For The Next PR

- no schema migration yet
- no runtime handler changes
- no semantic redesign of reconciled specification storage yet
- no canonical doc rewrite until proof shows the live shape clearly enough to justify one
