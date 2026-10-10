"""Generic HTTP-based remote compute backend (Phase 14).

College GPU and Google Colab share one implementation: both are "some
machine running this project's core/ code, reachable over HTTP,
exposing the same seven-method contract as every other backend." The
only difference between them is which environment variables name the
base URL and (optional) API key -- so both are just differently
-configured instances of this one class rather than two near-duplicate
files.

Security (Phase 14's "no credentials in the frontend" review):
  * The base URL and API key are read from environment variables by
    *name* at call time, never passed in as literal values and never
    cached on the instance -- nothing credential-shaped is ever held
    in a Python object that a status response or an exception's repr
    could accidentally serialize.
  * If the base-URL env var isn't set, get_status() returns
    unavailable immediately with no network call at all -- an
    unconfigured remote backend can't leak a stray request anywhere,
    and can't be probed by timing to see whether a key is set.
  * No error message ever includes the API key's value, the raw
    exception text from the HTTP client (which can echo request
    headers back), or the full URL with any query string -- see
    _safe_detail().
  * This class is instantiated only by core/compute/registry.py, which
    nothing in frontend/ or backend/ (the Express layer) can reach
    directly -- Express only ever sees this backend's get_status()
    JSON and whatever experiment data it returns, never the env var
    names or values themselves.

Wire protocol (what a real College GPU / Colab server is expected to
implement): plain JSON over HTTP, one path per ComputeBackend method,
below each method's request/response shape.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.compute.archive import pack_dir_b64, unpack_b64_into, validate_experiment_id
from core.compute.base import BackendUnavailableError, ComputeBackend, NotSupportedError

DEFAULT_TIMEOUT_SECONDS = 2.0
# Training / unlearning / evaluation can run for many minutes. The server sends
# a keep-alive byte every ~15 s, so this is a per-read socket timeout, not a cap
# on the whole run. Override with REMOTE_RUN_TIMEOUT_SECONDS.
DEFAULT_RUN_TIMEOUT_SECONDS = 600.0
DEFAULT_EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"


class RemoteJobError(ValueError):
    """The remote server ran the job and the job itself failed (bad input,
    missing file, out of memory...). Not an outage, so Auto mode does not retry
    it on another backend. Carries the server's short message, never a
    credential."""


class RemoteHttpBackend(ComputeBackend):
    def __init__(
        self,
        kind: str,
        name: str,
        base_url_env: str,
        api_key_env: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        experiments_dir: Path | None = None,
    ):
        self.kind = kind
        self.name = name
        self._base_url_env = base_url_env
        self._api_key_env = api_key_env
        self._timeout = timeout
        self._experiments_dir = Path(experiments_dir) if experiments_dir else DEFAULT_EXPERIMENTS_DIR

    def _base_url(self) -> str | None:
        url = os.environ.get(self._base_url_env)
        return url.rstrip("/") if url else None

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get(self._api_key_env)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    @staticmethod
    def _safe_detail(exc: Exception) -> str:
        """A failure reason safe to show in the UI -- the exception
        *type*, never its message (which, for an HTTP client, can
        include request headers, the resolved URL, or proxy details)."""
        return f"{type(exc).__name__} while reaching the remote backend."

    @staticmethod
    def _run_timeout() -> float:
        try:
            return float(os.environ.get("REMOTE_RUN_TIMEOUT_SECONDS", DEFAULT_RUN_TIMEOUT_SECONDS))
        except ValueError:
            return DEFAULT_RUN_TIMEOUT_SECONDS

    @staticmethod
    def _http_error(exc: urllib.error.HTTPError) -> Exception:
        """Map an HTTP error status to the right exception. Uses only the
        status code and our own server's short JSON `error` text."""
        code = exc.code
        message = ""
        try:
            message = str(json.loads(exc.read().decode("utf-8")).get("error", ""))[:300]
        except Exception:  # noqa: BLE001 - body is optional
            pass
        if code in (401, 403):
            return BackendUnavailableError(f"The remote backend rejected the API key (HTTP {code}).")
        if code in (409, 502, 503, 504, 520, 521, 522, 523, 524, 530):
            return BackendUnavailableError(message or f"The remote backend is not ready (HTTP {code}).")
        if code == 501:
            return NotSupportedError(message or "The remote backend does not support this operation.")
        return RemoteJobError(message or f"The remote request failed (HTTP {code}).")

    @staticmethod
    def _job_error(info: dict[str, Any]) -> Exception:
        message = str(info.get("message", ""))[:300]
        kind = str(info.get("type", "Error"))
        if kind == "NotSupportedError":
            return NotSupportedError(message)
        return RemoteJobError(f"{kind}: {message}" if message else kind)

    def _request(self, path: str, payload: dict[str, Any] | None, timeout: float | None = None) -> dict[str, Any]:
        base_url = self._base_url()
        if not base_url:
            raise BackendUnavailableError(f"{self._base_url_env} is not configured.")

        body = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}{path}",
            data=body,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout or self._timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise self._http_error(exc) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise BackendUnavailableError(self._safe_detail(exc)) from exc
        if isinstance(data, dict) and "_remote_error" in data:
            raise self._job_error(data["_remote_error"])
        return data

    def _run_job(self, path: str, experiment_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Run a long job remotely. If this machine has the experiment folder
        (and REMOTE_SYNC is not 0) the folder is sent up first and the
        server's copy is brought back afterwards, so later steps -- and the UI,
        which reads experiments/<id>/ locally -- see the new files."""
        validate_experiment_id(experiment_id)
        timeout = self._run_timeout()
        folder = self._experiments_dir / experiment_id
        sync = os.environ.get("REMOTE_SYNC", "1") != "0" and folder.is_dir()

        if sync:
            self._request("/upload_experiment", {"experiment_id": experiment_id, "archive_b64": pack_dir_b64(folder)}, timeout)
        result = self._request(path, payload, timeout)
        if sync:
            try:
                archive = self._request("/download_experiment", {"experiment_id": experiment_id}, timeout)
                unpack_b64_into(archive["archive_b64"], folder)
            except (BackendUnavailableError, KeyError, ValueError) as exc:
                raise RemoteJobError(
                    "The remote run finished, but its files could not be downloaded "
                    f"({type(exc).__name__}). They are still on the remote machine."
                ) from None
        return result

    def get_status(self) -> dict[str, Any]:
        started = time.monotonic()
        base_url = self._base_url()
        if not base_url:
            return {
                "backend": self.kind,
                "name": self.name,
                "available": False,
                "detail": f"Not configured ({self._base_url_env} is not set).",
                "device": None,
                "latency_ms": None,
            }
        try:
            result = self._request("/status", {})
            return {
                "backend": self.kind,
                "name": self.name,
                "available": bool(result.get("available", True)),
                "detail": result.get("detail", "Reachable."),
                "device": result.get("device"),
                "latency_ms": (time.monotonic() - started) * 1000,
            }
        except BackendUnavailableError as exc:
            return {
                "backend": self.kind,
                "name": self.name,
                "available": False,
                "detail": str(exc),
                "device": None,
                "latency_ms": (time.monotonic() - started) * 1000,
            }

    def load_experiment(self, experiment_id: str) -> dict[str, Any]:
        return self._request("/load_experiment", {"experiment_id": experiment_id})

    def get_client_distribution(self, experiment_id: str) -> dict[str, Any]:
        return self._request("/get_client_distribution", {"experiment_id": experiment_id})

    def get_fl_history(self, experiment_id: str) -> dict[str, Any]:
        return self._request("/get_fl_history", {"experiment_id": experiment_id})

    def start_unlearning(self, experiment_id: str, client_id: int, **kwargs: Any) -> dict[str, Any]:
        return self._run_job("/start_unlearning", experiment_id, {"experiment_id": experiment_id, "client_id": client_id, **kwargs})

    def get_unlearning_status(self, experiment_id: str) -> dict[str, Any]:
        return self._request("/get_unlearning_status", {"experiment_id": experiment_id})

    def get_results(self, experiment_id: str) -> dict[str, Any]:
        return self._request("/get_results", {"experiment_id": experiment_id})

    def run_federated_training(self, experiment_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._run_job("/run_federated_training", experiment_id, {"experiment_id": experiment_id, **kwargs})

    def run_evaluation(self, experiment_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._run_job("/run_evaluation", experiment_id, {"experiment_id": experiment_id, **kwargs})
