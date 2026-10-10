"""The backend-neutral compute API (Phase 14, Dashboard Spec Ch.71).

Every compute backend -- College GPU, Google Colab, Local (Mac/CPU/
CUDA/MPS), and the read-only Demo/Precomputed backend -- implements
this same seven-method contract. Nothing above this layer (the Express
routes, the React pages) is allowed to know which backend actually ran
a given experiment; a frontend switching backends changes nothing
about how results are displayed, because every backend hands back the
exact same artifact shapes this project has used since Phase 03.

The four concrete backends live in sibling modules:
    local_backend.py        -- in-process, calls core/* directly
    demo_backend.py          -- LocalBackend's read paths, no compute
    remote_http_backend.py   -- generic HTTP client, used for both
                                 College GPU and Google Colab (same
                                 wire protocol, different base URL)
and registry.py is what selects between them, including the Auto
fallback chain.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BackendUnavailableError(RuntimeError):
    """Raised when a backend cannot currently serve requests.

    Never carries a credential, API key, or raw exception text that
    might -- for a remote backend -- leak into a client-visible error
    message; see each backend's _safe_detail()/detail construction.
    """


class NotSupportedError(RuntimeError):
    """Raised when a backend is reachable but doesn't support this
    operation -- e.g. the Demo backend can serve any already-stored
    experiment's artifacts but cannot run new unlearning."""


class ComputeBackend(ABC):
    kind: str  # "college_gpu" | "colab" | "local" | "demo"
    name: str  # human-readable label for the status panel

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Health check. Must never raise -- on any failure, return
        {"available": False, "detail": <safe, credential-free reason>}
        rather than letting an exception propagate, since the status
        panel polls every backend and one bad backend must not break
        the others' results.

        Returns (at minimum):
            {
              "backend": self.kind,
              "name": self.name,
              "available": bool,
              "detail": str,          # human-readable, no secrets
              "device": str | None,   # e.g. "cuda", "mps", "cpu" -- local/demo only
              "latency_ms": float | None,
            }
        """

    @abstractmethod
    def load_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Basic experiment metadata (dataset, model, rounds, seed) --
        not the full artifact, just enough to confirm the experiment
        exists and show what it is."""

    @abstractmethod
    def get_client_distribution(self, experiment_id: str) -> dict[str, Any]:
        """The per-client partition: sample counts and class
        distribution for every federated client (Phase 03/04)."""

    @abstractmethod
    def get_fl_history(self, experiment_id: str) -> dict[str, Any]:
        """The round-by-round FedAvg training history (Phase 05)."""

    @abstractmethod
    def start_unlearning(self, experiment_id: str, client_id: int, **kwargs: Any) -> dict[str, Any]:
        """Run Gradient Ascent + Knowledge Distillation against
        `client_id` (Phase 08+09). Raises NotSupportedError on a
        read-only backend (Demo)."""

    @abstractmethod
    def get_unlearning_status(self, experiment_id: str) -> dict[str, Any]:
        """The most recently persisted unlearning run's status."""

    @abstractmethod
    def get_results(self, experiment_id: str) -> dict[str, Any]:
        """The Phase 10 evaluation results (before/after metrics)."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<{type(self).__name__} kind={self.kind!r}>"
