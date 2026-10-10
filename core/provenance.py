"""Reproducibility metadata (Phase 15, Dashboard Spec Ch.44).

Spec Ch.44 asks every experiment to store, among other things, its
"Software/config version" and "Unlearning hyperparameters". Until this
phase the artifacts recorded the dataset, partition, seed, FL protocol
and metrics -- but not which code produced them or which unlearning
hyperparameters were used, so a result could not be reproduced exactly.

`software_info()` is attached to the unlearning status and the
evaluation / retraining results. It only reports what it can actually
observe (a missing git checkout gives ``git_commit: None``, never a
made-up value) and never raises -- provenance must not be able to break
a run.
"""
from __future__ import annotations

import platform
import subprocess
from functools import lru_cache
from pathlib import Path

#: Bumped by hand when the artifact formats or algorithms change in a
#: way that makes older results not directly comparable.
PROJECT_VERSION = "1.0.0"

_REPO_ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = out.stdout.strip()
    return commit if out.returncode == 0 and commit else None


def _package_version(name: str) -> str | None:
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version(name)
    except PackageNotFoundError:
        return None
    except Exception:  # pragma: no cover - defensive; never break a run
        return None


def software_info() -> dict:
    """What produced a result: project version, git commit, runtimes."""
    return {
        "project_version": PROJECT_VERSION,
        "git_commit": _git_commit(),
        "python": platform.python_version(),
        "torch": _package_version("torch"),
        "numpy": _package_version("numpy"),
    }
