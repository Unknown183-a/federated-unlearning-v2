"""Model releases and the update policy for devices that already installed a model (Phase 16).

Unlearning produces a new model on the server. Devices that downloaded the old
model still hold a copy that contains the forgotten client's influence, and
nothing on the server can edit those copies. What the server CAN do is publish
the unlearned model as a new version, ask devices to switch, and stop allowing
the old version. This module is that logic. Standard library only: no torch.

Two update modes (chosen when an unlearned model is published):

  auto     Devices that are online are updated immediately. A device that is
           offline is updated the moment it reconnects. The old version is
           revoked straight away.

  request  Every device is asked to update and may accept until a deadline
           (published time + grace hours). The old version stays allowed until
           the deadline. A device that has not updated by then is updated
           automatically (online devices at the deadline, offline ones when
           they reconnect) and the old version is revoked.

Honest limits (also in docs/MODEL_UPDATES.md): this is a policy engine plus a
SIMULATION of devices. No real app is installed anywhere. A real device can
still keep an old copy of the model file or block the update; enforcement on
the device side (refusing to run a revoked version) is the client app's job.

State lives in experiments/<id>/model_releases.json. Each release's model file
is copied to experiments/<id>/releases/model_v<N>.pt so a release stays
identical even if unlearning is later re-run; its SHA-256 is recorded.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.compute.archive import validate_experiment_id

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPERIMENTS_DIR = REPO_ROOT / "experiments"
REGISTRY_FILE = "model_releases.json"
RELEASES_DIR = "releases"

MODES = ("auto", "request")
MAX_GRACE_HOURS = 24 * 365
MAX_CLOCK_STEP_HOURS = 24 * 365
MAX_DEVICES = 100
MAX_EVENTS = 300
STATE_EVENTS = 40
MAX_NOTE_LENGTH = 200


# -- small helpers ---------------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _experiment_dir(experiments_dir: Path | None, experiment_id: str) -> Path:
    validate_experiment_id(experiment_id)
    folder = Path(experiments_dir or DEFAULT_EXPERIMENTS_DIR) / experiment_id
    if not folder.is_dir():
        raise FileNotFoundError(f'Experiment "{experiment_id}" was not found.')
    return folder


def _fresh_registry(experiment_id: str) -> dict[str, Any]:
    return {
        "schema": 1,
        "experiment_id": experiment_id,
        "clock_offset_hours": 0.0,
        "releases": [],
        "devices": {},
        "events": [],
    }


def _load(folder: Path, experiment_id: str) -> dict[str, Any]:
    path = folder / REGISTRY_FILE
    if not path.is_file():
        return _fresh_registry(experiment_id)
    try:
        registry = json.loads(path.read_text())
    except ValueError:
        raise ValueError("The stored release registry is unreadable. Reset it and publish again.") from None
    if not isinstance(registry, dict) or "releases" not in registry or "devices" not in registry:
        raise ValueError("The stored release registry is unreadable. Reset it and publish again.")
    registry.setdefault("events", [])
    registry.setdefault("clock_offset_hours", 0.0)
    return registry


def _save(folder: Path, registry: dict[str, Any]) -> None:
    registry["events"] = registry["events"][-MAX_EVENTS:]
    handle, temp_name = tempfile.mkstemp(dir=folder, prefix=".releases-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w") as out:
            json.dump(registry, out, indent=2)
        os.replace(temp_name, folder / REGISTRY_FILE)
    except BaseException:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def _now(registry: dict[str, Any], real_now: datetime | None) -> datetime:
    """The simulated clock: real time plus the offset the demo has advanced."""
    base = real_now or datetime.now(timezone.utc)
    return base + timedelta(hours=float(registry.get("clock_offset_hours", 0.0)))


def _event(registry: dict[str, Any], at: datetime, event: str, detail: str, device_id: str | None = None) -> None:
    registry["events"].append({"at": _iso(at), "event": event, "device_id": device_id, "detail": detail})


# -- policy rules ------------------------------------------------------------


def _effective_from(release: dict[str, Any]) -> str:
    """When older versions stop being allowed because of this release."""
    policy = release.get("policy")
    if policy and policy.get("mode") == "request" and release.get("deadline"):
        return release["deadline"]
    return release["published_at"]


def min_allowed_version(registry: dict[str, Any], now: datetime) -> int:
    allowed = 0
    for release in registry["releases"]:
        if _parse(_effective_from(release)) <= now:
            allowed = max(allowed, int(release["version"]))
    return allowed


def _latest(registry: dict[str, Any]) -> dict[str, Any] | None:
    return registry["releases"][-1] if registry["releases"] else None


def _device_status(registry: dict[str, Any], device: dict[str, Any], now: datetime) -> str:
    latest = _latest(registry)
    if latest is None or device["version"] >= latest["version"]:
        return "current"
    if device["version"] < min_allowed_version(registry, now):
        return "blocked"  # old version revoked; updates the moment the device is online
    return "update_requested"  # behind, but the old version is still allowed until the deadline


def _apply_update(registry: dict[str, Any], device_id: str, how: str, at: datetime) -> dict[str, Any]:
    device = registry["devices"][device_id]
    latest = _latest(registry)
    before = device["version"]
    device["version"] = latest["version"]
    device["pending_since"] = None
    device["last_check_in"] = _iso(at)
    detail = {
        "auto_updated": f"Updated v{before} to v{latest['version']} automatically.",
        "user_accepted": f"Accepted the request: v{before} to v{latest['version']}.",
        "forced_update": f"Deadline passed: updated v{before} to v{latest['version']} automatically.",
    }[how]
    _event(registry, at, how, detail, device_id)
    return {"device_id": device_id, "action": how, "version_before": before, "version_after": latest["version"]}


def _check_in_device(registry: dict[str, Any], device_id: str, now: datetime, at: datetime | None = None) -> dict[str, Any]:
    at = at or now
    device = registry["devices"][device_id]
    before = device["version"]
    if not device["online"]:
        return {"device_id": device_id, "action": "offline", "version_before": before, "version_after": before}

    latest = _latest(registry)
    if latest is None or before >= latest["version"]:
        device["last_check_in"] = _iso(at)
        return {"device_id": device_id, "action": "up_to_date", "version_before": before, "version_after": before}

    policy = latest.get("policy") or {"mode": "auto"}
    if policy["mode"] == "auto":
        return _apply_update(registry, device_id, "auto_updated", at)

    deadline = _parse(latest["deadline"])
    if now >= deadline:
        return _apply_update(registry, device_id, "forced_update", at)

    device["last_check_in"] = _iso(at)
    if not device.get("pending_since"):
        device["pending_since"] = _iso(at)
        _event(registry, at, "update_requested", f"Asked to update to v{latest['version']} before {latest['deadline']}.", device_id)
    return {"device_id": device_id, "action": "update_requested", "version_before": before, "version_after": before}


def _sweep(registry: dict[str, Any], now: datetime, previous: datetime) -> list[dict[str, Any]]:
    """After the clock moves: online devices still behind a request-mode release
    whose deadline has now passed are updated automatically, at the deadline."""
    latest = _latest(registry)
    results: list[dict[str, Any]] = []
    if latest is None:
        return results
    policy = latest.get("policy") or {}
    if policy.get("mode") != "request" or not latest.get("deadline"):
        return results
    deadline = _parse(latest["deadline"])
    if not (previous < deadline <= now):
        return results
    for device_id, device in registry["devices"].items():
        if device["online"] and device["version"] < latest["version"]:
            results.append(_apply_update(registry, device_id, "forced_update", deadline))
    return results


# -- state view -----------------------------------------------------------------


def _publish_blocker(folder: Path, registry: dict[str, Any]) -> str | None:
    status_path = folder / "unlearning_status.json"
    if not status_path.is_file():
        return "Run unlearning for this experiment first."
    try:
        status = json.loads(status_path.read_text())
    except ValueError:
        return "The stored unlearning result is unreadable."
    if status.get("status") != "complete":
        return "Unlearning for this experiment has not finished."
    if not (folder / "unlearning_final_model.pt").is_file():
        return "The unlearned model file is missing."
    if not registry["releases"]:
        return "Release the original model first: it is the version your devices already have."
    latest = registry["releases"][-1]
    if latest.get("kind") == "unlearned" and latest["sha256"] == _sha256_file(folder / "unlearning_final_model.pt"):
        return f"This unlearned model is already published as v{latest['version']}. Re-run unlearning to create a new one."
    return None


def _state(folder: Path, registry: dict[str, Any], now: datetime) -> dict[str, Any]:
    allowed = min_allowed_version(registry, now)
    latest = _latest(registry)
    devices = []
    for device_id in sorted(registry["devices"]):
        device = registry["devices"][device_id]
        devices.append(
            {
                "device_id": device_id,
                "version": device["version"],
                "online": device["online"],
                "status": _device_status(registry, device, now),
                "last_check_in": device.get("last_check_in"),
                "pending_since": device.get("pending_since"),
            }
        )
    counts = {"total": len(devices), "current": 0, "update_requested": 0, "blocked": 0, "offline": 0}
    for device in devices:
        counts[device["status"]] += 1
        if not device["online"]:
            counts["offline"] += 1
    releases = []
    for release in registry["releases"]:
        item = dict(release)
        item["allowed"] = release["version"] >= allowed
        item["effective_from"] = _effective_from(release)
        releases.append(item)
    hours_left = None
    if latest and (latest.get("policy") or {}).get("mode") == "request" and latest.get("deadline"):
        hours_left = round((_parse(latest["deadline"]) - now).total_seconds() / 3600, 2)
    return {
        "experiment_id": registry["experiment_id"],
        "now": _iso(now),
        "clock_offset_hours": float(registry.get("clock_offset_hours", 0.0)),
        "latest_version": latest["version"] if latest else None,
        "min_allowed_version": allowed,
        "hours_to_deadline": hours_left,
        "publish_blocker": _publish_blocker(folder, registry),
        "releases": releases,
        "devices": devices,
        "counts": counts,
        "events": list(reversed(registry["events"][-STATE_EVENTS:])),
    }


# -- public operations (each loads, changes, saves, returns the new state) ---------


def get_state(experiment_id: str, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    return _state(folder, registry, _now(registry, now))


def _snapshot(folder: Path, source_name: str, version: int) -> tuple[str, str]:
    target_dir = folder / RELEASES_DIR
    target_dir.mkdir(exist_ok=True)
    target = target_dir / f"model_v{version}.pt"
    shutil.copyfile(folder / source_name, target)
    return f"{RELEASES_DIR}/{target.name}", _sha256_file(target)


def release_original(experiment_id: str, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    """Version 1: the trained global model, i.e. what devices install first."""
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    if registry["releases"]:
        raise ValueError("The original model is already released.")
    if not (folder / "global_model.pt").is_file():
        raise ValueError("No trained global model exists for this experiment. Train it first.")
    current = _now(registry, now)
    model_file, digest = _snapshot(folder, "global_model.pt", 1)
    registry["releases"].append(
        {
            "version": 1,
            "kind": "original",
            "label": "Original global model",
            "model_file": model_file,
            "sha256": digest,
            "published_at": _iso(current),
            "forgotten_client_id": None,
            "policy": None,
            "deadline": None,
            "note": "",
        }
    )
    _event(registry, current, "release_published", "Released v1 (original global model).")
    _save(folder, registry)
    state = _state(folder, registry, current)
    state["result"] = {"published_version": 1}
    return state


def publish_release(
    experiment_id: str,
    mode: str,
    grace_hours: float | None = None,
    note: str = "",
    experiments_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("mode must be 'auto' or 'request'.")
    if mode == "request":
        try:
            grace = float(grace_hours)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError("A request-mode release needs grace_hours (a number).") from None
        if not (0 < grace <= MAX_GRACE_HOURS):
            raise ValueError(f"grace_hours must be greater than 0 and at most {MAX_GRACE_HOURS}.")
    else:
        grace = None
    note = (note or "").strip()
    if len(note) > MAX_NOTE_LENGTH:
        raise ValueError(f"The note is too long (max {MAX_NOTE_LENGTH} characters).")

    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    blocker = _publish_blocker(folder, registry)
    if blocker:
        raise ValueError(blocker)

    current = _now(registry, now)
    status = json.loads((folder / "unlearning_status.json").read_text())
    client_id = status.get("target_client_id")
    version = registry["releases"][-1]["version"] + 1
    model_file, digest = _snapshot(folder, "unlearning_final_model.pt", version)
    deadline = _iso(current + timedelta(hours=grace)) if grace is not None else None
    registry["releases"].append(
        {
            "version": version,
            "kind": "unlearned",
            "label": f"Unlearned model (client {client_id} removed)",
            "model_file": model_file,
            "sha256": digest,
            "published_at": _iso(current),
            "forgotten_client_id": client_id,
            "policy": {"mode": mode, "grace_hours": grace},
            "deadline": deadline,
            "note": note,
        }
    )

    updated = asked = 0
    for device_id, device in registry["devices"].items():
        if not device["online"]:
            continue  # handled when it reconnects
        if mode == "auto":
            _apply_update(registry, device_id, "auto_updated", current)
            updated += 1
        else:
            device["pending_since"] = _iso(current)
            asked += 1
    summary = f"Published v{version} ({'auto update' if mode == 'auto' else f'request, {grace:g} h to accept'})."
    if mode == "auto":
        summary += f" {updated} online device(s) updated now; offline devices update when they reconnect."
    else:
        summary += f" {asked} online device(s) asked to update; offline devices are asked when they reconnect."
    _event(registry, current, "release_published", summary)
    _save(folder, registry)
    state = _state(folder, registry, current)
    state["result"] = {"published_version": version, "mode": mode, "deadline": deadline}
    return state


def register_devices(experiment_id: str, count: int, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("count must be a whole number of at least 1.")
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    latest = _latest(registry)
    if latest is None:
        raise ValueError("Release the original model first, so the devices have something installed.")
    if len(registry["devices"]) + count > MAX_DEVICES:
        raise ValueError(f"At most {MAX_DEVICES} demo devices.")
    current = _now(registry, now)
    start = len(registry["devices"]) + 1
    for index in range(start, start + count):
        registry["devices"][f"device-{index:02d}"] = {
            "version": latest["version"],
            "online": True,
            "last_check_in": _iso(current),
            "pending_since": None,
        }
    _event(registry, current, "devices_added", f"Added {count} demo device(s) on v{latest['version']}.")
    _save(folder, registry)
    return _state(folder, registry, current)


def _require_device(registry: dict[str, Any], device_id: str) -> None:
    if device_id not in registry["devices"]:
        raise ValueError(f'Unknown device "{device_id}".')


def check_in(experiment_id: str, device_id: str | None = None, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    """One device, or every device when device_id is None. Offline devices do nothing."""
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    current = _now(registry, now)
    targets = sorted(registry["devices"]) if device_id is None else [device_id]
    if device_id is not None:
        _require_device(registry, device_id)
    results = [_check_in_device(registry, target, current) for target in targets]
    _save(folder, registry)
    state = _state(folder, registry, current)
    state["result"] = {"checked_in": results}
    return state


def accept_update(experiment_id: str, device_id: str, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    _require_device(registry, device_id)
    device = registry["devices"][device_id]
    if not device["online"]:
        raise ValueError("That device is offline, so it cannot accept the update yet.")
    current = _now(registry, now)
    latest = _latest(registry)
    if latest is None or device["version"] >= latest["version"]:
        result = {"device_id": device_id, "action": "up_to_date", "version_before": device["version"], "version_after": device["version"]}
    else:
        policy = latest.get("policy") or {"mode": "auto"}
        before_deadline = policy["mode"] == "request" and current < _parse(latest["deadline"])
        if before_deadline:
            result = _apply_update(registry, device_id, "user_accepted", current)
        else:
            result = _check_in_device(registry, device_id, current)
    _save(folder, registry)
    state = _state(folder, registry, current)
    state["result"] = {"checked_in": [result]}
    return state


def set_online(experiment_id: str, device_id: str, online: bool, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(online, bool):
        raise ValueError("online must be true or false.")
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    _require_device(registry, device_id)
    current = _now(registry, now)
    device = registry["devices"][device_id]
    results: list[dict[str, Any]] = []
    if device["online"] != online:
        device["online"] = online
        _event(registry, current, "device_online" if online else "device_offline", "Came online." if online else "Went offline.", device_id)
        if online:
            results.append(_check_in_device(registry, device_id, current))  # a reconnecting device checks in
    _save(folder, registry)
    state = _state(folder, registry, current)
    state["result"] = {"checked_in": results}
    return state


def advance_clock(experiment_id: str, hours: float, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    try:
        step = float(hours)
    except (TypeError, ValueError):
        raise ValueError("hours must be a number.") from None
    if not (0 < step <= MAX_CLOCK_STEP_HOURS):
        raise ValueError(f"hours must be greater than 0 and at most {MAX_CLOCK_STEP_HOURS}.")
    folder = _experiment_dir(experiments_dir, experiment_id)
    registry = _load(folder, experiment_id)
    previous = _now(registry, now)
    registry["clock_offset_hours"] = float(registry.get("clock_offset_hours", 0.0)) + step
    current = _now(registry, now)
    _event(registry, current, "clock_advanced", f"Simulated clock moved forward {step:g} h.")
    results = _sweep(registry, current, previous)
    _save(folder, registry)
    state = _state(folder, registry, current)
    state["result"] = {"checked_in": results}
    return state


def reset(experiment_id: str, experiments_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    folder = _experiment_dir(experiments_dir, experiment_id)
    (folder / REGISTRY_FILE).unlink(missing_ok=True)
    shutil.rmtree(folder / RELEASES_DIR, ignore_errors=True)
    registry = _fresh_registry(experiment_id)
    return _state(folder, registry, _now(registry, now))
