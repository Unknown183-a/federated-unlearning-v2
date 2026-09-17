# Phase 12 — Quick Unlearning Demo & Model Library

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

## Goal

Let a user skip straight to unlearning using an already-trained model, and give them a library of past experiments to pick from.

## In Scope

- Experiment artifact schema (global model, partition info, FL history, unlearning history, MIA, runtime, retraining comparison)
- Model Library screen (page 9)
- Quick Unlearning Demo flow, reusing Phases 07-11 with a loaded model

## Out of Scope

- New ML logic — this phase is wiring, not new algorithms

## Tasks

- [ ] Define and implement the experiment artifact folder structure
- [ ] Build save/load for experiment artifacts
- [ ] Build the Model Library screen (Page 9)
- [ ] Wire the Quick Demo entry point to load an artifact directly into Phase 07's state

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

---
Previous: [Phase 11 — Before/After, Full Retraining Baseline & Runtime Comparison](../phase-11-comparison-retraining/README.md)
Next: [Phase 13 — Dashboard UX — Navigation, State & Visual Design System](../phase-13-dashboard-ux/README.md)
