"""CLI entrypoint the Express backend shells out to (Phase 08).

    python -m core.unlearning.cli --experiment-id demo-1 --client-id 3 \\
        --steps 30 --lr 0.01

Requires that experiment ``demo-1`` already has a partition (Phase 03)
and a trained global model checkpoint (Phase 05) saved. Runs the
Gradient Ascent stage against the given client's local data, persists
the resulting status + ascent-stage weights, and prints that same
status as JSON on stdout for the API layer.
"""
from __future__ import annotations

import argparse
import json
import sys

from core.unlearning.unlearning_engine import start_unlearning


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Gradient Ascent unlearning stage.")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--client-id", type=int, required=True)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args(argv)

    try:
        status = start_unlearning(
            experiment_id=args.experiment_id,
            client_id=args.client_id,
            steps=args.steps,
            lr=args.lr,
            batch_size=args.batch_size,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
