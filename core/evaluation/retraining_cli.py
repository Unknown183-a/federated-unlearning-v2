"""CLI entrypoint the Express backend shells out to (Phase 11).

    # Run the (expensive) full-retraining baseline, then compare:
    python -m core.evaluation.retraining_cli --experiment-id demo-1

    # Just re-read/re-compute the comparison from stored artifacts
    # (cheap; no training, no torch import):
    python -m core.evaluation.retraining_cli --experiment-id demo-1 --compare-only

Prints ``{"retraining": {...}, "comparison": {...}}`` (or, with
``--compare-only``, ``{"comparison": {...}}``) as JSON on stdout.
Errors go to stderr with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Phase 11 full-retraining baseline and/or compare it with unlearning."
    )
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--compare-only",
        action="store_true",
        help="Skip retraining; compare the stored evaluation and stored retraining baseline",
    )
    args = parser.parse_args(argv)

    try:
        # Imported lazily so --compare-only never pays for torch.
        from core.evaluation.comparison import compare_with_retraining

        output: dict = {}
        if not args.compare_only:
            from core.evaluation.retraining import run_retraining_baseline

            output["retraining"] = run_retraining_baseline(args.experiment_id, device=args.device)
        output["comparison"] = compare_with_retraining(args.experiment_id)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
