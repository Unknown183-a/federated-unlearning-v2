"""CLI entrypoint the Express backend shells out to (Phase 14).

    python -m core.compute.cli status

Prints the status of every compute backend plus which one Auto mode
would currently select, as JSON on stdout -- what the Compute Backend
status panel renders. Never fails: every backend's get_status() is
built to report unavailable rather than raise (see base.py), and
resolve_auto_backend() always resolves to at least Demo.
"""
from __future__ import annotations

import argparse
import json

from core.compute.registry import all_statuses, resolve_auto_backend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report every compute backend's status.")
    parser.parse_args(argv)  # no arguments yet -- kept for consistency with the other CLIs

    statuses = all_statuses()
    _, auto_trace = resolve_auto_backend()
    auto_selected = auto_trace[-1]["backend"]

    print(json.dumps({"backends": statuses, "auto_selected": auto_selected, "auto_trace": auto_trace}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
