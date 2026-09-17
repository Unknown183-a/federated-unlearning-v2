# Phase 09 — Knowledge Distillation & Live Unlearning Animation

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

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

- [ ] Implement Knowledge Distillation using the pre-unlearning model as teacher
- [ ] Track per-retained-client accuracy before and after distillation
- [ ] Build the live two-stage (ascent → distillation) animation component
- [ ] Wire the animation to real backend progress signals — never a fake timer

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

---
Previous: [Phase 08 — Unlearning Engine — Gradient Ascent](../phase-08-gradient-ascent/README.md)
Next: [Phase 10 — Evaluation & Membership Inference Attack](../phase-10-evaluation-mia/README.md)
