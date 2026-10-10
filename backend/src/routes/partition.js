import { Router } from "express";
import { readArtifact, isValidExperimentId, validateExperimentIdParam } from "../artifacts.js";
import { runEngine } from "../runEngine.js";
import { sendCorruptArtifact, sendInvalidRequest, sendNotFound } from "../errors.js";

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
router.param("experimentId", validateExperimentIdParam);

// POST /api/partition -> run core/partitioning (Python) for this config,
// persist the full partition to experiments/<id>/partition.json, and
// return the lightweight summary (Phase 03: Partitioning Engine + API).
router.post("/", (req, res) => {
  const { dataset, num_clients, partition_strategy, seed, experiment_id } = req.body || {};

  if (!dataset || !num_clients || !partition_strategy || seed === undefined || !experiment_id) {
    return sendInvalidRequest(
      res,
      "dataset, num_clients, partition_strategy, seed, and experiment_id are all required"
    );
  }
  if (!isValidExperimentId(String(experiment_id))) {
    return sendInvalidRequest(res, "That experiment id is not valid.");
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

  runEngine({
    args,
    stage: "partition",
    res,
    experimentId: String(experiment_id),
    onSuccess: (parsed) => res.status(200).json({ partition: parsed }),
  });
});

// GET /api/partition/:experimentId -> re-read a previously computed
// partition's summary without re-running the engine.
router.get("/:experimentId", (req, res) => {
  const { experimentId } = req.params;
  const artifact = readArtifact(experimentId, "partition.json");
  if (artifact.state === "missing") {
    return sendNotFound(
      res,
      `No partition found for experiment "${experimentId}"`,
      "PARTITION_UNAVAILABLE"
    );
  }
  if (artifact.state === "corrupt") return sendCorruptArtifact(res, "partition", experimentId);
  res.status(200).json({ partition: summarize(artifact.data) });
});

export default router;
