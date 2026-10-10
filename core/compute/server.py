"""Remote compute server (Phase 14b) -- run this on the College GPU box or in Colab.

    export COMPUTE_API_KEY=<long random string>
    python -m core.compute.server --host 127.0.0.1 --port 8000

It speaks the wire protocol that core/compute/remote_http_backend.py already
calls (see docs/COMPUTE_BACKENDS.md), and runs this repo's own core/ code via
LocalBackend, so a remote run produces the same artifacts as a local one.

Standard library only: nothing extra to install beyond core/requirements.txt.

Design notes
  * Auth: every request needs ``Authorization: Bearer $COMPUTE_API_KEY``
    (constant-time compare). The server refuses to start without a key unless
    ``--no-auth`` is given AND it is bound to loopback.
  * One job at a time: training / unlearning / evaluation hold a lock; a second
    request gets HTTP 409 instead of fighting over the GPU.
  * Long jobs send a space character every 15 s on a chunked response. That
    keeps tunnels with idle timeouts (Cloudflare drops silent connections after
    ~100 s) and the client's socket timeout from killing a run. The final JSON
    follows; failures arrive as ``{"_remote_error": {...}}`` because the HTTP
    status is already sent by then.
  * /upload_experiment and /download_experiment move an experiment folder as a
    zip so the Mac and the server see the same files (see archive.py).
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from core.compute.archive import pack_dir_b64, unpack_b64_into, validate_experiment_id
from core.compute.base import NotSupportedError

HEARTBEAT_SECONDS = 15.0
DEFAULT_MAX_BODY_BYTES = 1024 * 1024 * 1024  # 1 GiB (uploads are base64 zips)

READ_OPS = {
    "/load_experiment": "load_experiment",
    "/get_client_distribution": "get_client_distribution",
    "/get_fl_history": "get_fl_history",
    "/get_unlearning_status": "get_unlearning_status",
    "/get_results": "get_results",
}
JOB_OPS = {
    "/start_unlearning": "start_unlearning",
    "/run_federated_training": "run_federated_training",
    "/run_evaluation": "run_evaluation",
}


def _error_status(exc: BaseException) -> int:
    if isinstance(exc, FileNotFoundError):
        return 404
    if isinstance(exc, NotSupportedError):
        return 501
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return 400
    return 500


class ComputeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        backend: Any,
        experiments_dir: Path,
        api_key: str | None,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
        max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
    ):
        super().__init__(address, _Handler)
        self.backend = backend
        self.experiments_dir = Path(experiments_dir)
        self.api_key = api_key
        self.heartbeat_seconds = heartbeat_seconds
        self.max_body_bytes = max_body_bytes
        self.job_lock = threading.Lock()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FedUnlearnCompute/1"

    # -- plumbing -----------------------------------------------------------

    def log_message(self, fmt: str, *args: Any) -> None:  # request line only, never headers
        sys.stderr.write("[compute-server] " + (fmt % args) + "\n")

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _write_chunk(self, data: bytes) -> None:
        self.wfile.write(f"{len(data):X}\r\n".encode("ascii") + data + b"\r\n")
        self.wfile.flush()

    def _authorized(self) -> bool:
        key = self.server.api_key
        if not key:
            return True
        header = self.headers.get("Authorization", "")
        supplied = header[7:] if header.startswith("Bearer ") else ""
        return hmac.compare_digest(supplied.encode("utf-8"), key.encode("utf-8"))

    def _read_json_body(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = -1
        if length < 0:
            self._send_json(400, {"error": "Bad Content-Length."})
            return None
        if length > self.server.max_body_bytes:
            self._send_json(413, {"error": "Request body too large."})
            return None
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._send_json(400, {"error": "Body is not valid JSON."})
            return None
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Body must be a JSON object."})
            return None
        return payload

    # -- routes ---------------------------------------------------------------

    def do_GET(self) -> None:
        if not self._authorized():
            return self._send_json(401, {"error": "Missing or wrong API key."})
        self._send_json(405, {"error": "Use POST."})

    def do_POST(self) -> None:
        if not self._authorized():
            return self._send_json(401, {"error": "Missing or wrong API key."})
        payload = self._read_json_body()
        if payload is None:
            return
        path = self.path.split("?", 1)[0]
        try:
            if path == "/status":
                return self._status()
            if path in READ_OPS:
                eid = validate_experiment_id(payload.get("experiment_id"))
                return self._send_json(200, getattr(self.server.backend, READ_OPS[path])(eid))
            if path in JOB_OPS:
                eid = validate_experiment_id(payload.get("experiment_id"))
                kwargs = {k: v for k, v in payload.items() if k != "experiment_id"}
                method = getattr(self.server.backend, JOB_OPS[path])
                return self._run_job(lambda: method(experiment_id=eid, **kwargs))
            if path == "/upload_experiment":
                return self._upload(payload)
            if path == "/download_experiment":
                return self._download(payload)
        except Exception as exc:  # noqa: BLE001 - turned into a JSON error below
            traceback.print_exc()
            return self._send_json(_error_status(exc), {"error": f"{type(exc).__name__}: {str(exc)[:300]}"})
        self._send_json(404, {"error": f"Unknown path {path}."})

    def _status(self) -> None:
        status = dict(self.server.backend.get_status())
        status["busy"] = self.server.job_lock.locked()
        status.setdefault("detail", "Remote compute server ready.")
        self._send_json(200, status)

    def _upload(self, payload: dict[str, Any]) -> None:
        eid = validate_experiment_id(payload.get("experiment_id"))
        if not self.server.job_lock.acquire(blocking=False):
            return self._send_json(409, {"error": "A job is running; try again when it finishes."})
        try:
            count = unpack_b64_into(str(payload.get("archive_b64", "")), self.server.experiments_dir / eid)
        finally:
            self.server.job_lock.release()
        self._send_json(200, {"experiment_id": eid, "files": count})

    def _download(self, payload: dict[str, Any]) -> None:
        eid = validate_experiment_id(payload.get("experiment_id"))
        if not self.server.job_lock.acquire(blocking=False):
            return self._send_json(409, {"error": "A job is running; try again when it finishes."})
        try:
            archive = pack_dir_b64(self.server.experiments_dir / eid)
        finally:
            self.server.job_lock.release()
        self._send_json(200, {"experiment_id": eid, "archive_b64": archive})

    def _run_job(self, job: Callable[[], Any]) -> None:
        lock = self.server.job_lock
        if not lock.acquire(blocking=False):
            return self._send_json(409, {"error": "Another job is already running on this machine."})

        outcome: dict[str, Any] = {}

        def work() -> None:
            try:
                outcome["ok"] = job()
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                outcome["err"] = {
                    "type": type(exc).__name__,
                    "message": str(exc)[:300],
                    "status": _error_status(exc),
                }
            finally:
                lock.release()  # released by the worker so a dropped client can't free the GPU early

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            self._write_chunk(b" ")
            while True:
                thread.join(self.server.heartbeat_seconds)
                if not thread.is_alive():
                    break
                self._write_chunk(b" ")
            body = {"_remote_error": outcome["err"]} if "err" in outcome else outcome.get("ok")
            self._write_chunk(json.dumps(body, default=str).encode("utf-8"))
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # client went away; the job keeps running and still frees the lock when done
        self.close_connection = True


def _is_loopback(host: str) -> bool:
    return host in ("127.0.0.1", "::1", "localhost")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remote compute server for the Federated Unlearning Lab.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address. Keep 127.0.0.1 and reach it through an SSH or tunnel.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-auth", action="store_true", help="Allow running without COMPUTE_API_KEY (loopback only).")
    parser.add_argument("--experiments-dir", default=None, help="Default: <repo>/experiments")
    args = parser.parse_args(argv)

    api_key = os.environ.get("COMPUTE_API_KEY") or None
    if api_key is None:
        if not args.no_auth:
            print("COMPUTE_API_KEY is not set. Set it, or pass --no-auth (loopback only).", file=sys.stderr)
            return 2
        if not _is_loopback(args.host):
            print("--no-auth is only allowed with --host 127.0.0.1.", file=sys.stderr)
            return 2

    from core.compute.local_backend import LocalBackend  # imports torch; kept out of module import

    experiments_dir = Path(args.experiments_dir) if args.experiments_dir else Path(__file__).resolve().parents[2] / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    backend = LocalBackend()
    server = ComputeServer((args.host, args.port), backend, experiments_dir, api_key)
    device = backend.get_status().get("device")
    print(f"Compute server listening on http://{args.host}:{args.port}  (device: {device}, auth: {'on' if api_key else 'OFF'})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
