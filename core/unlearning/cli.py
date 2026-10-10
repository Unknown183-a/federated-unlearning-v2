"""CLI entrypoint the Express backend shells out to (Phase 08 + 09).

    python -m core.unlearning.cli --experiment-id demo-1 --client-id 3 \\
        --steps 30 --lr 0.01 --kd-epochs 5 --kd-lr 0.01

Requires that experiment ``demo-1`` already has a partition (Phase 03)
and a trained global model checkpoint (Phase 05) saved. Runs the
Gradient Ascent stage against the given client's local data, followed
by Knowledge Distillation against every other client, persists the
resulting status + both stages' weights, and prints that same status
as JSON on stdout for the API layer.
"""
from __future__ import annotations

import argparse
import json
import sys

from core.unlearning.unlearning_engine import start_unlearning


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Gradient Ascent + Knowledge Distillation unlearning pipeline."
    )
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--client-id", type=int, required=True)
    parser.add_argument("--steps", type=int, default=30, help="Gradient Ascent steps")
    parser.add_argument("--lr", type=float, default=0.01, help="Gradient Ascent learning rate")
    parser.add_argument("--batch-size", type=int, default=32, help="Gradient Ascent batch size")
    parser.add_argument("--kd-epochs", type=int, default=5, help="Knowledge Distillation epochs")
    parser.add_argument("--kd-lr", type=float, default=0.01, help="Knowledge Distillation learning rate")
    parser.add_argument("--kd-temperature", type=float, default=4.0, help="KD softmax temperature")
    parser.add_argument("--kd-alpha", type=float, default=0.5, help="KD hard-label loss weight")
    parser.add_argument("--kd-batch-size", type=int, default=64, help="Knowledge Distillation batch size")
    # Phase 14: optional compute backend selection. Omitted (the
    # default) behaves exactly as before this flag existed.
    parser.add_argument(
        "--backend",
        default=None,
        help="Compute backend: college_gpu | colab | local | demo | auto. Default: run in-process, same as omitting this flag.",
    )
    args = parser.parse_args(argv)

    unlearning_kwargs = dict(
        experiment_id=args.experiment_id,
        client_id=args.client_id,
        steps=args.steps,
        lr=args.lr,
        batch_size=args.batch_size,
        kd_epochs=args.kd_epochs,
        kd_lr=args.kd_lr,
        kd_temperature=args.kd_temperature,
        kd_alpha=args.kd_alpha,
        kd_batch_size=args.kd_batch_size,
    )

    if args.backend is not None:
        from core.compute.base import BackendUnavailableError, NotSupportedError
        from core.compute.registry import call_with_fallback

        try:
            status, trace = call_with_fallback(args.backend, "start_unlearning", **unlearning_kwargs)
        except (BackendUnavailableError, NotSupportedError, FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps({"status": status, "backend_trace": trace}))
        return 0

    try:
        status = start_unlearning(**unlearning_kwargs)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
