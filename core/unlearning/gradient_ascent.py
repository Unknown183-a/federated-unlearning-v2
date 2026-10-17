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

from core.unlearning.calibration import (
    CalibrationConfig,
    accuracy_on,
    ks_distance,
    per_sample_losses,
)

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
    calibration: CalibrationConfig | None = None,
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

    If `calibration` is given, ascent is stopped by calibrated rules
    instead of only the step budget (see core.unlearning.calibration):
    stop when the target client's per-sample loss distribution matches
    held-out data (KS distance <= ks_target), when it stops improving,
    or when retained guard accuracy drops too far -- and the returned
    weights are the best *safe* step, not necessarily the last one.
    Without `calibration` the behaviour is unchanged.
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

    # -- Calibrated-stopping state (unused when `calibration` is None) --
    cal_stop_reason: str | None = None
    cal_best_ks = None
    cal_best_state = None
    cal_best_step = 0
    cal_no_improve = 0
    cal_initial_ks = None
    cal_guard_baseline = 0.0
    cal_guard_on = False
    if calibration is not None:
        if not calibration.reference_indices:
            raise ValueError("calibration.reference_indices is empty")
        cal_guard_on = bool(calibration.guard_indices)
        if cal_guard_on:
            cal_guard_baseline = accuracy_on(
                model, calibration.guard_dataset, calibration.guard_indices, device
            )
        cal_initial_ks = ks_distance(
            per_sample_losses(model, dataset, target_indices, device),
            per_sample_losses(model, calibration.reference_dataset, calibration.reference_indices, device),
        )
        cal_best_ks = cal_initial_ks
        cal_best_state = copy.deepcopy(model.state_dict())
        if cal_initial_ks <= calibration.ks_target:
            # Already indistinguishable from unseen data: nothing to forget.
            cal_stop_reason = "already_calibrated"

    while step < steps and cal_stop_reason is None:
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
        record = {
            "step": step,
            "loss": step_loss,
            "accuracy": step_accuracy,
            "grad_norm": float(grad_norm),
        }

        if calibration is not None:
            ks = ks_distance(
                per_sample_losses(model, dataset, target_indices, device),
                per_sample_losses(model, calibration.reference_dataset, calibration.reference_indices, device),
            )
            record["ks_distance"] = ks
            safe = True
            if cal_guard_on:
                guard_acc = accuracy_on(
                    model, calibration.guard_dataset, calibration.guard_indices, device
                )
                record["retained_guard_accuracy"] = guard_acc
                safe = (cal_guard_baseline - guard_acc) <= calibration.max_retain_drop
            step_history.append(record)

            if not safe:
                cal_stop_reason = "retain_guard"
                break
            if ks < cal_best_ks:
                cal_best_ks = ks
                cal_best_state = copy.deepcopy(model.state_dict())
                cal_best_step = step
                cal_no_improve = 0
            else:
                cal_no_improve += 1
            if ks <= calibration.ks_target:
                cal_stop_reason = "ks_target_reached"
                break
            if cal_no_improve >= calibration.patience:
                cal_stop_reason = "ks_no_improvement"
                break
        else:
            step_history.append(record)

        if step_loss > best_loss + 1e-4:
            best_loss = step_loss
            plateau_count = 0
        else:
            plateau_count += 1
        if plateau_count >= plateau_patience:
            break

    if calibration is not None and cal_best_state is not None:
        # Return the best safe step, not whatever step ascent ended on.
        model.load_state_dict(cal_best_state)

    final_loss, final_accuracy = _evaluate_on_target(model, eval_loader, device)

    result = {
        "final_state_dict": copy.deepcopy(model.state_dict()),
        "initial_loss": initial_loss,
        "initial_accuracy": initial_accuracy,
        "final_loss": final_loss,
        "final_accuracy": final_accuracy,
        "steps_completed": step,
        "steps_requested": steps,
        "stopped_early": step < steps or cal_stop_reason is not None,
        "step_history": step_history,
    }
    if calibration is not None:
        result["calibration"] = {
            "stop_reason": cal_stop_reason or "step_budget_exhausted",
            "ks_target": calibration.ks_target,
            "max_retain_drop": calibration.max_retain_drop,
            "initial_ks_distance": cal_initial_ks,
            "selected_ks_distance": cal_best_ks,
            "selected_step": cal_best_step,
            "guard_baseline_accuracy": cal_guard_baseline if cal_guard_on else None,
            "reference_size": len(calibration.reference_indices),
            "guard_size": len(calibration.guard_indices or []),
        }
    return result
