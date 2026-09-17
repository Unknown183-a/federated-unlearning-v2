"""CLI entrypoint the Express backend shells out to (Phase 03).

    python -m core.partitioning.cli --dataset cifar10 --num-clients 10 \\
        --strategy non_iid --seed 42 --experiment-id demo-1

Computes the partition, persists the full partition (with per-client
sample indices, for later phases like federated training to consume)
to experiments/<experiment-id>/partition.json, and prints the
lightweight summary (no indices) as JSON on stdout for the API layer.
"""
from __future__ import annotations

import argparse
import json
import sys

from core.partitioning.engine import partition_dataset, summarize_partition
from core.partitioning.storage import save_partition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Partition a dataset across federated clients.")
    parser.add_argument("--dataset", required=True, help="Dataset id, e.g. cifar10")
    parser.add_argument("--num-clients", type=int, required=True)
    parser.add_argument("--strategy", choices=["iid", "non_iid"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--alpha", type=float, default=0.5, help="Dirichlet alpha (non_iid only)")
    args = parser.parse_args(argv)

    try:
        partition = partition_dataset(
            dataset=args.dataset,
            num_clients=args.num_clients,
            strategy=args.strategy,
            seed=args.seed,
            alpha=args.alpha,
        )
    except (ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    save_partition(args.experiment_id, partition)
    print(json.dumps(summarize_partition(partition)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
