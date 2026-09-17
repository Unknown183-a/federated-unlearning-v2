# Contributing

## Workflow

- Work through `phase-XX-*/` folders in order (see root `README.md`).
- Before starting a phase, read its `README.md` in full — especially
  "Depends On" and "Out of Scope".
- Update that phase's **Status** line and **Progress Log** table as work
  happens.

## Repo layout

```
frontend/     React (Vite) dashboard — UI only, no ML logic
backend/      Node/Express API — routes requests to a ComputeBackend
core/         Python ML logic (datasets, federated, unlearning, evaluation)
experiments/  Generated experiment artifacts (gitignored contents)
docs/         Architecture doc + full dashboard specification
```

## Coding conventions

- **Frontend**: functional React components, one component per file,
  colocate page components under `src/pages/`. No backend credentials
  or ML logic in frontend code, ever (spec Ch. 71.17).
- **Backend**: routes stay thin; anything backend-specific goes behind
  the `ComputeBackend` interface (`backend/src/compute/`) so the
  dashboard never depends on which backend is active.
- **Core**: standard Python, one concern per module, following the
  `core/federated/`, `core/unlearning/`, `core/evaluation/`,
  `core/datasets/` split from spec Ch. 49.
- Keep phases isolated — don't reach ahead into a later phase's scope.

## Environment variables

- Never commit `.env` files. Copy `.env.example` to `.env` locally.
- No secrets (SSH keys, GPU credentials, API keys) ever go in frontend
  code — server-side/env only (spec Ch. 71.17).
