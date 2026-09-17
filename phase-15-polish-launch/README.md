# Phase 15 — Error Handling, Reproducibility, Professor Demo Mode & Launch

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

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

- [ ] Implement error handling + clear messaging for every failure surface
- [ ] Add configuration/seed display to every result screen
- [ ] Build the guided Professor Demo Mode
- [ ] Audit every screen for correct Measured/Precomputed/Live/Illustrative labeling
- [ ] Run the full acceptance checklist end to end on all 3 datasets
- [ ] Write final project README and demo script

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
| — | Phase not started |

---
Previous: [Phase 14 — Backend Service Layer & Compute Backend Architecture](../phase-14-compute-backend-architecture/README.md)
Next: None (final phase)
