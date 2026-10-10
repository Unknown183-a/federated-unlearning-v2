import { Router } from "express";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

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

  py.on("error", (err) => {
    res.status(500).json({ error: "Could not start the compute status check", detail: err.message });
  });

  py.on("close", (code) => {
    if (res.headersSent) return;
    if (code !== 0) {
      return res.status(500).json({ error: "Compute status check failed", detail: stderr.trim() });
    }
    try {
      res.status(200).json(JSON.parse(stdout));
    } catch (err) {
      res.status(500).json({ error: "Could not parse compute status output", detail: stdout });
    }
  });
});

export default router;
