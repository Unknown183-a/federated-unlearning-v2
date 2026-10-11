"""Command-line entry for model releases (Phase 16). Prints one JSON object.

Input mistakes (bad mode, unknown device, nothing to publish yet) are printed
as {"error": "..."} with exit code 0, so the backend can answer 400 with a
plain message. Only genuine crashes exit non-zero.

    python -m core.distribution.cli state --experiment-id <id>
    python -m core.distribution.cli release-original --experiment-id <id>
    python -m core.distribution.cli publish --experiment-id <id> --mode request --grace-hours 48
    python -m core.distribution.cli devices --experiment-id <id> --count 8
    python -m core.distribution.cli check-in --experiment-id <id> [--device device-01]
    python -m core.distribution.cli accept --experiment-id <id> --device device-01
    python -m core.distribution.cli online --experiment-id <id> --device device-01 --value false
    python -m core.distribution.cli advance-clock --experiment-id <id> --hours 24
    python -m core.distribution.cli reset --experiment-id <id>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.distribution import releases


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experiments-dir", default=None, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name: str) -> argparse.ArgumentParser:
        item = sub.add_parser(name)
        item.add_argument("--experiment-id", required=True)
        return item

    command("state")
    command("release-original")
    publish = command("publish")
    publish.add_argument("--mode", required=True)
    publish.add_argument("--grace-hours", default=None)
    publish.add_argument("--note", default="")
    devices = command("devices")
    devices.add_argument("--count", required=True, type=int)
    check_in = command("check-in")
    check_in.add_argument("--device", default=None)
    accept = command("accept")
    accept.add_argument("--device", required=True)
    online = command("online")
    online.add_argument("--device", required=True)
    online.add_argument("--value", required=True, choices=["true", "false"])
    clock = command("advance-clock")
    clock.add_argument("--hours", required=True)
    command("reset")
    return parser


def run(argv: list[str] | None = None) -> dict:
    args = _parser().parse_args(argv)
    folder = Path(args.experiments_dir) if args.experiments_dir else None
    eid = args.experiment_id
    if args.command == "state":
        return releases.get_state(eid, folder)
    if args.command == "release-original":
        return releases.release_original(eid, folder)
    if args.command == "publish":
        return releases.publish_release(eid, args.mode, args.grace_hours, args.note, folder)
    if args.command == "devices":
        return releases.register_devices(eid, args.count, folder)
    if args.command == "check-in":
        return releases.check_in(eid, args.device, folder)
    if args.command == "accept":
        return releases.accept_update(eid, args.device, folder)
    if args.command == "online":
        return releases.set_online(eid, args.device, args.value == "true", folder)
    if args.command == "advance-clock":
        return releases.advance_clock(eid, args.hours, folder)
    if args.command == "reset":
        return releases.reset(eid, folder)
    raise ValueError("Unknown command.")


def main(argv: list[str] | None = None) -> int:
    try:
        payload = run(argv)
    except (ValueError, FileNotFoundError) as exc:
        payload = {"error": str(exc)}
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
