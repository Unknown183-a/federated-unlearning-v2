"""Phase 16: model releases and the auto / request-then-force update policy.

Pure standard-library logic, so no torch. The clock is controlled by passing
`now` and by the simulated-clock offset the module stores.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from core.distribution import releases as r
from core.distribution.cli import run as cli_run

T0 = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
EID = "exp-test-1"


@pytest.fixture
def exp(tmp_path):
    folder = tmp_path / EID
    folder.mkdir()
    (folder / "global_model.pt").write_bytes(b"original-weights")
    (folder / "unlearning_final_model.pt").write_bytes(b"unlearned-weights")
    (folder / "unlearning_status.json").write_text(json.dumps({"status": "complete", "target_client_id": 2}))
    return tmp_path


def ready(exp, devices=4):
    r.release_original(EID, exp, T0)
    r.register_devices(EID, devices, exp, T0)
    return exp


def versions(state):
    return {d["device_id"]: d["version"] for d in state["devices"]}


def statuses(state):
    return {d["device_id"]: d["status"] for d in state["devices"]}


# -- setup rules -----------------------------------------------------------


def test_cannot_publish_before_original_is_released(exp):
    with pytest.raises(ValueError, match="original model first"):
        r.publish_release(EID, "auto", None, "", exp, T0)


def test_cannot_add_devices_before_original_is_released(exp):
    with pytest.raises(ValueError, match="original model first"):
        r.register_devices(EID, 3, exp, T0)


def test_cannot_publish_when_unlearning_is_not_complete(exp):
    (exp / EID / "unlearning_status.json").write_text(json.dumps({"status": "running"}))
    r.release_original(EID, exp, T0)
    with pytest.raises(ValueError, match="not finished"):
        r.publish_release(EID, "auto", None, "", exp, T0)


def test_original_release_is_hashed_and_snapshotted(exp):
    state = r.release_original(EID, exp, T0)
    release = state["releases"][0]
    assert release["version"] == 1 and release["kind"] == "original"
    assert len(release["sha256"]) == 64
    assert (exp / EID / "releases" / "model_v1.pt").read_bytes() == b"original-weights"
    with pytest.raises(ValueError, match="already released"):
        r.release_original(EID, exp, T0)


def test_publish_validation(exp):
    ready(exp)
    with pytest.raises(ValueError, match="mode"):
        r.publish_release(EID, "sometimes", None, "", exp, T0)
    for bad in (None, "x", 0, -5, 10**9):
        with pytest.raises(ValueError):
            r.publish_release(EID, "request", bad, "", exp, T0)
    with pytest.raises(ValueError, match="too long"):
        r.publish_release(EID, "auto", None, "x" * 500, exp, T0)


def test_same_unlearned_model_cannot_be_published_twice(exp):
    ready(exp)
    r.publish_release(EID, "auto", None, "", exp, T0)
    state = r.get_state(EID, exp, T0)
    assert "already published" in state["publish_blocker"]
    with pytest.raises(ValueError, match="already published"):
        r.publish_release(EID, "auto", None, "", exp, T0)
    (exp / EID / "unlearning_final_model.pt").write_bytes(b"new-unlearned-weights")  # unlearning re-run
    assert r.get_state(EID, exp, T0)["publish_blocker"] is None


def test_release_is_a_frozen_copy_even_if_unlearning_is_rerun(exp):
    ready(exp)
    r.publish_release(EID, "auto", None, "", exp, T0)
    (exp / EID / "unlearning_final_model.pt").write_bytes(b"something-else")
    assert (exp / EID / "releases" / "model_v2.pt").read_bytes() == b"unlearned-weights"


# -- auto mode -------------------------------------------------------------------


def test_auto_updates_online_devices_immediately_and_revokes_old_version(exp):
    ready(exp)
    r.set_online(EID, "device-04", False, exp, T0)
    state = r.publish_release(EID, "auto", None, "", exp, T0)
    assert versions(state) == {"device-01": 2, "device-02": 2, "device-03": 2, "device-04": 1}
    assert state["min_allowed_version"] == 2
    assert statuses(state)["device-04"] == "blocked"  # old model revoked, waiting to reconnect


def test_auto_offline_device_updates_when_it_reconnects(exp):
    ready(exp)
    r.set_online(EID, "device-04", False, exp, T0)
    r.publish_release(EID, "auto", None, "", exp, T0)
    state = r.set_online(EID, "device-04", True, exp, T0)
    assert versions(state)["device-04"] == 2
    assert state["result"]["checked_in"][0]["action"] == "auto_updated"


# -- request mode ------------------------------------------------------------------


def test_request_mode_asks_but_does_not_change_devices_before_deadline(exp):
    ready(exp)
    state = r.publish_release(EID, "request", 48, "please update", exp, T0)
    assert set(versions(state).values()) == {1}
    assert set(statuses(state).values()) == {"update_requested"}
    assert state["min_allowed_version"] == 1  # old model still allowed during the grace period
    assert state["hours_to_deadline"] == 48.0
    assert state["releases"][-1]["deadline"] == "2026-10-13T12:00:00+00:00"


def test_device_can_accept_before_deadline(exp):
    ready(exp)
    r.publish_release(EID, "request", 48, "", exp, T0)
    state = r.accept_update(EID, "device-02", exp, T0)
    assert versions(state)["device-02"] == 2
    assert statuses(state)["device-02"] == "current"
    assert state["result"]["checked_in"][0]["action"] == "user_accepted"
    assert statuses(state)["device-01"] == "update_requested"


def test_online_devices_that_ignore_the_request_are_forced_at_the_deadline(exp):
    ready(exp)
    r.publish_release(EID, "request", 48, "", exp, T0)
    r.accept_update(EID, "device-01", exp, T0)
    state = r.advance_clock(EID, 24, exp, T0)  # halfway: still just a request
    assert versions(state) == {"device-01": 2, "device-02": 1, "device-03": 1, "device-04": 1}
    assert state["min_allowed_version"] == 1
    state = r.advance_clock(EID, 25, exp, T0)  # past the deadline
    assert set(versions(state).values()) == {2}
    assert state["min_allowed_version"] == 2
    forced = [e for e in state["events"] if e["event"] == "forced_update"]
    assert {e["device_id"] for e in forced} == {"device-02", "device-03", "device-04"}
    assert all(e["at"] == "2026-10-13T12:00:00+00:00" for e in forced)  # stamped at the deadline


def test_offline_device_is_blocked_after_deadline_then_forced_on_reconnect(exp):
    ready(exp)
    r.set_online(EID, "device-03", False, exp, T0)
    r.publish_release(EID, "request", 24, "", exp, T0)
    state = r.advance_clock(EID, 30, exp, T0)
    assert versions(state)["device-03"] == 1
    assert statuses(state)["device-03"] == "blocked"
    assert statuses(state)["device-01"] == "current"
    state = r.set_online(EID, "device-03", True, exp, T0)
    assert versions(state)["device-03"] == 2
    assert state["result"]["checked_in"][0]["action"] == "forced_update"


def test_reconnecting_before_deadline_gets_a_request_not_a_forced_update(exp):
    ready(exp)
    r.set_online(EID, "device-03", False, exp, T0)
    r.publish_release(EID, "request", 24, "", exp, T0)
    state = r.set_online(EID, "device-03", True, exp, T0)
    assert versions(state)["device-03"] == 1
    assert state["result"]["checked_in"][0]["action"] == "update_requested"


def test_accept_after_deadline_still_ends_up_updated(exp):
    ready(exp)
    r.set_online(EID, "device-02", False, exp, T0)
    r.publish_release(EID, "request", 1, "", exp, T0)
    r.advance_clock(EID, 5, exp, T0)
    r.set_online(EID, "device-02", True, exp, T0)  # forced on reconnect
    assert versions(r.get_state(EID, exp, T0))["device-02"] == 2


def test_offline_device_cannot_accept(exp):
    ready(exp)
    r.set_online(EID, "device-01", False, exp, T0)
    r.publish_release(EID, "request", 24, "", exp, T0)
    with pytest.raises(ValueError, match="offline"):
        r.accept_update(EID, "device-01", exp, T0)


def test_check_in_all_skips_offline_devices(exp):
    ready(exp)
    r.set_online(EID, "device-01", False, exp, T0)
    r.publish_release(EID, "request", 24, "", exp, T0)
    r.advance_clock(EID, 25, exp, T0)
    state = r.check_in(EID, None, exp, T0)
    actions = {x["device_id"]: x["action"] for x in state["result"]["checked_in"]}
    assert actions["device-01"] == "offline"


def test_second_unlearning_release_supersedes_the_first(exp):
    ready(exp)
    r.publish_release(EID, "request", 24, "", exp, T0)
    (exp / EID / "unlearning_final_model.pt").write_bytes(b"unlearned-again")
    r.publish_release(EID, "auto", None, "", exp, T0)
    state = r.get_state(EID, exp, T0)
    assert state["latest_version"] == 3
    r.check_in(EID, None, exp, T0)
    assert set(versions(r.get_state(EID, exp, T0)).values()) == {3}


# -- clock / registry housekeeping ---------------------------------------------------


def test_advance_clock_validation(exp):
    ready(exp)
    for bad in (0, -1, "x", None, 10**7):
        with pytest.raises(ValueError):
            r.advance_clock(EID, bad, exp, T0)


def test_unknown_device_and_bad_values(exp):
    ready(exp)
    with pytest.raises(ValueError, match="Unknown device"):
        r.check_in(EID, "device-99", exp, T0)
    with pytest.raises(ValueError, match="true or false"):
        r.set_online(EID, "device-01", "yes", exp, T0)  # type: ignore[arg-type]
    for bad in (0, -2, "3", True):
        with pytest.raises(ValueError):
            r.register_devices(EID, bad, exp, T0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="At most"):
        r.register_devices(EID, 500, exp, T0)


def test_reset_clears_everything(exp):
    ready(exp)
    r.publish_release(EID, "auto", None, "", exp, T0)
    state = r.reset(EID, exp, T0)
    assert state["releases"] == [] and state["devices"] == []
    assert not (exp / EID / "releases").exists()


def test_corrupt_registry_is_reported_not_crashed(exp):
    (exp / EID / "model_releases.json").write_text("{not json")
    with pytest.raises(ValueError, match="unreadable"):
        r.get_state(EID, exp, T0)


def test_experiment_must_exist_and_id_must_be_valid(exp):
    with pytest.raises(FileNotFoundError):
        r.get_state("exp-nope", exp, T0)
    with pytest.raises(ValueError, match="Invalid experiment id"):
        r.get_state("../etc", exp, T0)


def test_state_persists_between_calls(exp):
    ready(exp)
    r.publish_release(EID, "request", 12, "n", exp, T0)
    state = r.get_state(EID, exp, T0)
    assert state["releases"][-1]["note"] == "n"
    assert state["counts"]["update_requested"] == 4


# -- CLI --------------------------------------------------------------------------------


def test_cli_returns_json_state_and_reports_input_mistakes_as_errors(exp, capsys):
    from core.distribution.cli import main

    assert main(["--experiments-dir", str(exp), "release-original", "--experiment-id", EID]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["latest_version"] == 1

    assert main(["--experiments-dir", str(exp), "publish", "--experiment-id", EID, "--mode", "nope"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "mode must be" in out["error"]
