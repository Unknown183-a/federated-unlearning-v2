"""Knowledge Distillation unlearning step (Phase 09).

The repair stage: Gradient Ascent (Phase 08) deliberately damages the
whole model to forget the target client, but it has no way to damage
*only* the target client's influence -- the rest of the model's
accuracy on every other ("retained") client suffers too. This stage
repairs that collateral damage by distilling the *pre-ascent* global
model (the teacher, which still has all of its original accuracy)
back into the post-ascent model (the student), using the classic
Hinton et al. distillation objective:

    loss = alpha * CE(student_logits, hard_labels)
         + (1 - alpha) * T^2 * KL(softmax(student/T), softmax(teacher/T))

Training on the retained clients' data pulls the student back toward
the teacher's behavior on data it should still remember, without ever
showing it the target client's samples again -- so the forgetting from
Gradient Ascent isn't undone, only the accidental damage to everyone
else.
"""
from __future__ import annotations

import copy
from statistics import mean

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Subset

#: Standard temperature for the soft-target KL term (Hinton et al.,
#: 2015). Higher values soften the teacher's distribution further,
#: exposing more of the "dark knowledge" in its non-argmax logits.
DEFAULT_TEMPERATURE = 4.0

#: Weight on the hard-label term vs the soft-target term. 0.5 splits
#: the objective evenly between "get the right answer" and "match the
#: teacher's distribution".
DEFAULT_ALPHA = 0.5


def _evaluate_accuracy(model: nn.Module, loader: DataLoader, device: str) -> float:
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


def _client_eval_loaders(dataset, clients: list[dict], batch_size: int) -> dict[int, DataLoader]:
    return {
        client["client_id"]: DataLoader(
            Subset(dataset, client["indices"]), batch_size=max(batch_size, 256), shuffle=False
        )
        for client in clients
    }


def run_knowledge_distillation(
    teacher_state: dict,
    student_state: dict,
    model_id: str,
    channels: int,
    num_classes: int,
    dataset,
    retained_clients: list[dict],
    epochs: int = 5,
    lr: float = 0.01,
    temperature: float = DEFAULT_TEMPERATURE,
    alpha: float = DEFAULT_ALPHA,
    batch_size: int = 64,
    device: str = "cpu",
) -> dict:
    """Distill `teacher_state` (pre-ascent model) into `student_state`
    (post-ascent model), training only on `retained_clients`' data.

    `retained_clients` is a list of partition client dicts (Phase 03's
    shape: ``{"client_id": int, "indices": [...]}``) -- every client
    *except* the one Gradient Ascent targeted. Per-client accuracy is
    measured before and after distillation (Phase 09's acceptance
    criterion: "Retained-client accuracy recovers measurably after
    distillation"), alongside a per-epoch KD-loss/accuracy history for
    the live animation.

    Returns a dict with the resulting student state dict, the
    before/after per-client accuracy, and the full epoch history.
    """
    from core.federated.model import build_model

    if not retained_clients:
        raise ValueError("retained_clients is empty -- nothing to distill on")
    if epochs < 1:
        raise ValueError("epochs must be >= 1")

    teacher = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    teacher.load_state_dict(teacher_state)
    teacher.eval()
    for param in teacher.parameters():
        param.requires_grad_(False)

    student = build_model(model_id, channels=channels, num_classes=num_classes).to(device)
    student.load_state_dict(student_state)

    client_loaders = _client_eval_loaders(dataset, retained_clients, batch_size)
    all_indices = [i for client in retained_clients for i in client["indices"]]
    train_loader = DataLoader(Subset(dataset, all_indices), batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.SGD(student.parameters(), lr=lr, momentum=0.9)
    hard_criterion = nn.CrossEntropyLoss()

    per_client_accuracy_before = {
        client_id: _evaluate_accuracy(student, loader, device)
        for client_id, loader in client_loaders.items()
    }
    initial_retained_accuracy = mean(per_client_accuracy_before.values())

    epoch_history: list[dict] = []
    for epoch in range(1, epochs + 1):
        student.train()
        total_loss = 0.0
        total_batches = 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            student_logits = student(images)
            with torch.no_grad():
                teacher_logits = teacher(images)

            hard_loss = hard_criterion(student_logits, labels)
            soft_loss = (
                F.kl_div(
                    F.log_softmax(student_logits / temperature, dim=1),
                    F.softmax(teacher_logits / temperature, dim=1),
                    reduction="batchmean",
                )
                * (temperature**2)
            )
            loss = alpha * hard_loss + (1 - alpha) * soft_loss

            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            total_batches += 1

        avg_kd_loss = total_loss / total_batches if total_batches else 0.0
        epoch_accuracy = {
            client_id: _evaluate_accuracy(student, loader, device)
            for client_id, loader in client_loaders.items()
        }
        epoch_history.append(
            {
                "epoch": epoch,
                "kd_loss": avg_kd_loss,
                "retained_accuracy": mean(epoch_accuracy.values()),
            }
        )

    per_client_accuracy_after = {
        client_id: _evaluate_accuracy(student, loader, device)
        for client_id, loader in client_loaders.items()
    }
    final_retained_accuracy = mean(per_client_accuracy_after.values())

    return {
        "final_state_dict": copy.deepcopy(student.state_dict()),
        "temperature": temperature,
        "alpha": alpha,
        "epochs_completed": epochs,
        "epochs_requested": epochs,
        "initial_retained_accuracy": initial_retained_accuracy,
        "final_retained_accuracy": final_retained_accuracy,
        "per_client_accuracy_before": per_client_accuracy_before,
        "per_client_accuracy_after": per_client_accuracy_after,
        "epoch_history": epoch_history,
    }
