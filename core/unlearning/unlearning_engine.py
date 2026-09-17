"""Orchestrates the unlearning pipeline (Phase 08: Gradient Ascent only).

Exposes the two conceptual ComputeBackend operations from the
Dashboard Spec (Ch.71.8) that this phase is responsible for:

    start_unlearning(client_id)
    get_unlearning_status()

Knowledge Distillation (Phase 09) will extend `start_unlearning` to
run a second stage after this one; for now the pipeline stops after
Gradient Ascent, matching Phase 08's "stage 1 only" scope.
"""
from __future__ import annotations

import time

from core.datasets.base import get_dataset
from core.federated.storage import load_fl_history, load_model_checkpoint
from core.partitioning.storage import load_partition
from core.unlearning.gradient_ascent import run_gradient_ascent
from core.unlearning.storage import (
    load_unlearning_status,
    save_ga_checkpoint,
    save_unlearning_status,
)


def start_unlearning(
    experiment_id: str,
    client_id: int,
    steps: int = 30,
    lr: float = 0.01,
    batch_size: int = 32,
    device: str = "cpu",
) -> dict:
    """Run the Gradient Ascent stage against `client_id`'s local data.

    Requires that this experiment has already been through Phase 03
    (partitioned) and Phase 05 (trained, with a saved checkpoint).
    Persists the resulting status (and the ascent-stage weights) so a
    later `get_unlearning_status` call -- or Phase 09 -- can pick them
    back up without re-running anything.
    """
    started_at = time.time()

    history = load_fl_history(experiment_id)
    partition = load_partition(experiment_id)
    checkpoint = load_model_checkpoint(experiment_id)

    clients = partition["clients"]
    if not (0 <= client_id < len(clients)):
        raise ValueError(
            f"No client {client_id} in this experiment's partition "
            f"(num_clients={partition['num_clients']})"
        )
    target_indices = clients[client_id]["indices"]

    dataset = get_dataset(partition["dataset"]).get_train()

    status = {
        "experiment_id": experiment_id,
        "target_client_id": client_id,
        "stage": "gradient_ascent",
        "status": "running",
    }
    save_unlearning_status(experiment_id, status)

    try:
        result = run_gradient_ascent(
            global_state=checkpoint["state_dict"],
            model_id=checkpoint["model_id"],
            channels=checkpoint["channels"],
            num_classes=checkpoint["num_classes"],
            dataset=dataset,
            target_indices=target_indices,
            steps=steps,
            lr=lr,
            batch_size=batch_size,
            device=device,
        )
    except Exception as exc:
        status = {
            **status,
            "status": "failed",
            "error": str(exc),
            "duration_seconds": time.time() - started_at,
        }
        save_unlearning_status(experiment_id, status)
        raise

    save_ga_checkpoint(
        experiment_id,
        state_dict=result["final_state_dict"],
        model_id=checkpoint["model_id"],
        channels=checkpoint["channels"],
        num_classes=checkpoint["num_classes"],
    )

    status = {
        "experiment_id": experiment_id,
        "target_client_id": client_id,
        "stage": "gradient_ascent",
        "status": "complete",
        "model": history["model"],
        "dataset": history["dataset"],
        "steps_completed": result["steps_completed"],
        "steps_requested": result["steps_requested"],
        "stopped_early": result["stopped_early"],
        "initial_loss": result["initial_loss"],
        "initial_accuracy": result["initial_accuracy"],
        "final_loss": result["final_loss"],
        "final_accuracy": result["final_accuracy"],
        "step_history": result["step_history"],
        "duration_seconds": time.time() - started_at,
    }
    save_unlearning_status(experiment_id, status)
    return status


def get_unlearning_status(experiment_id: str) -> dict:
    """Return the most recently persisted unlearning status.

    Mirrors the conceptual `get_unlearning_status()` from Ch.71.8.
    Raises FileNotFoundError if `start_unlearning` hasn't been called
    yet for this experiment.
    """
    return load_unlearning_status(experiment_id)
