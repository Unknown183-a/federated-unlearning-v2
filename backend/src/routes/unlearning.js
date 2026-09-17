import { Router } from "express";
import { spawn } from "child_process";
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");

function statusPath(experimentId) {
  return join(REPO_ROOT, "experiments", experimentId, "unlearning_status.json");
}

const router = Router();

// POST /api/unlearning -> run core/unlearning (Python) Gradient Ascent
// stage for this experiment/target client, persist the status to
// experiments/<id>/unlearning_status.json, and return it (Phase 08:
// Unlearning Engine -- Gradient Ascent + API). This is
// start_unlearning(client_id) from the Dashboard Spec (Ch.71.8).
// Requires that /api/partition and /api/training have already been
// run for this experiment_id.
router.post("/", (req, res) => {
  const { experiment_id, client_id, steps, lr, batch_size } = req.body || {};

  if (!experiment_id || client_id === undefined) {
    return res.status(400).json({
      error: "experiment_id and client_id are required",
    });
  }

  const args = [
    "-m",
    "core.unlearning.cli",
    "--experiment-id",
    String(experiment_id),
    "--client-id",
    String(client_id),
  ];
  if (steps !== undefined) args.push("--steps", String(steps));
  if (lr !== undefined) args.push("--lr", String(lr));
  if (batch_size !== undefined) args.push("--batch-size", String(batch_size));

  const py = spawn(process.env.PYTHON_BIN || "python3", args, { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  py.on("error", (err) => {
    res.status(500).json({ error: "Could not start the unlearning engine", detail: err.message });
  });

  py.on("close", (code) => {
    if (res.headersSent) return;
    if (code !== 0) {
      return res.status(400).json({ error: "Unlearning failed", detail: stderr.trim() });
    }
    try {
      res.status(200).json({ status: JSON.parse(stdout) });
    } catch (err) {
      res.status(500).json({ error: "Could not parse unlearning engine output", detail: stdout });
    }
  });
});

// GET /api/unlearning/:experimentId -> re-read the most recently
// persisted unlearning status without re-running anything
// (get_unlearning_status()).
router.get("/:experimentId", (req, res) => {
  const path = statusPath(req.params.experimentId);
  if (!existsSync(path)) {
    return res
      .status(404)
      .json({ error: `No unlearning status found for experiment "${req.params.experimentId}"` });
  }
  const status = JSON.parse(readFileSync(path, "utf-8"));
  res.status(200).json({ status });
});

export default router;
