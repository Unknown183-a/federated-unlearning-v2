"""Accuracy evaluation (Phase 10).

Three of the five Evaluation-screen metrics (Ch.21-22, Page 7): global
accuracy, forget-client accuracy, and retained-client accuracy. Used by
`core.evaluation.evaluation_engine`, which calls each of these once
against the pre-unlearning checkpoint ("before") and once against the
final unlearned checkpoint ("after").

Deliberately independent of `core.unlearning`'s own per-client accuracy
tracking (Knowledge Distillation logs retained accuracy too, as part of
Phase 09's training loop) -- the Dashboard Spec keeps the Evaluation
Engine a separate backend service (Ch.35) from the Unlearning Engine,
so Phase 10's numbers are re-measured here rather than silently
depending on exactly how Phase 09 chose to log its own training-time
metrics.
"""
from __future__ import annotations

from statistics import mean

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from core.federated.model import build_model


def _build_and_load(
    state_dict: dict, model_id: str, channels: int, num_classes: int, device: str
) -> nn.Module:
    model = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def compute_accuracy(model: nn.Module, loader: DataLoader, device: str) -> float:
    """Return `model`'s accuracy on `loader`, with no grad tracking."""
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
    return correct / total if total else 0.0


def evaluate_global_accuracy(
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    test_dataset,
    device: str = "cpu",
    batch_size: int = 256,
) -> float:
    """Accuracy on the full held-out test split.

    "How much overall performance remains after unlearning" (Ch.22).
    """
    model = _build_and_load(state_dict, model_id, channels, num_classes, device)
    loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    return compute_accuracy(model, loader, device)


def evaluate_client_accuracy(
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    train_dataset,
    indices: list[int],
    device: str = "cpu",
    batch_size: int = 256,
) -> float:
    """Accuracy on one client's local training samples.

    Used for the forget-client metric ("helps demonstrate whether the
    selected client's information has been removed", Ch.22), and,
    per-client, to build the retained-client metric below.
    """
    if not indices:
        raise ValueError("indices is empty -- nothing to evaluate")
    model = _build_and_load(state_dict, model_id, channels, num_classes, device)
    loader = DataLoader(Subset(train_dataset, indices), batch_size=batch_size, shuffle=False)
    return compute_accuracy(model, loader, device)


def evaluate_retained_accuracy(
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    train_dataset,
    retained_clients: list[dict],
    device: str = "cpu",
    batch_size: int = 256,
) -> dict:
    """Retained-client accuracy: per-client, plus the mean across all of
    them.

    "Performance on data belonging to clients that should remain...
    helps demonstrate whether useful knowledge was preserved" (Ch.22).
    `retained_clients` uses the same ``{"client_id", "indices"}`` shape
    `core.partitioning`/`core.unlearning` already use.
    """
    if not retained_clients:
        raise ValueError("retained_clients is empty -- nothing to evaluate")
    model = _build_and_load(state_dict, model_id, channels, num_classes, device)
    per_client: dict[str, float] = {}
    for client in retained_clients:
        loader = DataLoader(
            Subset(train_dataset, client["indices"]), batch_size=batch_size, shuffle=False
        )
        # Keyed by str(client_id), not the int -- this dict is persisted
        # to evaluation_results.json, and JSON has no integer object
        # keys, so json.load() would hand back string keys anyway. Using
        # strings from the start means the in-memory result returned by
        # evaluate_experiment() and the one reloaded from disk are
        # actually equal, and matches the convention the frontend
        # already assumes (ClientInfluenceBars.jsx does
        # `Object.keys(retainedBefore).map(Number)` on exactly this
        # shape coming back from the unlearning status JSON).
        per_client[str(client["client_id"])] = compute_accuracy(model, loader, device)
    return {"per_client": per_client, "mean": mean(per_client.values())}
