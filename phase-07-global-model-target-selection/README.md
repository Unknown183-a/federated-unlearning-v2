# Phase 07 — Global Model & Target Client Selection

> Status: **Complete**
> Implementation: `frontend/src/components/GlobalModelSummary.jsx` (architecture, dataset, experiment ID, final accuracy/loss, rounds, clients, seed) and an extended `ClientCard`/`ClientCardGrid` (Phase 04, now with optional `selectable`/`selected`/`onSelect` props) reused as the target-client picker. Wired together in `frontend/src/pages/ClientSelection.jsx`, which re-reads the already-persisted `GET /api/training/:experimentId` and `GET /api/partition/:experimentId` for the current experiment (no re-running anything) and writes the chosen client into `ExperimentContext`'s new `target_client_id` field.

## Goal

Present the trained global model as a first-class object and let the user pick which client to forget.

## In Scope

- Global model summary card (architecture, final accuracy/loss, experiment ID)
- Target client picker, reusing the client card from Phase 04
- Page 5 (full)

## Out of Scope

- Unlearning logic itself (Phases 08-09)

## Tasks

- [x] Build the global model summary card
- [x] Build the target client picker screen, linking to each client's Phase 04 card
- [x] Persist target_client_id into the shared experiment state

## Deliverables

- Complete Page 5: Client Selection

## Depends On

Phase 06 (FL visualization)

## Acceptance Criteria

- Selecting a target client correctly carries into the unlearning phase's state

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | Page 5 built end to end: `GlobalModelSummary` reads the persisted `fl_history` (architecture, dataset, experiment ID, final accuracy/loss, rounds × local epochs, clients, seed); `ClientCard`/`ClientCardGrid` gained `selectable`/`selected`/`onSelect` props (default off, so Phase 04's Data Distribution usage is unchanged) and are reused directly as the picker, with a "Target" badge on the chosen card. Selecting a card writes `target_client_id` into `ExperimentContext`, which resets to `null` if the dataset changes. If no training/partition exists yet for the experiment, the page warns and links back to Federated Learning. `frontend/npm run build` verified clean. |

---
Previous: [Phase 06 — Federated Learning Visualization & Metrics](../phase-06-fl-visualization/README.md)
Next: [Phase 08 — Unlearning Engine — Gradient Ascent](../phase-08-gradient-ascent/README.md)
