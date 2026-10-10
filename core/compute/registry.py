"""Compute backend registry + Auto fallback chain (Phase 14).

    status = all_statuses()                  # for the status panel
    backend, trace = resolve_auto_backend()  # College GPU -> Colab -> Local -> Demo
    backend = get_backend("local")           # an explicit, user-pinned choice

Auto mode tries each backend in FALLBACK_ORDER and uses the first one
whose get_status() reports available -- Local and Demo always report
available (no network, no credentials needed), so Auto always resolves
to *something*; it degrades to Demo only if even Local's device
detection somehow fails. Every attempt, successful or not, is recorded
in the trace returned alongside the chosen backend, so a fallback is
always visible in the API response and never silent (Ch.71 /
acceptance criteria) -- the frontend's status panel renders this trace
directly rather than only showing the final choice.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from core.compute.base import BackendUnavailableError, ComputeBackend
from core.compute.demo_backend import DemoBackend
from core.compute.local_backend import LocalBackend
from core.compute.remote_http_backend import RemoteHttpBackend

# Priority order for Auto mode (Dashboard Spec: College GPU -> Colab -> Local -> Demo).
FALLBACK_ORDER = ["college_gpu", "colab", "local", "demo"]

_FACTORIES = {
    "college_gpu": lambda: RemoteHttpBackend(
        kind="college_gpu",
        name="College GPU",
        base_url_env="COLLEGE_GPU_BASE_URL",
        api_key_env="COLLEGE_GPU_API_KEY",
    ),
    "colab": lambda: RemoteHttpBackend(
        kind="colab",
        name="Google Colab",
        base_url_env="COLAB_BASE_URL",
        api_key_env="COLAB_API_KEY",
    ),
    "local": lambda: LocalBackend(),
    "demo": lambda: DemoBackend(),
}


def get_backend(kind: str) -> ComputeBackend:
    try:
        return _FACTORIES[kind]()
    except KeyError:
        raise ValueError(f"Unknown compute backend '{kind}' (expected one of {FALLBACK_ORDER})") from None


def all_statuses() -> list[dict[str, Any]]:
    """Status of every backend, in FALLBACK_ORDER, for the status
    panel. Probed concurrently so an unreachable remote backend's
    timeout doesn't multiply the panel's total load time -- worst case
    is one timeout, not the sum of all of them."""
    with ThreadPoolExecutor(max_workers=len(FALLBACK_ORDER)) as pool:
        results = list(pool.map(lambda kind: get_backend(kind).get_status(), FALLBACK_ORDER))
    return results


def resolve_auto_backend() -> tuple[ComputeBackend, list[dict[str, Any]]]:
    """Walk FALLBACK_ORDER, stopping at the first available backend.
    Returns that backend plus the status of every backend tried up to
    and including it (not the ones after -- once a backend is picked,
    there's nothing useful to report by also probing the rest)."""
    trace: list[dict[str, Any]] = []
    for kind in FALLBACK_ORDER:
        backend = get_backend(kind)
        status = backend.get_status()
        trace.append(status)
        if status.get("available"):
            return backend, trace
    # Demo is last in FALLBACK_ORDER and always reports available, so
    # this is unreachable in practice -- kept as a clear failure rather
    # than a silent None if that assumption is ever broken.
    raise RuntimeError("No compute backend is available, including Demo -- this should never happen.")


def resolve_requested_backend(kind: str | None) -> tuple[ComputeBackend, list[dict[str, Any]]]:
    """What every CLI's optional --backend flag resolves through.

    kind=None or "auto" -> Auto fallback chain (see resolve_auto_backend).
    A specific kind -> that exact backend, *not* falling back on
    failure -- an explicit choice should fail loudly and specifically
    rather than silently degrading to a different backend the caller
    didn't ask for; only Auto mode falls back.
    """
    if kind is None or kind == "auto":
        return resolve_auto_backend()

    backend = get_backend(kind)
    status = backend.get_status()
    return backend, [status]


def call_with_fallback(kind: str | None, method: str, **kwargs: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Run `method` on the requested backend, returning (result, trace).

    Auto (kind None/"auto"): walk FALLBACK_ORDER. A backend that
    reports unavailable up front is skipped, and one that *becomes*
    unavailable during the call (BackendUnavailableError -- e.g. the
    GPU box dies mid-request) is also skipped, with the trace entry
    rewritten to say it failed mid-run, then the next backend gets the
    same call. NotSupportedError is never retried: it means "this
    backend is up but read-only" (Demo), which is the caller's answer,
    not an outage.

    A pinned kind never falls back: if it's unavailable the call raises
    BackendUnavailableError and the caller sees exactly that.
    """
    if kind is not None and kind != "auto":
        backend = get_backend(kind)
        status = backend.get_status()
        return getattr(backend, method)(**kwargs), [status]

    trace: list[dict[str, Any]] = []
    for candidate in FALLBACK_ORDER:
        backend = get_backend(candidate)
        status = backend.get_status()
        trace.append(status)
        if not status.get("available"):
            continue
        try:
            return getattr(backend, method)(**kwargs), trace
        except BackendUnavailableError as exc:
            trace[-1] = {**status, "available": False, "detail": f"Failed mid-run: {exc}"}
    raise BackendUnavailableError("No compute backend could complete the request.")
