# Phase 10 — Evaluation & Membership Inference Attack

> Status: **Complete**
> Implementation: global/forget-client/retained-client accuracy, a loss-threshold Membership Inference Attack, and runtime, each measured before and after unlearning, plus Page 7.

## Goal

Measure whether unlearning actually worked: global accuracy, forget-client accuracy, retained-client accuracy, MIA, and runtime.

## In Scope

- Evaluation metric computation for all 5 metrics
- Membership Inference Attack implementation
- Runtime measurement for the full unlearning pipeline
- Page 7 (full)

## Out of Scope

- Before/after comparison UI (Phase 11)

## Tasks

- [x] Implement global/forget-client/retained-client accuracy evaluation
- [x] Implement a Membership Inference Attack against the unlearned model
- [x] Capture end-to-end unlearning runtime
- [x] Build the Evaluation screen presenting all 5 metrics together

## Deliverables

- Complete Page 7: Evaluation

## Depends On

Phase 09 (Knowledge Distillation)

## Acceptance Criteria

- All 5 metrics compute correctly for a full run
- MIA results move toward chance level on a successful unlearning run

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | `core/evaluation/accuracy.py` (global/forget-client/retained-client accuracy, independent of Phase 09's own training-time logging — the Dashboard Spec keeps the Evaluation Engine a separate backend service) and `core/evaluation/mia.py` (loss-threshold MIA, Yeom et al. 2018: sweep every observed loss as a candidate "member if loss ≤ threshold" cut, report balanced attack accuracy on an equal member/non-member split — 0.5 is chance, 1.0 is perfect). `evaluation_engine.evaluate_experiment()` requires a completed `unlearning_status` (Phase 08+09), loads both the original (`before`) and final unlearned (`after`) checkpoints, runs all three accuracy metrics plus the MIA against each, and reuses the Gradient Ascent / Knowledge Distillation durations already recorded in `unlearning_status` for the runtime metric rather than re-timing them. Results persist to `experiments/<id>/evaluation_results.json`. Wired up `core/evaluation/cli.py` (mirrors `core/unlearning/cli.py`), `POST /api/evaluation` + `GET /api/evaluation/:experimentId` (mirrors `backend/src/routes/unlearning.js`), and Page 7 (`Evaluation.jsx` + `EvaluationMetrics.jsx`): gated on a completed unlearning run, loads any previously stored result on mount, a "Run Evaluation" button for a fresh measurement, four before/after metric cards color-coded by whether that metric's own good direction (accuracy up, MIA down) improved, and a runtime breakdown. Verified: `python3 -m py_compile` on every new module, `node --check` on the new/edited backend files, and `npm run build` (frontend) all clean in this session's container. Could not get a working torch install in this sandbox to run `tests/test_evaluation.py` itself this session — the CUDA-bundled `torch` wheel from PyPI (the only index this sandbox's network allowlist permits; `download.pytorch.org`'s CPU-only builds aren't reachable) needs more disk than the ~2.8 GB free here, and forcing a `--no-deps` install left `torch` unable to even do a CPU matmul (`Bus error` on import-time init). `tests/test_evaluation.py` is written to the same patterns and monkeypatching style Phase 09's tests use (synthetic in-memory datasets, `EXPERIMENTS_DIR` redirected to `tmp_path`) and should be run with `pytest tests/test_evaluation.py` wherever a full torch install fits, including CI. |
| — | Follow-up session: got a working torch install after all and actually ran the suite (the earlier Bus error traced to a corrupted/truncated `libcublasLt.so` left over from a disk-full install attempt in an *even earlier* session -- a stray `rm -rf .../nvidia` cleanup then wiped out several other CUDA libs' files while leaving their pip metadata behind, so `pip install torch` kept reporting them "already satisfied" without ever re-downloading them; fixed by `pip install --force-reinstall --no-deps` on just the affected `nvidia-*` packages). With torch actually importable, `pytest tests/test_evaluation.py` caught one real bug: `evaluate_retained_accuracy`'s `per_client` dict was keyed by the integer `client_id`, so `evaluate_experiment()`'s freshly-computed result and the same result reloaded from `evaluation_results.json` were unequal (JSON object keys are always strings) -- `retained_client_accuracy_per_client` looked like `{0: ...}` in one and `{"0": ...}` in the other. Fixed by keying `per_client` with `str(client_id)` from the start, which also matches the string-keyed convention `ClientInfluenceBars.jsx` already assumes for this exact shape coming out of `unlearning_status.json`. Verified: `pytest tests/ -m "not slow"` (51 passed) including the full synthetic partition→train→unlearn→evaluate pipeline test, plus a manual end-to-end smoke test of `python -m core.evaluation.cli` itself as a subprocess (fails cleanly with a `ModuleNotFoundError: torchvision` traceback on stderr and exit code 1, since MNIST needs network access this sandbox doesn't allow -- confirms the CLI/argparse/error-surfacing path backend/src/routes/evaluation.js relies on works correctly, independent of the dataset being unavailable here). `npm run build` still clean. |

---
Previous: [Phase 09 — Knowledge Distillation & Live Unlearning Animation](../phase-09-knowledge-distillation/README.md)
Next: [Phase 11 — Before/After, Full Retraining Baseline & Runtime Comparison](../phase-11-comparison-retraining/README.md)
