# Phase 16 — Model Releases & Update Policy

> Status: **Complete**
> Implementation: `core/distribution/` (release rules and CLI), `backend/src/routes/releases.js`, and the **Model Updates** page are live on main. See [`docs/MODEL_UPDATES.md`](../docs/MODEL_UPDATES.md).

## Goal

Show what happens after unlearning when devices have already installed the old model: publish the unlearned model as a new version, ask or force devices to switch, and revoke the old version.

## In Scope

- Versioned model releases (v1 = original global model, later versions = unlearned models)
- Simulated devices (up to 100) with an online/offline state and a simulated clock
- Two update policies: **Auto update**, and **Request, then force after a deadline** (1 to 8760 hours)
- Event log of every publish, request, accept, forced update and revocation
- Integrity record: each release is copied to `experiments/<id>/releases/model_v<N>.pt` with its SHA-256
- Model Updates page (Research mode), labelled *Illustrative*

## Out of Scope

- Real device apps, push notifications or a real clock (devices and time are simulated)
- Signed manifests (asymmetric keys); integrity is a hash only
- Deleting old copies from devices, which the server cannot do

## Tasks

- [x] Release rules and storage (`core/distribution/releases.py`, standard library only)
- [x] CLI (`core/distribution/cli.py`)
- [x] API routes (`/api/releases/:experimentId/...`)
- [x] Model Updates page with simulated clock, device list and event log
- [x] Tests (`tests/test_releases.py`)
- [x] User documentation with stated limits (`docs/MODEL_UPDATES.md`)

## Deliverables

- `experiments/<id>/model_releases.json` (releases, devices, clock, event log)
- Immutable per-version model copies with recorded SHA-256

## Depends On

Phase 08/09 (a finished unlearning run to publish) and Phase 15 (error handling and labelling conventions)

## Acceptance Criteria

- An unlearned model can only be published after a finished unlearning run, and the same unlearned model cannot be published twice
- Auto update revokes the old version at once; Request-then-force revokes it only after the deadline
- Offline devices are handled when they reconnect, according to the policy
- The page states that devices and the clock are simulated and that old copies are not deleted

## Progress Log

| Date | Update |
|------|--------|
| 2026-10 | Implemented in the Phase 16 commit (see `git log`). Documentation index added afterwards: this folder, the README phase index and the Phase 15 "Next" link. `tests/test_releases.py` passes; the page was not exercised in a real browser. |

---
Previous: [Phase 15 — Error Handling, Reproducibility, Professor Demo Mode & Launch](../phase-15-polish-launch/README.md)
Next: None (final phase)
