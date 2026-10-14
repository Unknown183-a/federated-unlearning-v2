# Phase 15 — Error Handling, Reproducibility, Professor Demo Mode & Launch

> Status: **In Progress** — code and tests done; the end-to-end acceptance run on all 3 datasets still has to be done on a machine with PyTorch and the datasets.

## Goal

Final hardening pass: error handling across every stage, reproducibility guarantees, the presentation-safe professor demo mode, and launch readiness.

## In Scope

- Error handling for every failure surface (dataset, model, client, unlearning, evaluation)
- Reproducibility: seed + config always shown alongside every result
- Professor Demo Mode (10-15 minute guaranteed-safe walkthrough)
- Research transparency labeling pass (Measured/Precomputed/Live/Illustrative) across every screen
- Final QA against the full acceptance checklist

## Out of Scope

- New features — this phase is hardening and QA only

## Tasks

- [x] Implement error handling + clear messaging for every failure surface
- [x] Add configuration/seed display to every result screen
- [x] Build the guided Professor Demo Mode
- [x] Audit every screen for correct Measured/Precomputed/Live/Illustrative labeling
- [ ] Run the full acceptance checklist end to end on all 3 datasets (checker + checklist ready: `docs/ACCEPTANCE_CHECKLIST.md`)
- [x] Write final project README and demo script

## Deliverables

- Fully hardened, presentation-safe dashboard
- Final project README + demo script

## Depends On

Phase 14 (compute backend architecture)

## Acceptance Criteria

- The full research story (Dataset → ... → Retraining Comparison) replays correctly even with no live backend reachable
- Every acceptance criterion in the architecture reference document is checked off

## Progress Log

| Date | Update |
|------|--------|
| 2026-10 | **Errors.** `backend/src/errors.js` + `runEngine.js`: every engine failure now answers `{error, code, stage, detail, retryable}` (detail is one line, not a traceback with server paths). Unlearning failures name the stage (Gradient Ascent / Knowledge Distillation) from the persisted status. 15-minute engine timeout answers immediately. Express answers in JSON for 404s and bad bodies. `/api/compute/status` degrades to "Demo only" instead of a 500. Evaluation/retraining results that are not `complete` are refused (409) by the API and by the page. Experiment ids are validated (path-traversal hole closed). Frontend: `ErrorPanel` (Spec Ch.43 wording and recovery buttons), `ErrorBoundary`. **Reproducibility.** `core/provenance.py`; unlearning status now stores hyperparameters, seed and software version; `GET /api/experiments/:id/reproducibility`; collapsible config panel on every result page; missing values read "not recorded". **Labels.** One `ProvenanceBadge` replaces four copies of a chip; Data Distribution now loads a stored partition (it used to stay empty for loaded experiments); Overview has a legend. **Demo Mode.** Research / Professor Demo toggle, `/demo` launcher listing only fully replayable experiments, guide bar with timings, run buttons replaced by a replay note, training auto-replays. Added the spec's missing **Remove Influence** button. **Checker.** `python -m core.acceptance.cli`. **Verified:** 23 new torch-free tests pass (`tests/test_phase15.py`); the Express server was exercised with a fake Python for client, dataset, model, backend, not-supported, generic, bad-output, timeout and no-Python failures, plus path traversal, corrupt and incomplete files; the frontend builds, all 10 routes render, and the real app was driven in a simulated browser (jsdom) against the real backend through the whole Demo walkthrough (6 steps, no run buttons, config panel). **Full suite:** `pytest -m "not slow"` gives 128 passed on a fresh clone with the patch applied, including the new hyperparameter assertions in `tests/test_unlearning.py`. **Not verified / not done:** the 2 `slow` tests (real MNIST download) were not run (no torchvision or dataset access in the build sandbox); no real browser or projector was used; nothing was run on the three real datasets; the acceptance checklist is unticked until you do that. |

---
Previous: [Phase 14 — Backend Service Layer & Compute Backend Architecture](../phase-14-compute-backend-architecture/README.md)
Next: [Phase 16 — Model Releases & Update Policy](../phase-16-model-updates/README.md)
