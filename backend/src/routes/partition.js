import { Router } from "express";
import { spawn } from "child_process";
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");

function partitionPath(experimentId) {
  return join(REPO_ROOT, "experiments", experimentId, "partition.json");
}

function summarize(partition) {
  const samples = partition.clients.map((c) => c.num_samples);
  const avg = samples.reduce((a, b) => a + b, 0) / samples.length;
  const mostImbalanced = partition.clients.reduce((worst, c) => {
    if (!worst) return c;
    return Math.abs(c.num_samples - avg) > Math.abs(worst.num_samples - avg) ? c : worst;
  }, null);

  return {
    dataset: partition.dataset,
    num_clients: partition.num_clients,
    strategy: partition.strategy,
    seed: partition.seed,
    alpha: partition.alpha,
    num_classes: partition.num_classes,
    total_samples: partition.total_samples,
    average_samples_per_client: avg,
    most_imbalanced_client: mostImbalanced ? mostImbalanced.client_id : null,
    clients: partition.clients.map((c) => ({
      client_id: c.client_id,
      num_samples: c.num_samples,
      num_classes_present: Object.keys(c.class_counts).length,
      class_counts: c.class_counts,
    })),
  };
}

const router = Router();

// POST /api/partition -> run core/partitioning (Python) for this config,
// persist the full partition to experiments/<id>/partition.json, and
// return the lightweight summary (Phase 03: Partitioning Engine + API).
router.post("/", (req, res) => {
  const { dataset, num_clients, partition_strategy, seed, experiment_id } = req.body || {};

  if (!dataset || !num_clients || !partition_strategy || seed === undefined || !experiment_id) {
    return res.status(400).json({
      error:
        "dataset, num_clients, partition_strategy, seed, and experiment_id are all required",
    });
  }

  const args = [
    "-m",
    "core.partitioning.cli",
    "--dataset",
    String(dataset),
    "--num-clients",
    String(num_clients),
    "--strategy",
    String(partition_strategy),
    "--seed",
    String(seed),
    "--experiment-id",
    String(experiment_id),
  ];

  const py = spawn(process.env.PYTHON_BIN || "python3", args, { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  py.on("error", (err) => {
    res.status(500).json({ error: "Could not start the partitioning engine", detail: err.message });
  });

  py.on("close", (code) => {
    if (res.headersSent) return;
    if (code !== 0) {
      return res.status(400).json({ error: "Partitioning failed", detail: stderr.trim() });
    }
    try {
      res.status(200).json({ partition: JSON.parse(stdout) });
    } catch (err) {
      res.status(500).json({ error: "Could not parse partitioner output", detail: stdout });
    }
  });
});

// GET /api/partition/:experimentId -> re-read a previously computed
// partition's summary without re-running the engine.
router.get("/:experimentId", (req, res) => {
  const path = partitionPath(req.params.experimentId);
  if (!existsSync(path)) {
    return res
      .status(404)
      .json({ error: `No partition found for experiment "${req.params.experimentId}"` });
  }
  const partition = JSON.parse(readFileSync(path, "utf-8"));
  res.status(200).json({ partition: summarize(partition) });
});

export default router;
