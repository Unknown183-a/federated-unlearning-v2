"""Calibrated forgetting (opt-in extension to Phase 08).

Plain Gradient Ascent has no notion of "enough": it keeps raising the
target client's loss until a step budget runs out. That over-forgets --
the stored MNIST demo drives the target loss from 0.03 to ~130 and the
accuracy to ~10%, far below what a model that never saw the client
would score. A sudden collapse on one client's data is itself a
fingerprint of unlearning.

Calibrated forgetting stops ascent when the model treats the target
client's samples like *unseen* samples from the same distribution:

    KS(loss on target-client samples, loss on held-out reference samples)

is the two-sample Kolmogorov-Smirnov distance between the two per-sample
loss distributions (0 = indistinguishable, 1 = fully separated). Ascent
also stops (and rolls back to the last safe step) if accuracy on a guard
set of retained-client samples drops by more than a tolerance.

Everything here is opt-in; with no `CalibrationConfig` passed,
`run_gradient_ascent` behaves exactly as before.

Caveat: this is an empirical stopping rule, not a formal erasure
guarantee.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset


@dataclass
class CalibrationConfig:
    """Settings for calibrated stopping.

    reference_*: held-out samples the model never trained on, used as
        the "unseen data" yardstick. Must NOT overlap the samples the
        Phase 10 evaluation uses as MIA non-members.
    guard_*: retained-client training samples used to watch collateral
        damage during ascent (optional; leave indices empty to disable).
    ks_target: stop once KS distance falls to or below this value.
    max_retain_drop: largest allowed fall in guard accuracy (absolute,
        e.g. 0.05 = 5 points) before ascent is stopped and rolled back.
    patience: stop after this many steps without a new best KS distance.
    """

    reference_dataset: object
    reference_indices: list
    guard_dataset: object = None
    guard_indices: list | None = None
    ks_target: float = 0.1
    max_retain_drop: float = 0.05
    patience: int = 5


def per_sample_losses(
    model: nn.Module, dataset, indices: list, device: str, batch_size: int = 256
) -> torch.Tensor:
    """Unreduced cross-entropy for every sample in `indices`."""
    model.eval()
    criterion = nn.CrossEntropyLoss(reduction="none")
    loader = DataLoader(Subset(dataset, indices), batch_size=batch_size, shuffle=False)
    losses = []
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            losses.append(criterion(model(images), labels).cpu())
    return torch.cat(losses) if losses else torch.empty(0)


def accuracy_on(model: nn.Module, dataset, indices: list, device: str, batch_size: int = 256) -> float:
    """Accuracy of `model` on `indices` of `dataset` (0.0 if empty)."""
    if not indices:
        return 0.0
    model.eval()
    loader = DataLoader(Subset(dataset, indices), batch_size=batch_size, shuffle=False)
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            correct += (model(images).argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
    return correct / total if total else 0.0


def ks_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    """Two-sample Kolmogorov-Smirnov statistic: max |ECDF_a - ECDF_b|."""
    if a.numel() == 0 or b.numel() == 0:
        raise ValueError("ks_distance needs two non-empty samples")
    a_sorted = torch.sort(a.flatten()).values.contiguous()
    b_sorted = torch.sort(b.flatten()).values.contiguous()
    grid = torch.cat([a_sorted, b_sorted])
    cdf_a = torch.searchsorted(a_sorted, grid, right=True).float() / a_sorted.numel()
    cdf_b = torch.searchsorted(b_sorted, grid, right=True).float() / b_sorted.numel()
    return (cdf_a - cdf_b).abs().max().item()
