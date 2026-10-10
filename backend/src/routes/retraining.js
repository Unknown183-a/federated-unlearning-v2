import { Router } from "express";
import { readArtifact, isValidExperimentId, validateExperimentIdParam } from "../artifacts.js";
import { runEngine } from "../runEngine.js";
import {
  sendCorruptArtifact,
  sendIncompleteArtifact,
  sendInvalidRequest,
  sendNotFound,
} from "../errors.js";

const router = Router();
router.param("experimentId", validateExperimentIdParam);

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
    return sendInvalidRequest(res, "experiment_id is required");
  }
  if (!isValidExperimentId(String(experiment_id))) {
    return sendInvalidRequest(res, "That experiment id is not valid.");
  }
  const args = ["-m", "core.evaluation.retraining_cli", "--experiment-id", String(experiment_id)];
  if (device !== undefined) args.push("--device", String(device));
  runEngine({
    args,
    stage: "retraining",
    res,
    experimentId: String(experiment_id),
    onSuccess: (parsed) => res.status(200).json(parsed),
  });
});

// GET /api/retraining/:experimentId -> re-read the most recently
// persisted retraining baseline without re-running anything.
// Incomplete baselines are refused, same rule as /api/evaluation.
router.get("/:experimentId", (req, res) => {
  const { experimentId } = req.params;
  const artifact = readArtifact(experimentId, "retraining_results.json");
  if (artifact.state === "missing") {
    return sendNotFound(res, `No retraining baseline found for experiment "${experimentId}"`);
  }
  if (artifact.state === "corrupt") return sendCorruptArtifact(res, "retraining baseline", experimentId);
  if (artifact.data.status !== "complete") {
    return sendIncompleteArtifact(res, "retraining baseline", experimentId, artifact.data.status);
  }
  res.status(200).json({ retraining: artifact.data });
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
  runEngine({
    args,
    stage: "retraining",
    res,
    experimentId: req.params.experimentId,
    onSuccess: (parsed) => res.status(200).json(parsed),
  });
});

export default router;
