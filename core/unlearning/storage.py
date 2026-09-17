"""Persistence for unlearning status (Phase 08 + Phase 09).

Mirrors core/federated/storage.py: status is written to
``experiments/<experiment_id>/unlearning_status.json``, the
Gradient Ascent stage's resulting weights to
``experiments/<experiment_id>/unlearning_ga_model.pt`` -- both
alongside that experiment's ``partition.json``/``fl_history.json``/
``global_model.pt``. Knowledge Distillation (Phase 09) loads the GA
checkpoint as its starting point, and its own resulting weights --
the final unlearned model -- are saved to
``experiments/<experiment_id>/unlearning_final_model.pt``.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _status_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "unlearning_status.json"


def _ga_checkpoint_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "unlearning_ga_model.pt"


def _final_checkpoint_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "unlearning_final_model.pt"


def save_unlearning_status(experiment_id: str, status: dict) -> Path:
    """Persist the current unlearning status (overwrites any previous run)."""
    path = _status_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2))
    return path


def load_unlearning_status(experiment_id: str) -> dict:
    """Load the persisted unlearning status.

    Raises FileNotFoundError if `start_unlearning` hasn't been run yet
    for this experiment.
    """
    path = _status_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(f"No unlearning status found for experiment '{experiment_id}'")
    return json.loads(path.read_text())


def save_ga_checkpoint(
    experiment_id: str,
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
) -> Path:
    """Persist the Gradient Ascent stage's resulting weights.

    Same shape as `core.federated.storage.save_model_checkpoint` so
    Phase 09 can load either checkpoint the same way.
    """
    import torch

    path = _ga_checkpoint_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": state_dict,
            "model_id": model_id,
            "channels": channels,
            "num_classes": num_classes,
        },
        path,
    )
    return path


def load_ga_checkpoint(experiment_id: str) -> dict:
    """Load a previously saved Gradient Ascent checkpoint.

    Raises FileNotFoundError if the ascent stage hasn't run yet.
    """
    import torch

    path = _ga_checkpoint_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No Gradient Ascent checkpoint found for experiment '{experiment_id}' "
            "(run start_unlearning first)"
        )
    return torch.load(path, weights_only=False)


def save_final_checkpoint(
    experiment_id: str,
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
) -> Path:
    """Persist the fully unlearned model -- Gradient Ascent followed by
    Knowledge Distillation (Phase 09's "Unlearned Model" deliverable).

    Same shape as `save_ga_checkpoint`/`save_model_checkpoint` so a
    loader (e.g. Phase 10's evaluation) can reconstruct the model the
    same way regardless of which stage produced it.
    """
    import torch

    path = _final_checkpoint_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": state_dict,
            "model_id": model_id,
            "channels": channels,
            "num_classes": num_classes,
        },
        path,
    )
    return path


def load_final_checkpoint(experiment_id: str) -> dict:
    """Load the final (post-distillation) unlearned model checkpoint.

    Raises FileNotFoundError if Knowledge Distillation hasn't
    completed yet for this experiment.
    """
    import torch

    path = _final_checkpoint_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No final unlearned model found for experiment '{experiment_id}' "
            "(run start_unlearning first)"
        )
    return torch.load(path, weights_only=False)
