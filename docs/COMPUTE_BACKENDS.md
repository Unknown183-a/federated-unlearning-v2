# Compute Backends (Phase 14)

One interface (`core/compute/base.py::ComputeBackend`), four backends, one fallback chain.

| Kind | Class | Needs | Can run new work? |
|------|-------|-------|-------------------|
| `college_gpu` | `RemoteHttpBackend` | `COLLEGE_GPU_BASE_URL` (+ optional `COLLEGE_GPU_API_KEY`) | yes |
| `colab` | `RemoteHttpBackend` | `COLAB_BASE_URL` (+ optional `COLAB_API_KEY`) | yes |
| `local` | `LocalBackend` | nothing; auto-detects CUDA -> MPS -> CPU | yes |
| `demo` | `DemoBackend` | nothing | **no** (reads stored artifacts only) |

## Selecting a backend

The UI stores `compute_backend` (`auto` by default) and sends it as `backend` on the training, unlearning, and
evaluation POSTs. Omitting `backend` entirely preserves pre-Phase-14 behavior (in-process, no `core.compute` import).

* **Auto** walks `college_gpu -> colab -> local -> demo` and uses the first backend whose health check passes.
* **A pinned backend never falls back.** If it is unavailable the run fails with that backend's reason. Silently
  substituting a different machine than the one you chose would be worse than an error.

## Fallback is never silent

Every response from a run that used `backend` includes `backend_trace`: each backend tried, in order, with its
status/detail, ending with the one that served the request. The UI renders it (`BackendTraceNote`), and the
Overview panel shows what Auto would pick *before* you run anything.

Failure is handled at two points:
1. **Before the call** -- a backend failing its health check is skipped.
2. **During the call** -- a backend that passes its health check but raises `BackendUnavailableError` mid-request
   is skipped too; its trace entry is rewritten to `Failed mid-run: ...` and the next backend gets the same call.

`NotSupportedError` (Demo refusing to run new work) is **not** retried -- read-only is an answer, not an outage.

### Known limit

Failover happens per request, and a retried request restarts from the beginning on the next backend. A long
training run that dies at round 15 of 20 is re-run, not resumed; there is no checkpoint hand-off between backends.

## Remote wire protocol

JSON over HTTP `POST`, one path per method, `Authorization: Bearer <key>` only if a key is configured:
`/status`, `/load_experiment`, `/get_client_distribution`, `/get_fl_history`, `/start_unlearning`,
`/get_unlearning_status`, `/get_results`, `/run_federated_training`, `/run_evaluation`.
Bodies are `{"experiment_id": ..., ...kwargs}`. `/status` returns `{"available": bool, "detail": str, "device": str}`.
Default timeout is 2 seconds so an unreachable host can't stall the status panel.

## Security

* URLs and keys live only in server-side environment variables (see `.env.example`), read by name at call time in
  exactly one place (`remote_http_backend.py`) and never cached on an object.
* Errors report the exception **type**, never its message, so a key or URL echoed by an HTTP client can't reach a
  response. A test asserts the key never appears in a failure's `detail`.
* The browser only ever receives credential-free status JSON. Review result: no occurrence of the variable names,
  `Bearer`, or key material in `frontend/src` or the built bundle.
* Do not prefix these variables with `VITE_`; that would bundle them into the browser.

## Not covered

* Retraining-baseline execution (Phase 11) is not routed through compute backends; it still runs in-process.
* The two remote backends are tested against a real local HTTP server speaking the protocol above, not against an
  actual college or Colab machine; no such server ships in this repo.
