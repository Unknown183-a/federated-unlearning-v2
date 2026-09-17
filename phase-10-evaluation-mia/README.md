# Phase 10 — Evaluation & Membership Inference Attack

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

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

- [ ] Implement global/forget-client/retained-client accuracy evaluation
- [ ] Implement a Membership Inference Attack against the unlearned model
- [ ] Capture end-to-end unlearning runtime
- [ ] Build the Evaluation screen presenting all 5 metrics together

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

---
Previous: [Phase 09 — Knowledge Distillation & Live Unlearning Animation](../phase-09-knowledge-distillation/README.md)
Next: [Phase 11 — Before/After, Full Retraining Baseline & Runtime Comparison](../phase-11-comparison-retraining/README.md)
