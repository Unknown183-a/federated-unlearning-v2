# Phase 11 — Before/After, Full Retraining Baseline & Runtime Comparison

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

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

- [ ] Build the before/after side-by-side comparison view
- [ ] Implement the full-retraining baseline pipeline (typically run offline)
- [ ] Store retraining results as a stored artifact
- [ ] Build the runtime comparison chart

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

---
Previous: [Phase 10 — Evaluation & Membership Inference Attack](../phase-10-evaluation-mia/README.md)
Next: [Phase 12 — Quick Unlearning Demo & Model Library](../phase-12-quick-demo-model-library/README.md)
