"""Persistence for evaluation results (Phase 10).

Mirrors core/unlearning/storage.py: results are written to
``experiments/<experiment_id>/evaluation_results.json``, alongside
that experiment's ``partition.json``/``fl_history.json``/
``unlearning_status.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _results_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "evaluation_results.json"


def save_evaluation_results(experiment_id: str, results: dict) -> Path:
    """Persist the current evaluation results (overwrites any previous run)."""
    path = _results_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2))
    return path


def load_evaluation_results(experiment_id: str) -> dict:
    """Load previously saved evaluation results.

    Raises FileNotFoundError if `evaluate_experiment` hasn't been run
    yet for this experiment.
    """
    path = _results_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(f"No evaluation results found for experiment '{experiment_id}'")
    return json.loads(path.read_text())


# -- Full-retraining baseline (Phase 11) ----------------------------------
#
# The retraining baseline is a *separate run* from the unlearning
# pipeline (Ch.24) -- its own weights and its own results file, stored
# alongside (never over) the original experiment's artifacts:
#
#   experiments/<id>/retraining_results.json   metrics + runtime
#   experiments/<id>/retrained_model.pt        the retrained weights


def _retraining_results_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "retraining_results.json"


def _retrained_checkpoint_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "retrained_model.pt"


def save_retraining_results(experiment_id: str, results: dict) -> Path:
    """Persist the retraining baseline's results (overwrites any previous run)."""
    path = _retraining_results_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2))
    return path


def load_retraining_results(experiment_id: str) -> dict:
    """Load a previously stored retraining baseline.

    Raises FileNotFoundError if the baseline hasn't been run yet.
    """
    path = _retraining_results_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(f"No retraining baseline found for experiment '{experiment_id}'")
    return json.loads(path.read_text())


def save_retrained_checkpoint(
    experiment_id: str,
    state_dict: dict,
    model_id: str,
    channels: int,
    num_classes: int,
) -> Path:
    """Persist the retrained model's weights (same shape as the other checkpoints)."""
    import torch

    path = _retrained_checkpoint_path(experiment_id)
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


def load_retrained_checkpoint(experiment_id: str) -> dict:
    """Load the retrained model checkpoint. Raises FileNotFoundError if absent."""
    import torch

    path = _retrained_checkpoint_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(
            f"No retrained model found for experiment '{experiment_id}' "
            "(run the retraining baseline first)"
        )
    return torch.load(path, weights_only=False)
