"""CLI entrypoint the Express backend shells out to (Phase 10).

    python -m core.evaluation.cli --experiment-id demo-1

Requires that experiment ``demo-1`` already has a trained checkpoint
(Phase 05) and a completed unlearning run (Phase 08+09) saved. Computes
all five Page 7 metrics before/after, persists them, and prints the
result as JSON on stdout for the API layer.
"""
from __future__ import annotations

import argparse
import json
import sys

from core.evaluation.evaluation_engine import DEFAULT_NON_MEMBER_SAMPLE_SIZE, evaluate_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Phase 10 evaluation: accuracy (global/forget/retained), MIA, and runtime."
    )
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument(
        "--non-member-sample-size",
        type=int,
        default=DEFAULT_NON_MEMBER_SAMPLE_SIZE,
        help="Held-out test samples used as the MIA's non-member set",
    )
    parser.add_argument("--device", default="cpu")
    # Phase 14: optional compute backend selection. Omitted (the
    # default) behaves exactly as before this flag existed.
    parser.add_argument(
        "--backend",
        default=None,
        help="Compute backend: college_gpu | colab | local | demo | auto. Default: run in-process, same as omitting this flag.",
    )
    args = parser.parse_args(argv)

    if args.backend is not None:
        from core.compute.base import BackendUnavailableError, NotSupportedError
        from core.compute.registry import call_with_fallback

        try:
            results, trace = call_with_fallback(
                args.backend,
                "run_evaluation",
                experiment_id=args.experiment_id,
                non_member_sample_size=args.non_member_sample_size,
            )
        except (BackendUnavailableError, NotSupportedError, FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps({"results": results, "backend_trace": trace}))
        return 0

    try:
        results = evaluate_experiment(
            experiment_id=args.experiment_id,
            non_member_sample_size=args.non_member_sample_size,
            device=args.device,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
