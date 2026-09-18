"""Membership Inference Attack evaluation (Phase 10).

Implements the standard loss-threshold attack (Yeom et al., 2018,
"Privacy Risk in Machine Learning"): a model tends to have lower loss
on samples it was trained on ("members") than on samples it has never
seen ("non-members"), so an attacker who can query per-sample loss can
guess membership by thresholding it. No shadow models, no auxiliary
training required -- this is the standard simple MIA baseline, and the
one this project's evaluation is built around (the Dashboard Spec,
Ch.22, leaves the exact methodology to "the project's implemented MIA
methodology").

`run_membership_inference` reports **attack accuracy**: how often the
best threshold attack correctly labels a sample as member/non-member,
evaluated on an equal-sized, balanced mix of both classes.

    0.5 = chance level -- the attacker can't tell members from
          non-members. This is the goal after effective forgetting
          (Ch.22: "Should decrease after effective forgetting").
    1.0 = the attacker always gets it right.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from core.federated.model import build_model


def _per_sample_losses(model: nn.Module, loader: DataLoader, device: str) -> torch.Tensor:
    """Cross-entropy loss for every sample in `loader`, unreduced."""
    model.eval()
    criterion = nn.CrossEntropyLoss(reduction="none")
    losses = []
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            losses.append(criterion(outputs, labels).cpu())
    return torch.cat(losses) if losses else torch.empty(0)


def _best_threshold_accuracy(
    member_losses: torch.Tensor, nonmember_losses: torch.Tensor
) -> tuple[float, float]:
    """Sweep every observed loss value as a candidate threshold
    ("predict member if loss <= threshold") and return the threshold
    with the highest balanced attack accuracy, plus that accuracy.

    Balances the two classes by capping each to the smaller group's
    size, so the 0.5-is-chance baseline is meaningful regardless of how
    many member/non-member samples were passed in.
    """
    n = min(len(member_losses), len(nonmember_losses))
    if n == 0:
        raise ValueError("need at least one member and one non-member sample")
    members = member_losses[:n]
    nonmembers = nonmember_losses[:n]

    candidates = torch.cat([members, nonmembers]).unique()
    best_acc = 0.0
    best_threshold = float(candidates[0]) if len(candidates) else 0.0
    for threshold in candidates.tolist():
        correct = (members <= threshold).sum().item() + (nonmembers > threshold).sum().item()
        acc = correct / (2 * n)
        if acc > best_acc:
            best_acc = acc
            best_threshold = threshold
    return best_acc, best_threshold


def run_membership_inference(
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    train_dataset,
    member_indices: list[int],
    non_member_dataset,
    non_member_indices: list[int],
    device: str = "cpu",
    batch_size: int = 256,
) -> dict:
    """Run the loss-threshold MIA against one checkpoint.

    `member_indices` are the target client's own training indices
    (into `train_dataset`, the client whose removal is being measured).
    `non_member_indices` must come from data the model was never
    trained on at all -- the held-out test split (`non_member_dataset`)
    rather than another client's training data, so the attack's
    baseline reflects true non-membership rather than a different
    client's membership.
    """
    if not member_indices:
        raise ValueError("member_indices is empty -- nothing to attack")
    if not non_member_indices:
        raise ValueError("non_member_indices is empty -- nothing to attack")

    model = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    model.load_state_dict(state_dict)

    member_loader = DataLoader(
        Subset(train_dataset, member_indices), batch_size=batch_size, shuffle=False
    )
    nonmember_loader = DataLoader(
        Subset(non_member_dataset, non_member_indices), batch_size=batch_size, shuffle=False
    )

    member_losses = _per_sample_losses(model, member_loader, device)
    nonmember_losses = _per_sample_losses(model, nonmember_loader, device)

    attack_accuracy, threshold = _best_threshold_accuracy(member_losses, nonmember_losses)

    return {
        "attack_accuracy": attack_accuracy,
        "threshold": threshold,
        "member_count": len(member_losses),
        "non_member_count": len(nonmember_losses),
        "mean_member_loss": member_losses.mean().item() if len(member_losses) else 0.0,
        "mean_non_member_loss": nonmember_losses.mean().item() if len(nonmember_losses) else 0.0,
    }
