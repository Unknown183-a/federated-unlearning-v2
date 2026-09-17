"""Persistence for federated training history (Phase 05).

Mirrors core/partitioning/storage.py: history is written to
``experiments/<experiment_id>/fl_history.json`` alongside that
experiment's ``partition.json``.

Addendum (Phase 08): ``run_federated_training`` produced round-by-round
*metrics* (accuracy/loss) but never persisted the trained global
model's *weights* anywhere -- fine for Phase 06's charts and Phase 07's
summary card, both of which only read ``fl_history.json``, but the
Gradient Ascent stage needs to actually load the trained model to run
ascent steps against it. ``save_model_checkpoint``/``load_model_checkpoint``
below fill that gap, writing alongside the existing history file rather
than changing its shape.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _history_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "fl_history.json"


def _checkpoint_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "global_model.pt"


def save_fl_history(experiment_id: str, history: dict) -> Path:
    """Persist a completed (or in-progress) FL training history."""
    path = _history_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2))
    return path


def load_fl_history(experiment_id: str) -> dict:
    """Load a previously saved FL training history.

    Raises FileNotFoundError if this experiment hasn't been trained yet.
    """
    path = _history_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(f"No FL history found for experiment '{experiment_id}'")
    return json.loads(path.read_text())


def save_model_checkpoint(
    experiment_id: str,
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
) -> Path:
    """Persist the final trained global model's weights + build metadata.

    ``model_id``/``channels``/``num_classes`` are saved alongside the
    weights so a loader can reconstruct the exact architecture via
    ``core.federated.model.build_model`` without re-deriving it from
    the dataset manifest.
    """
    import torch

    path = _checkpoint_path(experiment_id)
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


def load_model_checkpoint(experiment_id: str) -> dict:
    """Load a previously saved global model checkpoint.

    Returns a dict with ``state_dict``, ``model_id``, ``channels``, and
    ``num_classes``. Raises FileNotFoundError if this experiment has no
    saved checkpoint (e.g. it was trained before this addendum, or
    training hasn't run yet).
    """
    import torch

    path = _checkpoint_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No model checkpoint found for experiment '{experiment_id}' "
            "(re-run federated training to produce one)"
        )
    return torch.load(path, weights_only=False)
