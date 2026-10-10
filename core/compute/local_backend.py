"""Local Mac / CPU / CUDA backend (Phase 14).

Runs every operation in-process by calling the exact same functions
the existing per-phase CLIs already call (core.federated.server,
core.unlearning.unlearning_engine, core.evaluation.evaluation_engine)
-- this backend is not a reimplementation, it's the same code behind
the shared interface. A run routed through LocalBackend therefore
produces byte-for-byte the same artifacts as calling those functions
directly, which is what every existing Express route has done since
Phase 05.

Device auto-detection (CUDA -> MPS -> CPU) happens once per process,
matching the "Local Mac backend with CUDA/MPS/CPU auto-detection" task
-- this project runs on both CUDA Linux boxes and Apple Silicon.
"""
from __future__ import annotations

import time
from typing import Any

from core.compute.base import ComputeBackend
from core.evaluation.evaluation_engine import DEFAULT_NON_MEMBER_SAMPLE_SIZE, evaluate_experiment
from core.evaluation.storage import load_evaluation_results
from core.federated.server import run_federated_training as _run_federated_training
from core.federated.storage import load_fl_history
from core.partitioning.storage import load_partition
from core.unlearning.storage import load_unlearning_status
from core.unlearning.unlearning_engine import start_unlearning as _start_unlearning


def detect_device() -> str:
    """CUDA -> MPS -> CPU, in that order. Imports torch lazily so that
    nothing that only needs backend *status* (e.g. the Demo backend,
    or a quick health check) pays torch's import cost."""
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class LocalBackend(ComputeBackend):
    kind = "local"
    name = "Local (Mac / CPU / CUDA)"

    def get_status(self) -> dict[str, Any]:
        started = time.monotonic()
        try:
            device = detect_device()
            detail = f"Running in-process on this machine ({device})."
            available = True
        except Exception as exc:  # pragma: no cover - torch import failures etc.
            device = None
            detail = f"Local device detection failed: {exc}"
            available = False
        return {
            "backend": self.kind,
            "name": self.name,
            "available": available,
            "detail": detail,
            "device": device,
            "latency_ms": (time.monotonic() - started) * 1000,
        }

    def load_experiment(self, experiment_id: str) -> dict[str, Any]:
        history = load_fl_history(experiment_id)
        return {
            "experiment_id": experiment_id,
            "dataset": history["dataset"],
            "model": history["model"],
            "num_clients": history["num_clients"],
            "rounds": history["rounds"],
            "seed": history["seed"],
        }

    def get_client_distribution(self, experiment_id: str) -> dict[str, Any]:
        return load_partition(experiment_id)

    def get_fl_history(self, experiment_id: str) -> dict[str, Any]:
        return load_fl_history(experiment_id)

    def start_unlearning(self, experiment_id: str, client_id: int, **kwargs: Any) -> dict[str, Any]:
        return _start_unlearning(experiment_id=experiment_id, client_id=client_id, **kwargs)

    def get_unlearning_status(self, experiment_id: str) -> dict[str, Any]:
        return load_unlearning_status(experiment_id)

    def get_results(self, experiment_id: str) -> dict[str, Any]:
        return load_evaluation_results(experiment_id)

    # Not part of the shared ComputeBackend contract (evaluation and
    # retraining aren't in the Dashboard Spec's Ch.71 list, which predates
    # those phases) but every backend that can start_unlearning should be
    # able to run the rest of the pipeline too, so these are exposed the
    # same way for Local -- RemoteHttpBackend mirrors this below.
    def run_federated_training(self, experiment_id: str, **kwargs: Any) -> dict[str, Any]:
        partition = load_partition(experiment_id)
        return _run_federated_training(experiment_id=experiment_id, partition=partition, **kwargs)

    def run_evaluation(self, experiment_id: str, non_member_sample_size: int = DEFAULT_NON_MEMBER_SAMPLE_SIZE, **kwargs: Any) -> dict[str, Any]:
        return evaluate_experiment(experiment_id=experiment_id, non_member_sample_size=non_member_sample_size, **kwargs)
