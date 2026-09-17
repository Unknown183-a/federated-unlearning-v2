"""Federated learning client logic (Phase 05).

One client = one shard of the training set (from Phase 03's
partition) plus a local copy of the current global model. Each round,
a client trains that local copy for a few epochs and reports back its
updated weights and how many samples it trained on -- the latter is
what FedAvg (fedavg.py) weights the aggregation by.
"""
from __future__ import annotations

import copy

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset


def local_train(
    global_state: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    dataset,
    indices: list[int],
    epochs: int,
    lr: float = 0.01,
    batch_size: int = 32,
    device: str = "cpu",
) -> dict:
    """Run one client's local training step for one round.

    Builds a fresh model from `model_id`, loads `global_state` into it,
    trains it on `dataset[indices]` for `epochs` epochs, and returns the
    updated state dict plus this client's local stats.
    """
    from core.federated.model import build_model

    model = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    model.load_state_dict(global_state)
    model.train()

    subset = Subset(dataset, indices)
    loader = DataLoader(subset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    criterion = nn.CrossEntropyLoss()

    total_loss = 0.0
    total_samples = 0
    for _ in range(max(1, epochs)):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * images.size(0)
            total_samples += images.size(0)

    avg_loss = total_loss / total_samples if total_samples else 0.0
    return {
        "state_dict": copy.deepcopy(model.state_dict()),
        "num_samples": len(indices),
        "local_loss": avg_loss,
    }
