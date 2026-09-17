import { Router } from "express";
import { spawn } from "child_process";
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");

function historyPath(experimentId) {
  return join(REPO_ROOT, "experiments", experimentId, "fl_history.json");
}

const router = Router();

// POST /api/training -> run core/federated (Python) FedAvg loop for this
// experiment, persist the round-by-round history to
// experiments/<id>/fl_history.json, and return it (Phase 05: FL Engine
// + API). Requires that /api/partition has already been run for this
// experiment_id -- the training CLI loads that saved partition.
router.post("/", (req, res) => {
  const { experiment_id, model, federated_rounds, local_epochs, seed } = req.body || {};

  if (!experiment_id || !model || !federated_rounds || !local_epochs || seed === undefined) {
    return res.status(400).json({
      error: "experiment_id, model, federated_rounds, local_epochs, and seed are all required",
    });
  }

  const args = [
    "-m",
    "core.federated.cli",
    "--experiment-id",
    String(experiment_id),
    "--model",
    String(model),
    "--rounds",
    String(federated_rounds),
    "--local-epochs",
    String(local_epochs),
    "--seed",
    String(seed),
  ];

  const py = spawn(process.env.PYTHON_BIN || "python3", args, { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  py.on("error", (err) => {
    res.status(500).json({ error: "Could not start the federated training engine", detail: err.message });
  });

  py.on("close", (code) => {
    if (res.headersSent) return;
    if (code !== 0) {
      return res.status(400).json({ error: "Training failed", detail: stderr.trim() });
    }
    try {
      res.status(200).json({ history: JSON.parse(stdout) });
    } catch (err) {
      res.status(500).json({ error: "Could not parse training engine output", detail: stdout });
    }
  });
});

// GET /api/training/:experimentId -> re-read a previously computed FL
// history without re-running training (get_fl_history()).
router.get("/:experimentId", (req, res) => {
  const path = historyPath(req.params.experimentId);
  if (!existsSync(path)) {
    return res
      .status(404)
      .json({ error: `No training history found for experiment "${req.params.experimentId}"` });
  }
  const history = JSON.parse(readFileSync(path, "utf-8"));
  res.status(200).json({ history });
});

export default router;
