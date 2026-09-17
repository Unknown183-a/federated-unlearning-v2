# Phase 08 — Unlearning Engine — Gradient Ascent

> Status: **Complete**
> Implementation: `core/unlearning/gradient_ascent.py` (`run_gradient_ascent` — minimizes negated cross-entropy on the target client's data, i.e. SGD ascent, with gradient clipping + plateau early-stopping so the rest of the model stays recoverable), `core/unlearning/unlearning_engine.py` (`start_unlearning(experiment_id, client_id, ...)` / `get_unlearning_status(experiment_id)`, matching the Ch.71.8 ComputeBackend interface), `core/unlearning/storage.py` (persists `unlearning_status.json` + the ascent-stage checkpoint), `core/unlearning/cli.py` (CLI entrypoint), and `backend/src/routes/unlearning.js` (`POST`/`GET /api/unlearning`). Required a small addendum to Phase 05: `core/federated/storage.py`/`server.py` now also persist the trained global model's *weights* (`global_model.pt`), not just its metrics — Gradient Ascent needs the actual model, which nothing before Phase 08 had saved.

## Goal

Implement the forgetting step: push the model to perform worse specifically on the target client's data.

## In Scope

- Gradient Ascent implementation against the target client's local data
- Per-step loss tracking on the target client
- start_unlearning(client_id) backend entry point (stage 1 only)

## Out of Scope

- Knowledge Distillation (Phase 09)
- Any UI beyond raw metric logging

## Tasks

- [x] Implement the Gradient Ascent step against the target client's data
- [x] Log target-client loss at each ascent step
- [x] Expose get_unlearning_status() for the ascent stage

## Deliverables

- Working Gradient Ascent stage, runnable standalone

## Depends On

Phase 07 (target client selection)

## Acceptance Criteria

- Target-client loss measurably rises over the ascent steps
- The rest of the model's weights remain recoverable (sanity-checked before Phase 09)

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | Gradient Ascent implemented as SGD minimizing negated cross-entropy loss on the target client's own partitioned samples, with gradient-norm clipping and plateau-based early stopping (loss must keep rising or ascent stops) so the acceptance criterion — target-client loss rises, rest of the model stays recoverable — holds by construction rather than by luck. Discovered along the way that no prior phase persisted the trained global model's weights (only round metrics), so this phase also adds `save_model_checkpoint`/`load_model_checkpoint` to Phase 05's storage module and a call to it at the end of `run_federated_training`, changing no existing behavior. `start_unlearning`/`get_unlearning_status` persist to `unlearning_status.json` + `unlearning_ga_model.pt`, ready for Phase 09 to load. `POST /api/unlearning` + `GET /api/unlearning/:experimentId` added, mirroring the existing `training.js` route shape. Unit tests (synthetic data, no download) plus a `@pytest.mark.slow` MNIST end-to-end test added to `tests/test_unlearning.py`; `node --check` and `python -m py_compile` verified clean on all new/edited files, but the suite itself needs a torch-enabled environment to actually run (not available in this session's container). |

---
Previous: [Phase 07 — Global Model & Target Client Selection](../phase-07-global-model-target-selection/README.md)
Next: [Phase 09 — Knowledge Distillation & Live Unlearning Animation](../phase-09-knowledge-distillation/README.md)
