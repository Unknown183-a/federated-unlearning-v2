import { Router } from "express";
import { spawn } from "child_process";
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");

function resultsPath(experimentId) {
  return join(REPO_ROOT, "experiments", experimentId, "evaluation_results.json");
}

const router = Router();

// POST /api/evaluation -> run core/evaluation (Python): global/forget-
// client/retained-client accuracy, MIA, and runtime, each measured
// before and after unlearning, persist to
// experiments/<id>/evaluation_results.json, and return it
// (Phase 10: Evaluation Engine -- evaluate_model() from the Dashboard
// Spec, Ch.36). Requires that /api/unlearning has already completed
// for this experiment_id (Phase 10 Depends On Phase 09).
router.post("/", (req, res) => {
  const { experiment_id, non_member_sample_size, device } = req.body || {};

  if (!experiment_id) {
    return res.status(400).json({ error: "experiment_id is required" });
  }

  const args = ["-m", "core.evaluation.cli", "--experiment-id", String(experiment_id)];
  if (non_member_sample_size !== undefined) {
    args.push("--non-member-sample-size", String(non_member_sample_size));
  }
  if (device !== undefined) args.push("--device", String(device));

  const py = spawn(process.env.PYTHON_BIN || "python3", args, { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  py.on("error", (err) => {
    res.status(500).json({ error: "Could not start the evaluation engine", detail: err.message });
  });

  py.on("close", (code) => {
    if (res.headersSent) return;
    if (code !== 0) {
      return res.status(400).json({ error: "Evaluation failed", detail: stderr.trim() });
    }
    try {
      res.status(200).json({ results: JSON.parse(stdout) });
    } catch (err) {
      res.status(500).json({ error: "Could not parse evaluation engine output", detail: stdout });
    }
  });
});

// GET /api/evaluation/:experimentId -> re-read the most recently
// persisted evaluation results without re-running anything.
router.get("/:experimentId", (req, res) => {
  const path = resultsPath(req.params.experimentId);
  if (!existsSync(path)) {
    return res
      .status(404)
      .json({ error: `No evaluation results found for experiment "${req.params.experimentId}"` });
  }
  const results = JSON.parse(readFileSync(path, "utf-8"));
  res.status(200).json({ results });
});

export default router;
