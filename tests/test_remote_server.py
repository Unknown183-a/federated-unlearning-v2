"""Phase 14b: the remote compute server + the client's long-job / sync behaviour.

Uses a stub backend, so no torch and no GPU: this tests the HTTP protocol,
auth, locking, keep-alive streaming, error mapping and folder sync.
"""
from __future__ import annotations

import base64
import io
import threading
import time
import urllib.error
import urllib.request
import zipfile

import pytest

from core.compute.archive import pack_dir_b64, unpack_b64_into, validate_experiment_id
from core.compute.base import BackendUnavailableError, NotSupportedError
from core.compute.remote_http_backend import RemoteHttpBackend, RemoteJobError
from core.compute.server import ComputeServer, main

KEY = "test-secret-key"


class StubBackend:
    def __init__(self, experiments_dir):
        self.experiments_dir = experiments_dir
        self.delay = 0.0
        self.calls = []

    def get_status(self):
        return {"available": True, "detail": "stub ready", "device": "cuda"}

    def load_experiment(self, experiment_id):
        return {"experiment_id": experiment_id, "dataset": "mnist"}

    def run_federated_training(self, experiment_id, **kwargs):
        self.calls.append(("run_federated_training", experiment_id, kwargs))
        time.sleep(self.delay)
        if kwargs.get("rounds") == -1:
            raise ValueError("rounds must be positive")
        if kwargs.get("rounds") == -2:
            raise NotSupportedError("read-only")
        folder = self.experiments_dir / experiment_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "fl_history.json").write_text('{"rounds": 2}')
        return {"final_accuracy": 0.9}


@pytest.fixture
def served(tmp_path, monkeypatch):
    server_dir = tmp_path / "server_experiments"
    local_dir = tmp_path / "local_experiments"
    server_dir.mkdir()
    local_dir.mkdir()
    backend = StubBackend(server_dir)
    server = ComputeServer(("127.0.0.1", 0), backend, server_dir, KEY, heartbeat_seconds=0.1)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("TEST_REMOTE_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("TEST_REMOTE_KEY", KEY)
    monkeypatch.delenv("REMOTE_SYNC", raising=False)
    client = RemoteHttpBackend("college_gpu", "Test", "TEST_REMOTE_URL", "TEST_REMOTE_KEY", experiments_dir=local_dir)
    try:
        yield client, backend, server_dir, local_dir, server
    finally:
        server.shutdown()
        thread.join(timeout=2)


def _post(url, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return urllib.request.urlopen(urllib.request.Request(url, data=b"{}", headers=headers, method="POST"), timeout=3)


# -- auth / status ---------------------------------------------------------


def test_status_works_with_key(served):
    client, *_ = served
    status = client.get_status()
    assert status["available"] is True
    assert status["device"] == "cuda"
    assert status["detail"] == "stub ready"


@pytest.mark.parametrize("key", [None, "wrong-key"])
def test_requests_without_the_right_key_get_401(served, monkeypatch, key):
    *_, server = served
    with pytest.raises(urllib.error.HTTPError) as err:
        _post(f"http://127.0.0.1:{server.server_port}/status", key)
    assert err.value.code == 401


def test_client_reports_rejected_key_as_unavailable_without_leaking_it(served, monkeypatch):
    client, *_ = served
    monkeypatch.setenv("TEST_REMOTE_KEY", "wrong-key")
    status = client.get_status()
    assert status["available"] is False
    assert "wrong-key" not in status["detail"] and KEY not in status["detail"]
    assert "API key" in status["detail"]


def test_read_op_and_bad_experiment_id(served):
    client, *_ = served
    assert client.load_experiment("exp-1")["dataset"] == "mnist"
    with pytest.raises(RemoteJobError):
        client.load_experiment("../etc")


# -- long jobs ---------------------------------------------------------------


def test_long_job_survives_heartbeats_and_returns_result(served):
    client, backend, *_ = served
    backend.delay = 0.45  # several heartbeats at 0.1 s
    result = client.run_federated_training("exp-1", rounds=2)
    assert result == {"final_accuracy": 0.9}


def test_job_failure_is_a_job_error_not_an_outage(served):
    client, *_ = served
    with pytest.raises(RemoteJobError, match="rounds must be positive"):
        client.run_federated_training("exp-1", rounds=-1)


def test_not_supported_is_preserved(served):
    client, *_ = served
    with pytest.raises(NotSupportedError):
        client.run_federated_training("exp-1", rounds=-2)


def test_second_job_while_busy_is_unavailable_409(served):
    client, backend, *_ = served
    backend.delay = 0.6
    first = {}
    t = threading.Thread(target=lambda: first.update(r=client.run_federated_training("exp-1", rounds=2)))
    t.start()
    time.sleep(0.2)
    with pytest.raises(BackendUnavailableError, match="already running"):
        client.run_federated_training("exp-2", rounds=2)
    t.join(timeout=5)
    assert first["r"] == {"final_accuracy": 0.9}


# -- folder sync -------------------------------------------------------------


def test_sync_pushes_inputs_and_pulls_results_back(served):
    client, backend, server_dir, local_dir, _ = served
    (local_dir / "exp-1").mkdir()
    (local_dir / "exp-1" / "partition.json").write_text('{"clients": 5}')

    client.run_federated_training("exp-1", rounds=2)

    assert (server_dir / "exp-1" / "partition.json").read_text() == '{"clients": 5}'  # pushed
    assert (local_dir / "exp-1" / "fl_history.json").read_text() == '{"rounds": 2}'  # pulled back


def test_sync_can_be_disabled(served, monkeypatch):
    client, backend, server_dir, local_dir, _ = served
    monkeypatch.setenv("REMOTE_SYNC", "0")
    (local_dir / "exp-1").mkdir()
    (local_dir / "exp-1" / "partition.json").write_text("{}")
    (server_dir / "exp-1").mkdir()
    client.run_federated_training("exp-1", rounds=2)
    assert not (server_dir / "exp-1" / "partition.json").exists()
    assert not (local_dir / "exp-1" / "fl_history.json").exists()


# -- archive safety ----------------------------------------------------------


def _zip_b64(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return base64.b64encode(buf.getvalue()).decode()


@pytest.mark.parametrize("name", ["../evil.txt", "/abs.txt", "a/../../evil.txt", "C:/evil.txt", "a\\b.txt"])
def test_unpack_rejects_unsafe_paths(tmp_path, name):
    with pytest.raises(ValueError):
        unpack_b64_into(_zip_b64({name: "x"}), tmp_path / "exp")
    assert not (tmp_path / "evil.txt").exists()


def test_unpack_rejects_garbage(tmp_path):
    with pytest.raises(ValueError):
        unpack_b64_into("not base64!!", tmp_path / "exp")
    with pytest.raises(ValueError):
        unpack_b64_into(base64.b64encode(b"plain bytes").decode(), tmp_path / "exp")


def test_pack_unpack_round_trip(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    (src / "a.json").write_text("1")
    (src / "sub" / "b.pt").write_bytes(b"\x00\x01")
    dst = tmp_path / "dst"
    assert unpack_b64_into(pack_dir_b64(src), dst) == 2
    assert (dst / "a.json").read_text() == "1"
    assert (dst / "sub" / "b.pt").read_bytes() == b"\x00\x01"


def test_experiment_id_validation():
    assert validate_experiment_id("exp-mv2d3hn6-zf17vh") == "exp-mv2d3hn6-zf17vh"
    for bad in ["", "..", "a/b", "../x", None, 5, "-x", "a" * 101, "a..b"]:
        with pytest.raises(ValueError):
            validate_experiment_id(bad)


# -- startup safety ----------------------------------------------------------


def test_server_refuses_to_start_without_a_key(monkeypatch):
    monkeypatch.delenv("COMPUTE_API_KEY", raising=False)
    assert main(["--port", "0"]) == 2


def test_no_auth_is_loopback_only(monkeypatch):
    monkeypatch.delenv("COMPUTE_API_KEY", raising=False)
    assert main(["--no-auth", "--host", "0.0.0.0", "--port", "0"]) == 2
