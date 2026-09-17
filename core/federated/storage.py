"""Persistence for federated training history (Phase 05).

Mirrors core/partitioning/storage.py: history is written to
``experiments/<experiment_id>/fl_history.json`` alongside that
experiment's ``partition.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _history_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "fl_history.json"


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
