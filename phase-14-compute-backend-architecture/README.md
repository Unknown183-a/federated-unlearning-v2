# Phase 14 — Backend Service Layer & Compute Backend Architecture

> Status: **Complete**
> Implementation: `core/compute/` (one interface, four backends, Auto fallback), the status route, the selector panel, and the security review are live on main. See [`docs/COMPUTE_BACKENDS.md`](../docs/COMPUTE_BACKENDS.md).

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

- [x] Finalize the backend-neutral API contract
- [x] Implement the College GPU backend
- [x] Implement the Google Colab backend
- [x] Implement the Local Mac backend with CUDA/MPS/CPU auto-detection
- [x] Implement the Demo/Precomputed backend
- [x] Build the Compute Backend selector + status panel UI
- [x] Implement Auto mode with the College GPU → Colab → Local → Demo priority chain
- [x] Implement failure detection + fallback messaging (never silent)
- [x] Security review: confirm no credentials ever reach the frontend

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
| — | `core/compute/base.py` defines the seven-method `ComputeBackend` contract from the plan plus `BackendUnavailableError` / `NotSupportedError`. `LocalBackend` calls the same `core.*` functions the per-phase CLIs already call (not a reimplementation) and auto-detects CUDA → MPS → CPU; `DemoBackend` inherits its read paths and refuses writes. College GPU and Colab are the *same* class, `RemoteHttpBackend`, configured by different env-var names, over a documented JSON-over-HTTP protocol using stdlib `urllib` (no new dependency). I also added `run_federated_training` / `run_evaluation` to the backends, which go beyond the seven-method contract, because a backend-neutral layer that can only run unlearning but not the training before it would be half an abstraction. `registry.py` holds the fallback order (college_gpu → colab → local → demo), probes all backends concurrently for the status panel so one dead host costs one timeout, not four, and `call_with_fallback()` for execution. **Pinned backends never fall back** (an explicit choice fails loudly); only Auto does. First draft only checked health *before* a call, which would not satisfy "killing the primary mid-run triggers a visible fallback"; `call_with_fallback` now also catches `BackendUnavailableError` raised *during* the call, rewrites that trace entry to `Failed mid-run`, and hands the same call to the next backend. `NotSupportedError` is deliberately never retried. **Known limit, stated plainly:** failover is per request and restarts from the beginning — there is no checkpoint hand-off, so a run that dies at round 15/20 is re-run, not resumed. The three CLIs (federated/unlearning/evaluation) gained an optional `--backend`; omitted, the code path is unchanged and never imports `core.compute`. With it, output gains `backend_trace`. Express: `GET /api/compute/status`, and training/unlearning/evaluation routes forward an optional `backend` field. Frontend: `compute_backend` in the central config (preserved across `loadExperiment`), `ComputeBackendPanel` on Overview (selector + live status + what Auto would pick and why it skipped the others), and `BackendTraceNote` on the three action pages so a fallback is shown after the run too. **Security review, actually run:** grepping `frontend/src`, `backend/src`, and the built bundle for the env-var names, `Bearer`, and key material found nothing except one explanatory comment; the variables are read in exactly one place (`remote_http_backend.py`); errors carry the exception *type* only, and a test asserts a configured key never appears in a failure detail; `.env` is gitignored and `.env.example` documents the names and warns against a `VITE_` prefix. **Verified:** 38 new tests in `tests/test_compute.py` (remote backend exercised over a real local HTTP server for status, bearer header presence/absence, payload forwarding, unreachable host, and key non-leak; Auto resolution; pinned no-fallback; mid-call death failing over; CLI dispatch); full suite `pytest -m "not slow"` 105 passed; `npm run build` clean; the live Express server was curled for: Demo refusing unlearning, pinned unconfigured College GPU failing with its own reason (no fallback), Auto falling through to Local, and the no-`backend` legacy path unchanged. **Not verified / not done:** no real college or Colab machine exists in this repo, so the remote backends are proven against a protocol-speaking local server only; retraining-baseline execution (Phase 11) is not routed through backends; the React panel was built and type-checked by the bundler but not exercised in a browser. |

---
Previous: [Phase 13 — Dashboard UX — Navigation, State & Visual Design System](../phase-13-dashboard-ux/README.md)
Next: [Phase 15 — Error Handling, Reproducibility, Professor Demo Mode & Launch](../phase-15-polish-launch/README.md)
