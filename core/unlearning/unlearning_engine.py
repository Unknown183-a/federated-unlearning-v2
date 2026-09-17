"""Orchestrates the unlearning pipeline (Phase 08 + Phase 09).

Exposes the two conceptual ComputeBackend operations from the
Dashboard Spec (Ch.71.8):

    start_unlearning(client_id)
    get_unlearning_status()

`start_unlearning` runs both stages of the pipeline in sequence:

    1. Gradient Ascent (Phase 08)   -- forget the target client
    2. Knowledge Distillation (Phase 09) -- repair collateral damage
       on every other ("retained") client, using the pre-ascent
       global model as the teacher

and persists the resulting status (and both stages' weights) so a
later `get_unlearning_status` call can pick the full result back up
without re-running anything. Evaluation/MIA (Phase 10) is out of
scope here -- this pipeline stops once the final unlearned model is
saved.
"""
from __future__ import annotations

import time

from core.datasets.base import get_dataset
from core.federated.storage import load_fl_history, load_model_checkpoint
from core.partitioning.storage import load_partition
from core.unlearning.gradient_ascent import run_gradient_ascent
from core.unlearning.knowledge_distillation import run_knowledge_distillation
from core.unlearning.storage import (
    load_unlearning_status,
    save_final_checkpoint,
    save_ga_checkpoint,
    save_unlearning_status,
)


def start_unlearning(
    experiment_id: str,
    client_id: int,
    steps: int = 30,
    lr: float = 0.01,
    batch_size: int = 32,
    kd_epochs: int = 5,
    kd_lr: float = 0.01,
    kd_temperature: float = 4.0,
    kd_alpha: float = 0.5,
    kd_batch_size: int = 64,
    device: str = "cpu",
) -> dict:
    """Run the full Gradient Ascent -> Knowledge Distillation pipeline
    against `client_id`'s local data.

    Requires that this experiment has already been through Phase 03
    (partitioned) and Phase 05 (trained, with a saved checkpoint).
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
    retained_clients = [c for c in clients if c["client_id"] != client_id]

    dataset = get_dataset(partition["dataset"]).get_train()

    # The pre-ascent global model is Knowledge Distillation's teacher
    # (Phase 09's goal): capture it now, before Gradient Ascent
    # overwrites the working weights below.
    pretrained_state = checkpoint["state_dict"]

    status = {
        "experiment_id": experiment_id,
        "target_client_id": client_id,
        "model": history["model"],
        "dataset": history["dataset"],
        "stage": "gradient_ascent",
        "status": "running",
    }
    save_unlearning_status(experiment_id, status)

    # -- Stage 1: Gradient Ascent (Phase 08) --------------------------
    ga_started_at = time.time()
    try:
        ga_result = run_gradient_ascent(
            global_state=pretrained_state,
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
        state_dict=ga_result["final_state_dict"],
        model_id=checkpoint["model_id"],
        channels=checkpoint["channels"],
        num_classes=checkpoint["num_classes"],
    )

    gradient_ascent_summary = {
        "status": "complete",
        "steps_completed": ga_result["steps_completed"],
        "steps_requested": ga_result["steps_requested"],
        "stopped_early": ga_result["stopped_early"],
        "initial_loss": ga_result["initial_loss"],
        "initial_accuracy": ga_result["initial_accuracy"],
        "final_loss": ga_result["final_loss"],
        "final_accuracy": ga_result["final_accuracy"],
        "step_history": ga_result["step_history"],
        "duration_seconds": time.time() - ga_started_at,
    }

    status = {
        **status,
        "stage": "knowledge_distillation",
        "gradient_ascent": gradient_ascent_summary,
    }
    save_unlearning_status(experiment_id, status)

    # -- Stage 2: Knowledge Distillation (Phase 09) -------------------
    kd_started_at = time.time()
    try:
        kd_result = run_knowledge_distillation(
            teacher_state=pretrained_state,
            student_state=ga_result["final_state_dict"],
            model_id=checkpoint["model_id"],
            channels=checkpoint["channels"],
            num_classes=checkpoint["num_classes"],
            dataset=dataset,
            retained_clients=retained_clients,
            epochs=kd_epochs,
            lr=kd_lr,
            temperature=kd_temperature,
            alpha=kd_alpha,
            batch_size=kd_batch_size,
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

    save_final_checkpoint(
        experiment_id,
        state_dict=kd_result["final_state_dict"],
        model_id=checkpoint["model_id"],
        channels=checkpoint["channels"],
        num_classes=checkpoint["num_classes"],
    )

    knowledge_distillation_summary = {
        "status": "complete",
        "epochs_completed": kd_result["epochs_completed"],
        "epochs_requested": kd_result["epochs_requested"],
        "temperature": kd_result["temperature"],
        "alpha": kd_result["alpha"],
        "initial_retained_accuracy": kd_result["initial_retained_accuracy"],
        "final_retained_accuracy": kd_result["final_retained_accuracy"],
        "per_client_accuracy_before": kd_result["per_client_accuracy_before"],
        "per_client_accuracy_after": kd_result["per_client_accuracy_after"],
        "epoch_history": kd_result["epoch_history"],
        "duration_seconds": time.time() - kd_started_at,
    }

    status = {
        **status,
        "status": "complete",
        "knowledge_distillation": knowledge_distillation_summary,
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
