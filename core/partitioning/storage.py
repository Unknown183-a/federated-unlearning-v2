"""Persistence for computed partitions (Phase 03).

Partitions are written to ``experiments/<experiment_id>/partition.json``
at the repo root -- the same ``experiments/`` directory DemoBackend
(Phase 00/14) is planned to read precomputed artifacts from.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"


def _partition_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "partition.json"


def save_partition(experiment_id: str, partition: dict) -> Path:
    """Persist a full partition (including per-client indices) to disk."""
    path = _partition_path(experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(partition, indent=2))
    return path


def load_partition(experiment_id: str) -> dict:
    """Load a previously saved partition. Raises FileNotFoundError if missing."""
    path = _partition_path(experiment_id)
    if not path.exists():
        raise FileNotFoundError(f"No partition found for experiment '{experiment_id}'")
    return json.loads(path.read_text())
