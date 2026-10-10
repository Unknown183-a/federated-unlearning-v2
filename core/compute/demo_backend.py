"""Demo / Precomputed backend (Phase 14).

Serves whatever experiments already have artifacts on disk -- no
compute, no GPU, no network, so it's always available and always the
last link in the Auto fallback chain. It shares LocalBackend's read
paths (same storage modules, same artifact shapes) rather than
duplicating them, and overrides only the write operation to refuse it
clearly: a professor running the demo on a laptop with no GPU and no
internet should get a working, if limited, dashboard, not a crash --
but it must never pretend to run new unlearning it didn't actually run.
"""
from __future__ import annotations

import time
from typing import Any

from core.compute.base import NotSupportedError
from core.compute.local_backend import LocalBackend


class DemoBackend(LocalBackend):
    kind = "demo"
    name = "Demo (Precomputed)"

    def get_status(self) -> dict[str, Any]:
        started = time.monotonic()
        return {
            "backend": self.kind,
            "name": self.name,
            "available": True,  # reading JSON off disk never fails to "be available"
            "detail": "Serves already-stored experiment artifacts only; cannot run new unlearning.",
            "device": None,
            "latency_ms": (time.monotonic() - started) * 1000,
        }

    def start_unlearning(self, experiment_id: str, client_id: int, **kwargs: Any) -> dict[str, Any]:
        raise NotSupportedError(
            "The Demo backend serves precomputed experiments only -- switch to Local or a "
            "configured GPU backend to run new unlearning."
        )

    def run_federated_training(self, experiment_id: str, **kwargs: Any) -> dict[str, Any]:
        raise NotSupportedError(
            "The Demo backend serves precomputed experiments only -- switch to Local or a "
            "configured GPU backend to run new training."
        )

    def run_evaluation(self, experiment_id: str, **kwargs: Any) -> dict[str, Any]:
        raise NotSupportedError(
            "The Demo backend serves precomputed experiments only -- switch to Local or a "
            "configured GPU backend to run new evaluation."
        )
