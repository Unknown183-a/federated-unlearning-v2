"""Gradient Ascent unlearning step (Phase 08).

The forgetting stage: instead of the usual training direction (descend
the loss on a client's data so the model gets *better* at it), we
ascend the loss on the target client's data so the model gets
deliberately *worse* at it -- pushing it to unlearn whatever it picked
up from that client during FedAvg (Phase 05).

Implemented the standard way this is done in practice: minimize the
*negated* cross-entropy loss with an ordinary SGD optimizer. Minimizing
``-loss`` is exactly gradient ascent on ``loss``, so this reuses
`torch.optim.SGD` instead of hand-rolling a parameter update rule.

Only the ascent stage lives here (Phase 08 scope). Knowledge
Distillation, which repairs the rest of the model afterwards, is
Phase 09.
"""
from __future__ import annotations

import copy

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

#: Cap on how far any single ascent step is allowed to push a
#: parameter. Gradient ascent has no natural convergence point (unlike
#: descent, it diverges by design), so unclipped gradients can blow the
#: target client's loss up so fast that the rest of the model's
#: weights are no longer recoverable for Phase 09's distillation step.
#: This keeps ascent controlled instead of destructive.
DEFAULT_GRAD_CLIP_NORM = 5.0

#: Stop early if the target-client loss has stopped rising for this
#: many consecutive steps -- once ascent plateaus, further steps just
#: keep damaging the rest of the model for no additional forgetting.
DEFAULT_PLATEAU_PATIENCE = 5


def _evaluate_on_target(model: nn.Module, loader: DataLoader, device: str) -> tuple[float, float]:
    """Return (avg_loss, accuracy) of `model` on the target client's data."""
    model.eval()
    criterion = nn.CrossEntropyLoss(reduction="sum")
    correct = 0
    total = 0
    total_loss = 0.0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            total_loss += criterion(outputs, labels).item()
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
    avg_loss = total_loss / total if total else 0.0
    accuracy = correct / total if total else 0.0
    return avg_loss, accuracy


def run_gradient_ascent(
    global_state: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    dataset,
    target_indices: list[int],
    steps: int = 30,
    lr: float = 0.01,
    batch_size: int = 32,
    grad_clip_norm: float = DEFAULT_GRAD_CLIP_NORM,
    plateau_patience: int = DEFAULT_PLATEAU_PATIENCE,
    device: str = "cpu",
) -> dict:
    """Run the Gradient Ascent stage against one client's local data.

    Starts from the trained global model (`global_state`) and takes up
    to `steps` ascent steps on the target client's own samples
    (`target_indices` into `dataset`), logging the target-client loss
    and accuracy at every step (Ch.15 of the Dashboard Spec).

    Returns a dict with the resulting state dict and the full
    per-step history, so callers can both use the new weights (feed
    them into Phase 09's Knowledge Distillation) and show the live
    chart the spec calls for.
    """
    from core.federated.model import build_model

    if not target_indices:
        raise ValueError("target_indices is empty -- nothing to ascend against")
    if steps < 1:
        raise ValueError("steps must be >= 1")

    model = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    model.load_state_dict(global_state)

    subset = Subset(dataset, target_indices)
    loader = DataLoader(subset, batch_size=batch_size, shuffle=True)
    # A fixed, non-shuffled loader for consistent before/after/per-step
    # evaluation -- the training loader above reshuffles every step.
    eval_loader = DataLoader(subset, batch_size=max(batch_size, 256), shuffle=False)

    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    criterion = nn.CrossEntropyLoss()

    initial_loss, initial_accuracy = _evaluate_on_target(model, eval_loader, device)

    step_history: list[dict] = []
    best_loss = initial_loss
    plateau_count = 0
    step = 0
    data_iter = iter(loader)

    while step < steps:
        step += 1
        try:
            images, labels = next(data_iter)
        except StopIteration:
            data_iter = iter(loader)
            images, labels = next(data_iter)
        images, labels = images.to(device), labels.to(device)

        model.train()
        optimizer.zero_grad()
        outputs = model(images)
        # Ascent, not descent: minimizing -loss maximizes loss.
        loss = criterion(outputs, labels)
        (-loss).backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip_norm)
        optimizer.step()

        step_loss, step_accuracy = _evaluate_on_target(model, eval_loader, device)
        step_history.append(
            {
                "step": step,
                "loss": step_loss,
                "accuracy": step_accuracy,
                "grad_norm": float(grad_norm),
            }
        )

        if step_loss > best_loss + 1e-4:
            best_loss = step_loss
            plateau_count = 0
        else:
            plateau_count += 1
        if plateau_count >= plateau_patience:
            break

    final_loss, final_accuracy = _evaluate_on_target(model, eval_loader, device)

    return {
        "final_state_dict": copy.deepcopy(model.state_dict()),
        "initial_loss": initial_loss,
        "initial_accuracy": initial_accuracy,
        "final_loss": final_loss,
        "final_accuracy": final_accuracy,
        "steps_completed": step,
        "steps_requested": steps,
        "stopped_early": step < steps,
        "step_history": step_history,
    }
