# Phase 11 — Before/After, Full Retraining Baseline & Runtime Comparison

> Status: **Complete**
> Implementation: full-retraining-from-scratch baseline (excludes the target client, reuses the original run's protocol), original vs unlearned vs retrained comparison, and Page 8, are live on main.

## Goal

Prove unlearning was worth doing by comparing it against the original model and against retraining from scratch.

## In Scope

- Before/after visualization, reusing Phase 10's metrics
- Full retraining baseline pipeline (exclude target client, retrain from scratch)
- Runtime comparison chart (unlearning vs retraining)
- Page 8 (full)

## Out of Scope

- Quick Demo mode (Phase 12)

## Tasks

- [x] Build the before/after side-by-side comparison view
- [x] Implement the full-retraining baseline pipeline (typically run offline)
- [x] Store retraining results as a stored artifact
- [x] Build the runtime comparison chart

## Deliverables

- Complete Page 8: Retraining Comparison

## Depends On

Phase 10 (evaluation)

## Acceptance Criteria

- Retraining baseline numbers are clearly labeled as a separate run
- Runtime chart shows unlearning as a small fraction of retraining cost

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | `core/federated/server.py` split into `fedavg_train()` (the FedAvg loop, no persistence -- returns `(history, final_state_dict)`) and `run_federated_training()` (the existing persisting wrapper, now a thin call to `fedavg_train` + save), so the retraining baseline can reuse the identical training loop against a reduced partition without writing over the original experiment's `fl_history.json`/`global_model.pt`. `core/evaluation/evaluation_engine.py` similarly had its per-checkpoint metric computation pulled out into `evaluate_model_state()` (global/forget/retained accuracy + MIA for one set of weights), reused by both `evaluate_experiment` (before/after) and the new retraining pipeline, so all three models -- original, unlearned, retrained -- are scored by exactly the same code against the same target-client indices and MIA non-member set. `core/evaluation/retraining.py`'s `run_retraining_baseline()`: loads the completed unlearning status (for the target client) and the stored Phase 10 evaluation (for the MIA non-member sample size, and to reject a stale evaluation for a different target with a clear error), builds a partition with the target client's shard dropped, reruns FedAvg with the *same* model/rounds/local_epochs/seed/lr/batch_size as the original run (falls back to this project's existing defaults for lr/batch_size on `fl_history.json` files written before this addendum started recording them), evaluates the result with `evaluate_model_state`, and persists both the weights (`retrained_model.pt`) and results (`retraining_results.json`, tagged `run_kind: "separate_retraining_baseline"`) -- never touching the original experiment's files. `core/evaluation/comparison.py` (was a one-line stub): `build_comparison()`/`compare_with_retraining()` line up original/unlearned/retrained for the four Page 7 metrics and compute the runtime comparison honestly per Ch.25 -- a speedup is only reported when both times exist, and if unlearning was *not* faster the result says so (negative `time_saved_seconds`, `unlearning_faster: false`) rather than being hidden or clamped. This module is pure data (reads the two stored JSON artifacts) and needs no torch, so `core/evaluation/retraining_cli.py` exposes a `--compare-only` flag that re-runs just the comparison without importing torch at all -- the common case once a baseline already exists. Wired up `POST /api/retraining` + `GET /api/retraining/:experimentId` + `GET /api/retraining/:experimentId/comparison` (mirrors the other Python-backed routes), and Page 8 (`RetrainingComparison.jsx` + `RetrainingComparisonChart.jsx` grouped-bar component + `RuntimeComparisonChart.jsx`): gated on a completed Phase 10 evaluation (not on the baseline itself, which this page is what triggers), loads any previously stored comparison on mount, a "Run Retraining Baseline" button that also warns this is roughly as expensive as the original training run, and a closing panel restating the forgetting/utility/efficiency framing from Ch.55. Verified: `python3 -m py_compile` on every new/edited module, `node --check` on the new/edited backend files, `npm run build` clean, and -- with a working torch install in this session's container (`pip install torch`, ~5.7 GB of CUDA wheels, fit in the ~10 GB free here) -- the new `tests/test_retraining.py` (comparison-math tests with no torch dependency, plus a synthetic partition→train→unlearn→evaluate→retrain pipeline test asserting the retrained federation excludes exactly the target client, the original experiment's files are byte-for-byte untouched afterwards, and both the legacy-lr/batch-size fallback and the stale-evaluation rejection work) and the full existing suite: `pytest tests/ -m "not slow"` (67 passed). The two `slow`-marked MNIST-download integration tests (`test_federated.py`, `test_unlearning.py`) still fail in this sandbox exactly as Phase 10 documented -- no network access for the actual dataset download -- unrelated to this phase's changes. |

---
Previous: [Phase 10 — Evaluation & Membership Inference Attack](../phase-10-evaluation-mia/README.md)
Next: [Phase 12 — Quick Unlearning Demo & Model Library](../phase-12-quick-demo-model-library/README.md)
