"""Run the machine-checkable acceptance checks against stored experiments.

    python -m core.acceptance.cli --experiment-id exp-abc123
    python -m core.acceptance.cli --all
    python -m core.acceptance.cli --all --json          # for tooling

Exit code is 0 only if no experiment has a failed check, so this can
gate a release or a "ready to present" step. Warnings (e.g. a run made
before Phase 15 that has no recorded unlearning hyperparameters) do not
fail the run.

Needs no torch, no GPU and no network: it only reads the JSON artifacts.
"""
from __future__ import annotations

import argparse
import json
import sys

from core.acceptance.checks import FAIL, WARN, list_experiment_ids, validate_experiment

_ICON = {"pass": "PASS", "fail": "FAIL", "warn": "WARN"}


def _print_human(report: dict) -> None:
    s = report["summary"]
    print(f"\nExperiment {report['experiment_id']}: {s['passed']} passed, {s['failed']} failed, {s['warnings']} warnings")
    section = None
    for c in report["checks"]:
        if c["section"] != section:
            section = c["section"]
            print(f"  {section}")
        line = f"    [{_ICON[c['status']]}] {c['description']}"
        if c["detail"] and c["status"] in (FAIL, WARN):
            line += f"\n           -> {c['detail']}"
        print(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check stored experiments against the acceptance checklist.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--experiment-id", help="Check one experiment")
    group.add_argument("--all", action="store_true", help="Check every experiment under experiments/")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    args = parser.parse_args(argv)

    ids = list_experiment_ids() if args.all else [args.experiment_id]
    if not ids:
        print("No experiments found under experiments/.", file=sys.stderr)
        return 1

    reports = [validate_experiment(i) for i in ids]
    if args.json:
        print(json.dumps({"reports": reports, "ok": all(r["ok"] for r in reports)}))
    else:
        for report in reports:
            _print_human(report)
    return 0 if all(r["ok"] for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
