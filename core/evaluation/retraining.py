"""Full-retraining baseline (Phase 11, Dashboard Spec Ch.24).

The gold-standard answer to "what would the model look like if the
target client had never participated": run the same FedAvg protocol
from scratch on every client *except* the target, then score the
result with exactly the same metrics used for the original and
unlearned models.

    ORIGINAL --- GA + KD ------------> UNLEARNED MODEL  --.
        \\                                                  >-- COMPARISON
         '-- retrain w/o target client -> RETRAINED MODEL -'

This is a **separate run** from the unlearning pipeline. Its weights
and results are written to their own files
(``retrained_model.pt`` / ``retraining_results.json``) and never touch
the original experiment's ``fl_history.json``/``global_model.pt``.
It is also the expensive one -- roughly as costly as the original
training -- so it is normally run offline / on demand, and the
dashboard reads back the stored result (Ch.37).

The protocol is matched to the original run on purpose (same model,
rounds, local epochs, seed, lr, batch size), so the *only* difference
between the two training runs is the missing client.
"""
from __future__ import annotations

import time

from core.datasets.base import get_dataset, load_manifest
from core.evaluation.evaluation_engine import evaluate_model_state
from core.evaluation.storage import (
    load_evaluation_results,
    save_retrained_checkpoint,
    save_retraining_results,
)
from core.federated.server import fedavg_train
from core.federated.storage import load_fl_history
from core.partitioning.storage import load_partition
from core.unlearning.storage import load_unlearning_status

#: Optimizer defaults core.federated.cli applies when the caller doesn't
#: override them. Histories written before Phase 11 didn't record lr /
#: batch_size, and the training API never overrides them, so these are
#: what those runs actually used.
LEGACY_LR = 0.01
LEGACY_BATCH_SIZE = 32


def run_retraining_baseline(experiment_id: str, device: str = "cpu") -> dict:
    """Retrain from scratch without the unlearning target, evaluate, persist.

    Requires the experiment to have been partitioned, trained (Phase 05),
    unlearned (Phase 08+09) and evaluated (Phase 10): the target client
    comes from the completed unlearning run, and the MIA non-member set
    size comes from the stored evaluation, so the retrained model is
    scored on the identical basis as the other two models.

    Raises FileNotFoundError if a prerequisite artifact is missing, or
    ValueError if unlearning hasn't completed or retraining is impossible
    (e.g. the target is the only client).
    """
    status = load_unlearning_status(experiment_id)
    if status.get("status") != "complete":
        raise ValueError(
            f"Unlearning has not completed for experiment '{experiment_id}' "
            f"(status: {status.get('status')!r}) -- run start_unlearning first"
        )
    evaluation = load_evaluation_results(experiment_id)  # FileNotFoundError if not evaluated
    history = load_fl_history(experiment_id)
    partition = load_partition(experiment_id)

    target_client_id = status["target_client_id"]
    if evaluation.get("target_client_id") != target_client_id:
        raise ValueError(
            f"Stored evaluation is for client {evaluation.get('target_client_id')} but the "
            f"latest unlearning run targeted client {target_client_id} -- re-run evaluation first"
        )

    clients = partition["clients"]
    target_client = next(c for c in clients if c["client_id"] == target_client_id)
    retained_clients = [c for c in clients if c["client_id"] != target_client_id]
    if not retained_clients:
        raise ValueError("Cannot retrain without the target client: it is the only client")

    # Same partition minus the target client. Client ids are kept as-is so
    # results stay comparable client-for-client with the other two models.
    reduced_partition = {
        **partition,
        "num_clients": len(retained_clients),
        "clients": retained_clients,
    }

    model_id = history["model"]
    rounds = history["rounds"]
    local_epochs = history["local_epochs"]
    seed = history["seed"]
    lr = history.get("lr", LEGACY_LR)
    batch_size = history.get("batch_size", LEGACY_BATCH_SIZE)

    # -- The retraining run itself (this is the number the runtime chart uses) --
    started_at = time.time()
    retrain_history, retrained_state = fedavg_train(
        experiment_id=experiment_id,
        partition=reduced_partition,
        model_id=model_id,
        rounds=rounds,
        local_epochs=local_epochs,
        seed=seed,
        lr=lr,
        batch_size=batch_size,
        device=device,
    )
    retraining_seconds = time.time() - started_at

    meta = load_manifest()[partition["dataset"]]
    channels, num_classes = meta["channels"], meta["num_classes"]
    save_retrained_checkpoint(
        experiment_id,
        state_dict=retrained_state,
        model_id=model_id,
        channels=channels,
        num_classes=num_classes,
    )

    # -- Score it exactly like the original / unlearned models --------------
    dataset = get_dataset(partition["dataset"])
    train_data = dataset.get_train()
    test_data = dataset.get_test()
    non_member_count = evaluation["after"]["mia_detail"]["non_member_count"]
    non_member_indices = list(range(min(non_member_count, len(test_data))))

    metrics = evaluate_model_state(
        retrained_state,
        model_id,
        channels,
        num_classes,
        train_data,
        test_data,
        target_client,
        retained_clients,
        non_member_indices,
        device=device,
    )

    original_training_seconds = sum(r["duration_seconds"] for r in history["round_history"])

    results = {
        "experiment_id": experiment_id,
        "run_kind": "separate_retraining_baseline",
        "target_client_id": target_client_id,
        "excluded_client_ids": [target_client_id],
        "model": model_id,
        "dataset": partition["dataset"],
        "num_clients_trained": len(retained_clients),
        "protocol": {
            "rounds": rounds,
            "local_epochs": local_epochs,
            "seed": seed,
            "lr": lr,
            "batch_size": batch_size,
            "hyperparameters_recorded": "lr" in history and "batch_size" in history,
        },
        "metrics": metrics,
        "runtime": {
            "retraining_seconds": retraining_seconds,
            "original_training_seconds": original_training_seconds,
        },
        "round_history": [
            {
                "round": r["round"],
                "accuracy": r["accuracy"],
                "loss": r["loss"],
                "duration_seconds": r["duration_seconds"],
            }
            for r in retrain_history["round_history"]
        ],
        "status": "complete",
    }
    save_retraining_results(experiment_id, results)
    return results
