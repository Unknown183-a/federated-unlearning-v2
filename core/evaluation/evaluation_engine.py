"""Orchestrates Phase 10 evaluation.

All five Page 7 metrics (Ch.21-22) -- global accuracy, forget-client
accuracy, retained-client accuracy, MIA, and runtime -- computed once
against the pre-unlearning checkpoint ("before") and once against the
final unlearned checkpoint ("after"). Exposes the single conceptual
``evaluate_model(...)`` entry point from the Dashboard Spec (Ch.36) as
``evaluate_experiment(experiment_id)``, matching the "Evaluation
Engine" box in the Ch.35 backend service diagram.

Requires that this experiment has already been through Phase 05
(trained, checkpoint saved) and Phase 08+09 (``start_unlearning``
complete, final checkpoint + status saved) -- Phase 10 Depends On
Phase 09.
"""
from __future__ import annotations

import time

from core.datasets.base import get_dataset
from core.evaluation.accuracy import (
    evaluate_client_accuracy,
    evaluate_global_accuracy,
    evaluate_retained_accuracy,
)
from core.evaluation.mia import run_membership_inference
from core.evaluation.storage import save_evaluation_results
from core.federated.storage import load_model_checkpoint
from core.partitioning.storage import load_partition
from core.unlearning.storage import load_final_checkpoint, load_unlearning_status

#: How many held-out test samples to use as the MIA's non-member set.
#: Capped against however much test data actually exists (see
#: `evaluate_experiment`) so this never over-requests on a small split.
DEFAULT_NON_MEMBER_SAMPLE_SIZE = 200


def evaluate_experiment(
    experiment_id: str,
    non_member_sample_size: int = DEFAULT_NON_MEMBER_SAMPLE_SIZE,
    device: str = "cpu",
) -> dict:
    """Compute and persist the full before/after evaluation for one
    experiment's completed unlearning run.

    Raises FileNotFoundError if the experiment hasn't been partitioned/
    trained/unlearned yet, or ValueError if unlearning didn't finish
    successfully.
    """
    started_at = time.time()

    status = load_unlearning_status(experiment_id)
    if status.get("status") != "complete":
        raise ValueError(
            f"Unlearning has not completed for experiment '{experiment_id}' "
            f"(status: {status.get('status')!r}) -- run start_unlearning first"
        )

    partition = load_partition(experiment_id)
    before_checkpoint = load_model_checkpoint(experiment_id)
    after_checkpoint = load_final_checkpoint(experiment_id)

    model_id = before_checkpoint["model_id"]
    channels = before_checkpoint["channels"]
    num_classes = before_checkpoint["num_classes"]

    clients = partition["clients"]
    target_client_id = status["target_client_id"]
    target_client = next(c for c in clients if c["client_id"] == target_client_id)
    retained_clients = [c for c in clients if c["client_id"] != target_client_id]

    dataset = get_dataset(partition["dataset"])
    train_data = dataset.get_train()
    test_data = dataset.get_test()

    # Non-member sample for MIA: a slice of the held-out test split --
    # data the model was never trained on at all -- capped to however
    # much test data actually exists.
    non_member_indices = list(range(min(non_member_sample_size, len(test_data))))

    results: dict = {
        "experiment_id": experiment_id,
        "target_client_id": target_client_id,
        "model": model_id,
        "dataset": partition["dataset"],
    }

    for label, checkpoint in (("before", before_checkpoint), ("after", after_checkpoint)):
        state = checkpoint["state_dict"]

        global_accuracy = evaluate_global_accuracy(
            state, model_id, channels, num_classes, test_data, device=device
        )
        forget_client_accuracy = evaluate_client_accuracy(
            state, model_id, channels, num_classes, train_data, target_client["indices"], device=device
        )
        retained = evaluate_retained_accuracy(
            state, model_id, channels, num_classes, train_data, retained_clients, device=device
        )
        mia = run_membership_inference(
            state,
            model_id,
            channels,
            num_classes,
            train_data,
            target_client["indices"],
            test_data,
            non_member_indices,
            device=device,
        )

        results[label] = {
            "global_accuracy": global_accuracy,
            "forget_client_accuracy": forget_client_accuracy,
            "retained_client_accuracy": retained["mean"],
            "retained_client_accuracy_per_client": retained["per_client"],
            "mia_success": mia["attack_accuracy"],
            "mia_detail": mia,
        }

    ga_summary = status.get("gradient_ascent") or {}
    kd_summary = status.get("knowledge_distillation") or {}
    results["runtime"] = {
        "gradient_ascent_seconds": ga_summary.get("duration_seconds"),
        "knowledge_distillation_seconds": kd_summary.get("duration_seconds"),
        "total_unlearning_seconds": status.get("duration_seconds"),
        "evaluation_seconds": time.time() - started_at,
    }
    results["status"] = "complete"

    save_evaluation_results(experiment_id, results)
    return results
