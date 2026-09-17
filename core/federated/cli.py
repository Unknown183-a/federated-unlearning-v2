"""CLI entrypoint the Express backend shells out to (Phase 05).

    python -m core.federated.cli --experiment-id demo-1 --model cnn \\
        --rounds 20 --local-epochs 1 --seed 42

Requires that experiment ``demo-1`` already has a partition saved by
core.partitioning.cli (Phase 03) -- this loads that partition, runs
the FedAvg loop against it, persists the full round-by-round history
to experiments/<experiment-id>/fl_history.json, and prints that same
history as JSON on stdout for the API layer.
"""
from __future__ import annotations

import argparse
import json
import sys

from core.partitioning.storage import load_partition
from core.federated.server import run_federated_training


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run FedAvg training for an experiment.")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--model", choices=["cnn", "resnet"], default="cnn")
    parser.add_argument("--rounds", type=int, required=True)
    parser.add_argument("--local-epochs", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args(argv)

    try:
        partition = load_partition(args.experiment_id)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        history = run_federated_training(
            experiment_id=args.experiment_id,
            partition=partition,
            model_id=args.model,
            rounds=args.rounds,
            local_epochs=args.local_epochs,
            seed=args.seed,
            lr=args.lr,
            batch_size=args.batch_size,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(history))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
