# Phase 13 — Dashboard UX — Navigation, State & Visual Design System

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

## Goal

Tie all 9 pages together into one coherent app with a persistent stepper, shared state, and the full visual design system.

## In Scope

- Global navigation stepper across all 9 pages
- Central experiment state management
- Visual design system: pipeline mini-map, consistent color code, target-client highlighting
- Accessibility pass (text-equivalents for charts, keyboard navigation, color contrast)

## Out of Scope

- Backend/compute architecture (Phase 14)

## Tasks

- [ ] Build the persistent navigation stepper reflecting the 9-page order
- [ ] Consolidate all page state into one central store
- [ ] Build the persistent pipeline mini-map component
- [ ] Apply a consistent color code for dataset/client/server/model across all pages
- [ ] Accessibility pass: alt text/summaries for every chart, keyboard nav, contrast check

## Deliverables

- Fully navigable 9-page app with one shared state model

## Depends On

Phase 12 (quick demo + model library)

## Acceptance Criteria

- Navigating back and forth between pages never loses or recomputes state
- Every chart has a text-equivalent summary

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |

---
Previous: [Phase 12 — Quick Unlearning Demo & Model Library](../phase-12-quick-demo-model-library/README.md)
Next: [Phase 14 — Backend Service Layer & Compute Backend Architecture](../phase-14-compute-backend-architecture/README.md)
