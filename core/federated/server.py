"""Federated learning server / aggregation loop (Phase 05).

Drives the FedAvg round loop: each round, every client trains locally
on its partition shard (client.py), the server aggregates their
updates (fedavg.py), and the new global model is evaluated on the
held-out test set. The per-round results are what Phase 06's charts
and progress UI consume, and what get_fl_history() returns.
"""
from __future__ import annotations

import copy
import time

import torch
from torch.utils.data import DataLoader

from core.datasets.base import get_dataset, load_manifest
from core.federated.client import local_train
from core.federated.fedavg import federated_average
from core.federated.model import build_model
from core.federated.storage import load_fl_history, save_fl_history


def _evaluate(model, test_loader, device: str) -> tuple[float, float]:
    """Return (accuracy, avg_loss) of `model` on `test_loader`."""
    model.eval()
    criterion = torch.nn.CrossEntropyLoss(reduction="sum")
    correct = 0
    total = 0
    total_loss = 0.0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            total_loss += criterion(outputs, labels).item()
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
    accuracy = correct / total if total else 0.0
    avg_loss = total_loss / total if total else 0.0
    return accuracy, avg_loss


def run_federated_training(
    experiment_id: str,
    partition: dict,
    model_id: str,
    rounds: int,
    local_epochs: int,
    seed: int,
    lr: float = 0.01,
    batch_size: int = 32,
    eval_batch_size: int = 256,
    device: str = "cpu",
) -> dict:
    """Run the full FedAvg loop for `rounds` rounds and persist the result.

    `partition` is a full partition dict from core.partitioning (with
    per-client sample indices), already computed for this experiment.
    Returns the same history dict that gets written to
    experiments/<experiment_id>/fl_history.json.
    """
    if rounds < 1:
        raise ValueError("rounds must be >= 1")

    dataset_id = partition["dataset"]
    manifest = load_manifest()
    meta = manifest[dataset_id]
    channels = meta["channels"]
    num_classes = meta["num_classes"]

    torch.manual_seed(seed)

    dataset = get_dataset(dataset_id)
    train_set = dataset.get_train()
    test_set = dataset.get_test()
    test_loader = DataLoader(test_set, batch_size=eval_batch_size, shuffle=False)

    global_model = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    global_state = copy.deepcopy(global_model.state_dict())

    round_history = []
    for round_num in range(1, rounds + 1):
        started = time.time()
        client_reports = []
        for client in partition["clients"]:
            indices = client["indices"]
            if not indices:
                # No samples this round -- nothing to train or aggregate,
                # but still show up in the per-client completion log.
                client_reports.append(
                    {
                        "client_id": client["client_id"],
                        "num_samples": 0,
                        "local_loss": None,
                        "completed": True,
                        "state_dict": None,
                    }
                )
                continue
            result = local_train(
                global_state=global_state,
                model_id=model_id,
                channels=channels,
                num_classes=num_classes,
                dataset=train_set,
                indices=indices,
                epochs=local_epochs,
                lr=lr,
                batch_size=batch_size,
                device=device,
            )
            client_reports.append(
                {
                    "client_id": client["client_id"],
                    "num_samples": result["num_samples"],
                    "local_loss": result["local_loss"],
                    "completed": True,
                    "state_dict": result["state_dict"],
                }
            )

        contributing = [c for c in client_reports if c["state_dict"] is not None]
        if not contributing:
            raise ValueError("No client had any samples to train on this round")

        global_state = federated_average(
            [c["state_dict"] for c in contributing],
            [c["num_samples"] for c in contributing],
        )
        global_model.load_state_dict(global_state)
        accuracy, loss = _evaluate(global_model, test_loader, device)

        round_history.append(
            {
                "round": round_num,
                "accuracy": accuracy,
                "loss": loss,
                "duration_seconds": time.time() - started,
                "clients": [
                    {
                        "client_id": c["client_id"],
                        "num_samples": c["num_samples"],
                        "local_loss": c["local_loss"],
                        "completed": c["completed"],
                    }
                    for c in client_reports
                ],
            }
        )

    history = {
        "experiment_id": experiment_id,
        "dataset": dataset_id,
        "model": model_id,
        "num_clients": partition["num_clients"],
        "rounds": rounds,
        "local_epochs": local_epochs,
        "seed": seed,
        "final_accuracy": round_history[-1]["accuracy"],
        "final_loss": round_history[-1]["loss"],
        "round_history": round_history,
    }

    save_fl_history(experiment_id, history)
    return history


def get_fl_history(experiment_id: str) -> dict:
    """Load a previously computed/persisted FL training history.

    Mirrors the conceptual ``get_fl_history(experiment_id)`` from the
    Dashboard Spec (Ch.36) / ComputeBackend interface.
    """
    return load_fl_history(experiment_id)
