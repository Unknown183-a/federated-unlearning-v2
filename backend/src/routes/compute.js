import { Router } from "express";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { conciseDetail } from "../errors.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");

const router = Router();

// GET /api/compute/status -> the status of every compute backend
// (College GPU, Google Colab, Local, Demo) plus which one Auto mode
// would currently select and the full trace of what it tried (Phase
// 14). Shells out to core.compute.cli, which is the only code that
// ever touches the COLLEGE_GPU_* / COLAB_* environment variables --
// this route, and everything in the browser, only ever sees the
// credential-free status JSON that CLI prints (see
// core/compute/remote_http_backend.py's security notes). Nothing here
// reads, forwards, or logs those variables.
router.get("/status", (req, res) => {
  const py = spawn(process.env.PYTHON_BIN || "python3", ["-m", "core.compute.cli"], { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  // A status check must never hang the page: if the probe has not
  // answered in 15s (e.g. an unreachable remote backend and a slow
  // network), fall through to the stored-experiment fallback below.
  const timer = setTimeout(() => py.kill("SIGKILL"), 15000);

  py.on("error", (err) => {
    clearTimeout(timer);
    respondDegraded(res, `Could not start the compute status check (${err.message}).`);
  });

  py.on("close", (code) => {
    clearTimeout(timer);
    if (res.headersSent) return;
    if (code !== 0) {
      return respondDegraded(res, `The compute status check failed: ${conciseDetail(stderr) || `exit ${code}`}`);
    }
    try {
      res.status(200).json(JSON.parse(stdout));
    } catch {
      respondDegraded(res, "The compute status check returned an unreadable response.");
    }
  });
});

// Phase 15 (Spec Ch.71.12: "The presentation must remain functional even
// when no remote GPU is reachable"). If the Python status probe itself
// cannot run, the dashboard still works for every STORED experiment --
// those are read as JSON directly by the Express routes, with no Python
// involved. So instead of a 500, say exactly that, and flag the response
// as degraded so the UI shows it. Nothing here pretends a live backend
// is available: only the Demo (Precomputed) backend is listed.
function respondDegraded(res, reason) {
  if (res.headersSent) return;
  const demo = {
    backend: "demo",
    name: "Demo (Precomputed)",
    available: true,
    detail: "Stored experiments can still be replayed. New live runs are unavailable.",
    device: null,
    latency_ms: null,
  };
  res.status(200).json({
    degraded: true,
    degraded_reason: reason,
    backends: [demo],
    auto_selected: "demo",
    auto_trace: [demo],
  });
}

export default router;
