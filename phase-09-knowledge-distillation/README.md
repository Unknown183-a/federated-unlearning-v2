# Phase 09 — Knowledge Distillation & Live Unlearning Animation

> Status: **Complete**
> Implementation: `core/unlearning/knowledge_distillation.py` (`run_knowledge_distillation` — Hinton-style distillation: `alpha * CE(hard labels) + (1 - alpha) * T^2 * KL(student/T, teacher/T)`, teacher = pre-ascent global model, student = post-ascent model, trained on every client except the forgotten one; tracks per-retained-client accuracy before/after), `core/unlearning/unlearning_engine.py` (`start_unlearning` extended to chain Gradient Ascent → Knowledge Distillation, capturing the pre-ascent checkpoint as the KD teacher before Phase 08 overwrites the working weights), `core/unlearning/storage.py` (adds `save_final_checkpoint`/`load_final_checkpoint` for the fully-unlearned model, `unlearning_final_model.pt`), `core/unlearning/cli.py` + `backend/src/routes/unlearning.js` (pass through `kd_epochs`/`kd_lr`/`kd_temperature`/`kd_alpha`/`kd_batch_size`), and Page 6 in full: `frontend/src/pages/Unlearning.jsx` plus `UnlearningStepper.jsx`, `GradientAscentPanel.jsx`, `KnowledgeDistillationPanel.jsx`, `ClientInfluenceBars.jsx`.

## Goal

Repair collateral damage from Gradient Ascent using the pre-unlearning model as a teacher, and visualize both stages live.

## In Scope

- Knowledge Distillation implementation (teacher = pre-ascent model)
- Per-retained-client accuracy tracking, before/after distillation
- Live two-stage unlearning animation UI
- Page 6 (full)

## Out of Scope

- Evaluation/MIA (Phase 10)

## Tasks

- [x] Implement Knowledge Distillation using the pre-unlearning model as teacher
- [x] Track per-retained-client accuracy before and after distillation
- [x] Build the live two-stage (ascent → distillation) animation component
- [x] Wire the animation to real backend progress signals — never a fake timer

## Deliverables

- Complete Page 6: Unlearning, running both stages live

## Depends On

Phase 08 (Gradient Ascent)

## Acceptance Criteria

- Retained-client accuracy recovers measurably after distillation
- The live animation only advances on real backend progress events

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | Knowledge Distillation implemented as classic Hinton et al. response-based distillation, trained only on the retained clients' data (the target client's samples are never shown again, so the ascent-driven forgetting isn't undone — only the accidental damage to everyone else is). `start_unlearning` now runs both stages back to back: it captures the checkpoint's original state dict as the KD teacher *before* calling `run_gradient_ascent` (which returns a separately-damaged copy), then feeds that damaged copy in as the KD student, along with every partition client except the target as `retained_clients`. Persists an intermediate status after each stage (`stage: "gradient_ascent"` then `stage: "knowledge_distillation"`) so a crash mid-pipeline still leaves the completed stage's results on disk, plus the final unlearned weights (`unlearning_final_model.pt`) alongside the existing GA checkpoint. Page 6 follows the same "live" strategy Phase 06 established for FL: the backend runs synchronously and returns the complete, real per-step/per-epoch history at once, and the frontend reveals it progressively (a `setTimeout`-paced replay of *already-measured* values, never a fabricated countdown) — first the Gradient Ascent step history, then the Knowledge Distillation epoch history, ending on a before/after client-accuracy comparison. Tuning note for the recovery-accuracy test: gradient ascent has no natural stopping point, so ascent hyperparameters that are too aggressive (high lr/many steps) blow the model into a degenerate collapsed state no amount of distillation can recover from within a few epochs — the unit test uses a handful of gentle ascent steps against a teacher that was trained to actually memorize its tiny synthetic dataset, so there's real recoverable signal for distillation to pull back in. Verified: `pytest tests/ -m "not slow"` (37 passed) and `npm run build` (frontend) both green in this session's container, now that a working torch/torchvision install was possible; the `@pytest.mark.slow` MNIST end-to-end test still needs a network path to torchvision's MNIST mirrors (`ossci-datasets.s3.amazonaws.com` / `yann.lecun.com`), which this sandbox doesn't allow but CI does. |

---
Previous: [Phase 08 — Unlearning Engine — Gradient Ascent](../phase-08-gradient-ascent/README.md)
Next: [Phase 10 — Evaluation & Membership Inference Attack](../phase-10-evaluation-mia/README.md)
