# Phase 12 — Quick Unlearning Demo & Model Library

> Status: **Complete**
> Implementation: the experiment registry (aggregated from each phase's own stored artifacts), Page 1's two-mode Overview, the Model Library, and Page 9 Experiment History are live on main.

## Goal

Let a user skip straight to unlearning using an already-trained model, and give them a library of past experiments to pick from.

## In Scope

- Experiment artifact schema (global model, partition info, FL history, unlearning history, MIA, runtime, retraining comparison)
- Model Library screen (page 9)
- Quick Unlearning Demo flow, reusing Phases 07-11 with a loaded model

## Out of Scope

- New ML logic — this phase is wiring, not new algorithms

## Tasks

- [x] Define and implement the experiment artifact folder structure
- [x] Build save/load for experiment artifacts
- [x] Build the Model Library screen (Page 9)
- [x] Wire the Quick Demo entry point to load an artifact directly into Phase 07's state

## Deliverables

- Complete Page 9: Experiment History
- Working Quick Demo end to end

## Depends On

Phase 11 (comparison)

## Acceptance Criteria

- A stored experiment can be loaded and replayed through Pages 5-8 without retraining
- The Quick Demo completes in under 15 minutes end to end

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | Rather than inventing a second, parallel "experiment manifest" file (Ch.30) that could drift out of sync with the artifacts each earlier phase already owns and writes (`partition.json`, `fl_history.json` + `global_model.pt`, `unlearning_status.json`, `evaluation_results.json`, `retraining_results.json`), the "experiment artifact schema" this phase asked for is implemented as a read-only aggregator: `backend/src/routes/experiments.js` scans `experiments/*/` and, for each experiment_id, reads whichever of those files already exist (tolerating any subset -- a directory with only `partition.json` is as valid as one with everything) to derive a summary -- dataset, num_clients, model, rounds, final_accuracy, target_client_id, a `stages` object (partitioned/trained/unlearned/evaluated/compared), a single derived `status` label, and an `updated_at` sort key from the newest artifact's mtime. This is pure JSON aggregation with no ML logic (explicitly out of scope for this phase), so it lives directly in Express rather than shelling out to Python, same pattern as this project's other plain-JSON GET handlers. `GET /api/experiments` (Page 9, every experiment regardless of how far it got) and `GET /api/experiments?trained_only=true` (the Quick Demo's Model Library -- only experiments with an actual `global_model.pt` on disk, matching Ch.27's "READY" status) share the same summaries, just filtered differently; `GET /api/experiments/:id` returns one. `ExperimentContext.jsx` gained `loadExperiment(summary)`, which overwrites (not merges) the current draft config with a stored experiment's id and known fields and sets `training_mode: "load_existing"` -- used identically by both entry points so a reopened experiment behaves the same regardless of which one brought the user there. `Overview.jsx` (was a stub) implements the Ch.2 two-mode landing page: "Start Complete Experiment" goes to Setup for the fresh draft experiment_id already generated on load; "Start Quick Demo" reveals the Model Library grid (`ModelLibraryCard.jsx`, one card per trained experiment, `[ Select ]` per Ch.27's wireframe) inline, and selecting a card calls `loadExperiment` then navigates straight to Client Selection (Page 5) -- skipping Setup/Partition/Training entirely, satisfying "this mode should avoid full FL training" (Ch.28). `ExperimentHistory.jsx` (was a stub) implements Page 9: every experiment in a status-colored table, "Open" doing the same `loadExperiment` + navigate-to-Client-Selection as the Quick Demo. No change was needed to Client Selection, Unlearning, Evaluation, or Retraining Comparison themselves -- each already re-reads its own stored artifact for whatever `config.experiment_id` currently is and replays it as "Stored Experiment" rather than re-running anything (built in Phases 07-11), which is exactly the "loaded and replayed through Pages 5-8 without retraining" acceptance criterion. Verified: `node --check` on the new/edited backend files; the registry's listing/filtering/status-derivation/sort-order logic exercised directly against a fixture `experiments/` directory (this repo has no JS test framework, so this matches how the other hand-rolled route logic in this project has been checked); the live Express server boots and all three endpoints (`/api/experiments`, `?trained_only=true`, `/api/experiments/:id`) were curled against both an empty and a populated real `experiments/` directory (cleaned up afterward, not committed); `npm run build` clean; and the full Python suite unaffected -- `pytest tests/ -m "not slow"` still 67 passed, since this phase touched no `core/` code at all. |

---
Previous: [Phase 11 — Before/After, Full Retraining Baseline & Runtime Comparison](../phase-11-comparison-retraining/README.md)
Next: [Phase 13 — Dashboard UX — Navigation, State & Visual Design System](../phase-13-dashboard-ux/README.md)
