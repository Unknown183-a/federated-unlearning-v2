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
