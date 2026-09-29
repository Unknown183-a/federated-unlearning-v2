import { Router } from "express";
import { spawn } from "child_process";
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");

function retrainingPath(experimentId) {
  return join(REPO_ROOT, "experiments", experimentId, "retraining_results.json");
}

function runCli(args, res, resultKey, failLabel) {
  const py = spawn(process.env.PYTHON_BIN || "python3", args, { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  py.on("error", (err) => {
    res.status(500).json({ error: `Could not start ${failLabel}`, detail: err.message });
  });

  py.on("close", (code) => {
    if (res.headersSent) return;
    if (code !== 0) {
      return res.status(400).json({ error: `${failLabel} failed`, detail: stderr.trim() });
    }
    try {
      res.status(200).json(JSON.parse(stdout));
    } catch (err) {
      res.status(500).json({ error: `Could not parse ${failLabel} output`, detail: stdout });
    }
  });
}

const router = Router();

// POST /api/retraining -> run core.evaluation.retraining_cli (Python):
// full-retraining-from-scratch baseline (excludes the unlearning
// target client, reuses the original run's protocol), persist to
// experiments/<id>/{retrained_model.pt,retraining_results.json}, and
// return { retraining, comparison } (Phase 11, Dashboard Spec Ch.24).
// This is the expensive call -- typically run once, offline/on demand
// (Ch.37) -- and requires /api/unlearning + /api/evaluation to have
// already completed for this experiment_id.
router.post("/", (req, res) => {
  const { experiment_id, device } = req.body || {};
  if (!experiment_id) {
    return res.status(400).json({ error: "experiment_id is required" });
  }
  const args = ["-m", "core.evaluation.retraining_cli", "--experiment-id", String(experiment_id)];
  if (device !== undefined) args.push("--device", String(device));
  runCli(args, res, "retraining", "The retraining baseline");
});

// GET /api/retraining/:experimentId -> re-read the most recently
// persisted retraining baseline without re-running anything.
router.get("/:experimentId", (req, res) => {
  const path = retrainingPath(req.params.experimentId);
  if (!existsSync(path)) {
    return res
      .status(404)
      .json({ error: `No retraining baseline found for experiment "${req.params.experimentId}"` });
  }
  const retraining = JSON.parse(readFileSync(path, "utf-8"));
  res.status(200).json({ retraining });
});

// GET /api/retraining/:experimentId/comparison -> cheap re-computation
// of original vs unlearned vs retrained from the two stored artifacts
// (no training, no torch import) -- compare_with_retraining() from the
// Dashboard Spec (Ch.36).
router.get("/:experimentId/comparison", (req, res) => {
  const args = [
    "-m",
    "core.evaluation.retraining_cli",
    "--experiment-id",
    String(req.params.experimentId),
    "--compare-only",
  ];
  runCli(args, res, "the comparison", "The comparison");
});

export default router;
