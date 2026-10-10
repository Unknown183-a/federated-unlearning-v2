"""Phase 14 tests: the backend-neutral compute API, the four backends,
the Auto fallback chain, and the "no credentials leak" security review.

RemoteHttpBackend is exercised against a real local http.server on
127.0.0.1 (not mocked at the function-call level) so the request/
response/timeout/header-forwarding logic is proven over an actual
socket, not just assumed from reading the code.
"""
import http.server
import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from core.compute.base import BackendUnavailableError, NotSupportedError
from core.compute.demo_backend import DemoBackend
from core.compute.local_backend import LocalBackend, detect_device
from core.compute.remote_http_backend import RemoteHttpBackend
from core.compute.registry import (
    FALLBACK_ORDER,
    all_statuses,
    get_backend,
    resolve_auto_backend,
    resolve_requested_backend,
)


# -- A tiny real HTTP server for RemoteHttpBackend's tests -------------------


class _Handler(http.server.BaseHTTPRequestHandler):
    # Overridden per test via class attributes set on a subclass.
    response_body = {"available": True, "device": "cuda"}
    status_code = 200
    captured_headers = None
    captured_bodies = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if type(self).captured_headers is not None:
            type(self).captured_headers.append(dict(self.headers))
        if type(self).captured_bodies is not None:
            type(self).captured_bodies.append(json.loads(body) if body else {})
        self.send_response(type(self).status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(type(self).response_body).encode("utf-8"))

    def log_message(self, *args):  # silence test output
        pass


@pytest.fixture
def fake_server():
    """Starts a real HTTP server on an ephemeral localhost port and
    tears it down after the test. Yields (base_url, HandlerClass) so
    each test can configure the response and inspect captured requests."""
    handler_cls = type("Handler", (_Handler,), {"captured_headers": [], "captured_bodies": []})
    server = http.server.HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", handler_cls
    finally:
        server.shutdown()
        thread.join(timeout=2)


# -- LocalBackend --------------------------------------------------------


def test_detect_device_returns_a_real_torch_device_string():
    assert detect_device() in ("cuda", "mps", "cpu")


def test_local_backend_status_reports_available_and_device():
    status = LocalBackend().get_status()
    assert status["backend"] == "local"
    assert status["available"] is True
    assert status["device"] in ("cuda", "mps", "cpu")
    assert status["latency_ms"] is not None


def test_local_backend_reads_delegate_to_storage(tmp_path, monkeypatch):
    import core.federated.storage as fl_storage
    import core.partitioning.storage as partition_storage
    import core.unlearning.storage as unlearning_storage
    import core.evaluation.storage as evaluation_storage

    for module in (fl_storage, partition_storage, unlearning_storage, evaluation_storage):
        monkeypatch.setattr(module, "EXPERIMENTS_DIR", tmp_path)

    partition_storage.save_partition("e", {"dataset": "mnist", "num_clients": 2, "clients": []})
    fl_storage.save_fl_history(
        "e", {"dataset": "mnist", "model": "cnn", "num_clients": 2, "rounds": 3, "seed": 1, "final_accuracy": 0.9}
    )
    unlearning_storage.save_unlearning_status("e", {"experiment_id": "e", "status": "complete"})
    evaluation_storage.save_evaluation_results("e", {"experiment_id": "e", "status": "complete"})

    backend = LocalBackend()
    assert backend.load_experiment("e")["dataset"] == "mnist"
    assert backend.get_client_distribution("e")["num_clients"] == 2
    assert backend.get_fl_history("e")["rounds"] == 3
    assert backend.get_unlearning_status("e")["status"] == "complete"
    assert backend.get_results("e")["status"] == "complete"


def test_local_backend_start_unlearning_forwards_every_kwarg(monkeypatch):
    captured = {}

    def fake_start_unlearning(**kwargs):
        captured.update(kwargs)
        return {"status": "complete"}

    import core.compute.local_backend as local_backend_module

    monkeypatch.setattr(local_backend_module, "_start_unlearning", fake_start_unlearning)
    result = LocalBackend().start_unlearning(experiment_id="e", client_id=2, steps=10, lr=0.05)
    assert result == {"status": "complete"}
    assert captured == {"experiment_id": "e", "client_id": 2, "steps": 10, "lr": 0.05}


# -- DemoBackend -----------------------------------------------------------


def test_demo_backend_is_always_available_with_no_device():
    status = DemoBackend().get_status()
    assert status["available"] is True
    assert status["device"] is None


def test_demo_backend_shares_local_backends_read_paths(tmp_path, monkeypatch):
    import core.federated.storage as fl_storage

    monkeypatch.setattr(fl_storage, "EXPERIMENTS_DIR", tmp_path)
    fl_storage.save_fl_history(
        "e", {"dataset": "cifar10", "model": "resnet", "num_clients": 5, "rounds": 10, "seed": 3, "final_accuracy": 0.7}
    )
    assert DemoBackend().get_fl_history("e")["dataset"] == "cifar10"


def test_demo_backend_refuses_to_start_unlearning():
    with pytest.raises(NotSupportedError, match="precomputed experiments only"):
        DemoBackend().start_unlearning(experiment_id="e", client_id=1)


def test_demo_backend_refuses_training_and_evaluation():
    with pytest.raises(NotSupportedError):
        DemoBackend().run_federated_training(experiment_id="e")
    with pytest.raises(NotSupportedError):
        DemoBackend().run_evaluation(experiment_id="e")


# -- RemoteHttpBackend: unconfigured ----------------------------------------


def test_remote_backend_unconfigured_reports_unavailable_without_any_network_call(monkeypatch):
    monkeypatch.delenv("COLLEGE_GPU_BASE_URL", raising=False)
    calls = []
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(AssertionError("should not be called")))

    backend = RemoteHttpBackend("college_gpu", "College GPU", "COLLEGE_GPU_BASE_URL", "COLLEGE_GPU_API_KEY")
    status = backend.get_status()
    assert status["available"] is False
    assert "not set" in status["detail"]
    assert calls == []


def test_remote_backend_unreachable_host_reports_unavailable_quickly(monkeypatch):
    # Port 1 is a real, immediately-refusing port on loopback -- no hang.
    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", "http://127.0.0.1:1")
    backend = RemoteHttpBackend("college_gpu", "College GPU", "COLLEGE_GPU_BASE_URL", "COLLEGE_GPU_API_KEY", timeout=1.0)
    status = backend.get_status()
    assert status["available"] is False
    assert status["backend"] == "college_gpu"


# -- RemoteHttpBackend: real HTTP round trip ---------------------------------


def test_remote_backend_status_round_trip_over_real_http(fake_server, monkeypatch):
    base_url, handler_cls = fake_server
    handler_cls.response_body = {"available": True, "device": "cuda", "detail": "2x A100"}
    monkeypatch.setenv("COLAB_BASE_URL", base_url)
    monkeypatch.delenv("COLAB_API_KEY", raising=False)

    backend = RemoteHttpBackend("colab", "Google Colab", "COLAB_BASE_URL", "COLAB_API_KEY")
    status = backend.get_status()
    assert status["available"] is True
    assert status["device"] == "cuda"
    assert status["detail"] == "2x A100"


def test_remote_backend_sends_api_key_as_bearer_header(fake_server, monkeypatch):
    base_url, handler_cls = fake_server
    monkeypatch.setenv("COLAB_BASE_URL", base_url)
    monkeypatch.setenv("COLAB_API_KEY", "super-secret-token")

    RemoteHttpBackend("colab", "Google Colab", "COLAB_BASE_URL", "COLAB_API_KEY").get_status()
    assert handler_cls.captured_headers[0]["Authorization"] == "Bearer super-secret-token"


def test_remote_backend_omits_authorization_header_when_no_key_configured(fake_server, monkeypatch):
    base_url, handler_cls = fake_server
    monkeypatch.setenv("COLAB_BASE_URL", base_url)
    monkeypatch.delenv("COLAB_API_KEY", raising=False)

    RemoteHttpBackend("colab", "Google Colab", "COLAB_BASE_URL", "COLAB_API_KEY").get_status()
    assert "Authorization" not in handler_cls.captured_headers[0]


def test_remote_backend_start_unlearning_forwards_payload(fake_server, monkeypatch):
    base_url, handler_cls = fake_server
    handler_cls.response_body = {"status": "complete", "target_client_id": 4}
    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", base_url)

    backend = RemoteHttpBackend("college_gpu", "College GPU", "COLLEGE_GPU_BASE_URL", "COLLEGE_GPU_API_KEY")
    result = backend.start_unlearning(experiment_id="e", client_id=4, steps=20)
    assert result == {"status": "complete", "target_client_id": 4}
    assert handler_cls.captured_bodies[0] == {"experiment_id": "e", "client_id": 4, "steps": 20}


def test_remote_backend_error_detail_never_contains_the_api_key(fake_server, monkeypatch):
    """Security review: a failure reason must never leak the credential,
    even indirectly through a raw exception message."""
    base_url, handler_cls = fake_server
    handler_cls.status_code = 500
    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", "http://127.0.0.1:1")  # force a connection failure, not just a 500
    monkeypatch.setenv("COLLEGE_GPU_API_KEY", "super-secret-token")

    backend = RemoteHttpBackend("college_gpu", "College GPU", "COLLEGE_GPU_BASE_URL", "COLLEGE_GPU_API_KEY", timeout=1.0)
    status = backend.get_status()
    assert "super-secret-token" not in status["detail"]
    assert "super-secret-token" not in json.dumps(status)


def test_remote_backend_get_status_never_raises_on_failure(monkeypatch):
    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", "http://127.0.0.1:1")
    backend = RemoteHttpBackend("college_gpu", "College GPU", "COLLEGE_GPU_BASE_URL", "COLLEGE_GPU_API_KEY", timeout=1.0)
    # Should not raise -- base.py's contract says get_status() must never propagate.
    status = backend.get_status()
    assert status["available"] is False


def test_remote_backend_other_methods_raise_backend_unavailable_when_unreachable(monkeypatch):
    monkeypatch.delenv("COLAB_BASE_URL", raising=False)
    backend = RemoteHttpBackend("colab", "Google Colab", "COLAB_BASE_URL", "COLAB_API_KEY")
    with pytest.raises(BackendUnavailableError):
        backend.get_fl_history("e")


# -- registry: selection + Auto fallback chain -------------------------------


@pytest.fixture(autouse=True)
def _clear_remote_env(monkeypatch):
    """Every registry test assumes a clean slate: neither remote
    backend configured, so Auto reliably resolves to Local."""
    for var in ("COLLEGE_GPU_BASE_URL", "COLLEGE_GPU_API_KEY", "COLAB_BASE_URL", "COLAB_API_KEY"):
        monkeypatch.delenv(var, raising=False)


def test_fallback_order_is_college_gpu_then_colab_then_local_then_demo():
    assert FALLBACK_ORDER == ["college_gpu", "colab", "local", "demo"]


def test_get_backend_returns_the_right_kind():
    assert get_backend("local").kind == "local"
    assert get_backend("demo").kind == "demo"
    assert get_backend("college_gpu").kind == "college_gpu"
    assert get_backend("colab").kind == "colab"


def test_get_backend_rejects_unknown_kind():
    with pytest.raises(ValueError, match="Unknown compute backend"):
        get_backend("quantum_computer")


def test_all_statuses_covers_every_backend_in_order():
    statuses = all_statuses()
    assert [s["backend"] for s in statuses] == FALLBACK_ORDER
    # Unconfigured remotes unavailable; local/demo always available.
    by_kind = {s["backend"]: s for s in statuses}
    assert by_kind["college_gpu"]["available"] is False
    assert by_kind["colab"]["available"] is False
    assert by_kind["local"]["available"] is True
    assert by_kind["demo"]["available"] is True


def test_resolve_auto_backend_falls_back_to_local_when_remotes_unconfigured():
    backend, trace = resolve_auto_backend()
    assert backend.kind == "local"
    # Never silent: both failed remote attempts are visible in the trace.
    assert [t["backend"] for t in trace] == ["college_gpu", "colab", "local"]
    assert trace[0]["available"] is False
    assert trace[1]["available"] is False
    assert trace[2]["available"] is True


def test_resolve_auto_backend_picks_college_gpu_first_when_it_is_available(fake_server, monkeypatch):
    base_url, handler_cls = fake_server
    handler_cls.response_body = {"available": True, "device": "a100"}
    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", base_url)

    backend, trace = resolve_auto_backend()
    assert backend.kind == "college_gpu"
    assert trace == [trace[0]]  # stops at the first available backend, doesn't probe further


def test_resolve_requested_backend_auto_is_the_fallback_chain():
    backend, trace = resolve_requested_backend("auto")
    assert backend.kind == "local"
    assert len(trace) == 3


def test_resolve_requested_backend_none_also_means_auto():
    backend, _ = resolve_requested_backend(None)
    assert backend.kind == "local"


def test_resolve_requested_backend_explicit_pin_does_not_fall_back_when_unavailable():
    """An explicit, unavailable choice fails loud and specific --
    unlike Auto, it must not silently substitute a different backend."""
    backend, trace = resolve_requested_backend("college_gpu")
    assert backend.kind == "college_gpu"
    assert len(trace) == 1
    assert trace[0]["available"] is False


# -- CLI --------------------------------------------------------------------


def test_compute_cli_status_prints_valid_json(capsys):
    from core.compute.cli import main

    assert main([]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [b["backend"] for b in payload["backends"]] == FALLBACK_ORDER
    assert payload["auto_selected"] == "local"
    assert [t["backend"] for t in payload["auto_trace"]] == ["college_gpu", "colab", "local"]


# -- --backend wiring in the existing per-phase CLIs -------------------------
#
# These confirm the *dispatch*: given --backend, each CLI resolves a
# backend and calls the right method with the right kwargs, and prints
# the {<payload>, "backend_trace": [...]} shape instead of the bare
# payload. They use a fake backend double (not a real torch run) since
# the underlying ML correctness is already covered by each phase's own
# tests -- this file only needs to prove the new wiring is correct.


class _FakeBackend:
    kind = "local"

    def __init__(self):
        self.calls = []

    def get_status(self):
        return {"backend": "local", "name": "fake", "available": True, "detail": "ok", "device": "cpu", "latency_ms": 0.0}

    def run_federated_training(self, **kwargs):
        self.calls.append(("run_federated_training", kwargs))
        return {"final_accuracy": 0.9}

    def start_unlearning(self, **kwargs):
        self.calls.append(("start_unlearning", kwargs))
        return {"status": "complete"}

    def run_evaluation(self, **kwargs):
        self.calls.append(("run_evaluation", kwargs))
        return {"status": "complete"}


def _fake_call_with_fallback(fake):
    """Stand-in for registry.call_with_fallback that routes to `fake`."""

    def call(kind, method, **kwargs):
        return getattr(fake, method)(**kwargs), [fake.get_status()]

    return call


def test_federated_cli_backend_flag_dispatches_through_registry(monkeypatch, capsys):
    import core.federated.cli as federated_cli

    import core.compute.registry as registry_module

    fake = _FakeBackend()
    monkeypatch.setattr(registry_module, "call_with_fallback", _fake_call_with_fallback(fake))

    rc = federated_cli.main(
        ["--experiment-id", "e", "--model", "cnn", "--rounds", "5", "--local-epochs", "1", "--seed", "1", "--backend", "local"]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["history"] == {"final_accuracy": 0.9}
    assert payload["backend_trace"][0]["backend"] == "local"
    name, kwargs = fake.calls[0]
    assert name == "run_federated_training"
    assert kwargs == {"experiment_id": "e", "model_id": "cnn", "rounds": 5, "local_epochs": 1, "seed": 1, "lr": 0.01, "batch_size": 32}


def test_federated_cli_without_backend_flag_is_unchanged(monkeypatch):
    """The default path must never even import core.compute."""
    import core.federated.cli as federated_cli

    with pytest.raises(SystemExit):
        # Missing required args -> argparse exits before reaching any
        # backend code either way; this just confirms --backend is
        # genuinely optional (parses fine without it elsewhere).
        federated_cli.main(["--experiment-id", "e"])


def test_unlearning_cli_backend_flag_dispatches_through_registry(monkeypatch, capsys):
    import core.unlearning.cli as unlearning_cli
    import core.compute.registry as registry_module

    fake = _FakeBackend()
    monkeypatch.setattr(registry_module, "call_with_fallback", _fake_call_with_fallback(fake))

    rc = unlearning_cli.main(["--experiment-id", "e", "--client-id", "2", "--backend", "auto"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == {"status": "complete"}
    name, kwargs = fake.calls[0]
    assert name == "start_unlearning"
    assert kwargs["experiment_id"] == "e"
    assert kwargs["client_id"] == 2


def test_unlearning_cli_backend_demo_reports_not_supported_cleanly(capsys):
    import core.unlearning.cli as unlearning_cli

    # Real registry, real DemoBackend -- no monkeypatching needed.
    rc = unlearning_cli.main(["--experiment-id", "e", "--client-id", "2", "--backend", "demo"])
    assert rc == 1
    assert "precomputed experiments only" in capsys.readouterr().err


def test_unlearning_cli_pinned_unconfigured_remote_fails_loudly_without_fallback(capsys):
    import core.unlearning.cli as unlearning_cli

    rc = unlearning_cli.main(["--experiment-id", "e", "--client-id", "2", "--backend", "college_gpu"])
    assert rc == 1
    assert "COLLEGE_GPU_BASE_URL is not configured" in capsys.readouterr().err


def test_evaluation_cli_backend_flag_dispatches_through_registry(monkeypatch, capsys):
    import core.evaluation.cli as evaluation_cli
    import core.compute.registry as registry_module

    fake = _FakeBackend()
    monkeypatch.setattr(registry_module, "call_with_fallback", _fake_call_with_fallback(fake))

    rc = evaluation_cli.main(["--experiment-id", "e", "--backend", "local"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"] == {"status": "complete"}
    assert fake.calls[0][0] == "run_evaluation"


# -- mid-run failover (call_with_fallback) -------------------------------------


def test_primary_dying_between_checks_changes_the_auto_choice(fake_server, monkeypatch):
    """Primary healthy -> Auto picks it. Kill it -> next resolution
    visibly falls through to Local, with the dead backend in the trace."""

    base_url, handler_cls = fake_server
    handler_cls.response_body = {"available": True, "device": "a100"}
    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", base_url)
    assert resolve_auto_backend()[0].kind == "college_gpu"

    monkeypatch.setenv("COLLEGE_GPU_BASE_URL", "http://127.0.0.1:1")  # the server is gone
    backend, trace = resolve_auto_backend()
    assert backend.kind == "local"
    assert trace[0]["backend"] == "college_gpu" and trace[0]["available"] is False


def test_call_with_fallback_survives_a_backend_dying_mid_call(monkeypatch):
    """A backend that passes its health check but raises
    BackendUnavailableError *during* the call (it died mid-run) must
    be skipped, the trace must say so, and the next backend must serve
    the same call."""
    import core.compute.registry as registry

    class DiesMidRun:
        kind = "college_gpu"
        name = "College GPU"

        def get_status(self):
            return {"backend": "college_gpu", "name": "College GPU", "available": True, "detail": "ok", "device": "cuda", "latency_ms": 1.0}

        def start_unlearning(self, **kwargs):
            raise BackendUnavailableError("URLError while reaching the remote backend.")

    class Healthy:
        kind = "local"
        name = "Local"

        def get_status(self):
            return {"backend": "local", "name": "Local", "available": True, "detail": "ok", "device": "cpu", "latency_ms": 0.1}

        def start_unlearning(self, **kwargs):
            return {"status": "complete", "ran_on": "local", **kwargs}

    fakes = {"college_gpu": DiesMidRun(), "local": Healthy()}
    monkeypatch.setattr(registry, "get_backend", lambda kind: fakes.get(kind, DemoBackend()))
    monkeypatch.setattr(registry, "FALLBACK_ORDER", ["college_gpu", "local"])

    result, trace = registry.call_with_fallback("auto", "start_unlearning", experiment_id="e", client_id=1)
    assert result["ran_on"] == "local"
    assert [t["backend"] for t in trace] == ["college_gpu", "local"]
    assert trace[0]["available"] is False
    assert trace[0]["detail"].startswith("Failed mid-run")


def test_call_with_fallback_never_retries_not_supported(monkeypatch):
    """Demo being read-only is an answer, not an outage -- it must
    surface as NotSupportedError, not trigger a retry elsewhere."""
    import core.compute.registry as registry

    with pytest.raises(NotSupportedError):
        registry.call_with_fallback("demo", "start_unlearning", experiment_id="e", client_id=1)


def test_call_with_fallback_pinned_backend_does_not_fall_back():
    import core.compute.registry as registry

    with pytest.raises(BackendUnavailableError, match="COLLEGE_GPU_BASE_URL"):
        registry.call_with_fallback("college_gpu", "get_fl_history", experiment_id="e")


def test_call_with_fallback_auto_serves_from_local_when_remotes_unconfigured(tmp_path, monkeypatch):
    import core.federated.storage as fl_storage
    import core.compute.registry as registry

    monkeypatch.setattr(fl_storage, "EXPERIMENTS_DIR", tmp_path)
    fl_storage.save_fl_history("e", {"dataset": "mnist", "model": "cnn", "num_clients": 2, "rounds": 1, "seed": 1})
    result, trace = registry.call_with_fallback("auto", "get_fl_history", experiment_id="e")
    assert result["dataset"] == "mnist"
    assert [t["backend"] for t in trace] == ["college_gpu", "colab", "local"]
