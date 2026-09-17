# Phase 14 — Backend Service Layer & Compute Backend Architecture

> Status: **Not Started**
> Implementation: not started at this time — this folder currently holds only the plan.

## Goal

Formalize the backend-neutral API and implement the four compute backends with fallback, status, and security guarantees.

## In Scope

- Backend-neutral API layer (get_status, load_experiment, get_client_distribution, get_fl_history, start_unlearning, get_unlearning_status, get_results)
- College GPU backend
- Google Colab backend
- Local Mac (MPS/CPU) backend
- Demo/Precomputed backend
- Compute Backend selector UI + status panel
- Automatic fallback chain + failure messaging
- Security review (no credentials in frontend)

## Out of Scope

- New ML algorithms — this phase is infrastructure only

## Tasks

- [ ] Finalize the backend-neutral API contract
- [ ] Implement the College GPU backend
- [ ] Implement the Google Colab backend
- [ ] Implement the Local Mac backend with CUDA/MPS/CPU auto-detection
- [ ] Implement the Demo/Precomputed backend
- [ ] Build the Compute Backend selector + status panel UI
- [ ] Implement Auto mode with the College GPU → Colab → Local → Demo priority chain
- [ ] Implement failure detection + fallback messaging (never silent)
- [ ] Security review: confirm no credentials ever reach the frontend

## Deliverables

- All 4 backends working behind one interface
- Compute status panel
- Documented fallback behavior

## Depends On

Phase 13 (dashboard UX)

## Acceptance Criteria

- Switching backends changes nothing in the visualization layer
- Killing the primary backend mid-run triggers a visible, correct fallback
- No credential ever appears in frontend source or network requests

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |

---
Previous: [Phase 13 — Dashboard UX — Navigation, State & Visual Design System](../phase-13-dashboard-ux/README.md)
Next: [Phase 15 — Error Handling, Reproducibility, Professor Demo Mode & Launch](../phase-15-polish-launch/README.md)
