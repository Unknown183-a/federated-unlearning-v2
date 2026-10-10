import { Router } from "express";
import { readArtifact, isValidExperimentId, validateExperimentIdParam } from "../artifacts.js";
import { runEngine } from "../runEngine.js";
import { sendCorruptArtifact, sendInvalidRequest, sendNotFound } from "../errors.js";

const router = Router();
router.param("experimentId", validateExperimentIdParam);

// POST /api/unlearning -> run core/unlearning (Python) Gradient Ascent
// followed by Knowledge Distillation for this experiment/target
// client, persist the status to experiments/<id>/unlearning_status.json,
// and return it (Phase 08 + Phase 09: Unlearning Engine -- Gradient
// Ascent + Knowledge Distillation + API). This is
// start_unlearning(client_id) from the Dashboard Spec (Ch.71.8).
// Requires that /api/partition and /api/training have already been
// run for this experiment_id.
//
// Phase 15: a failure reports WHICH stage failed ("Gradient Ascent" or
// "Knowledge Distillation") using what the engine persisted, plus the
// technical error and a retry hint (Dashboard Spec Ch.43).
router.post("/", (req, res) => {
  const {
    experiment_id,
    client_id,
    steps,
    lr,
    batch_size,
    kd_epochs,
    kd_lr,
    kd_temperature,
    kd_alpha,
    kd_batch_size,
    backend,
  } = req.body || {};

  if (!experiment_id || client_id === undefined || client_id === null) {
    return sendInvalidRequest(res, "experiment_id and client_id are required");
  }
  if (!isValidExperimentId(String(experiment_id))) {
    return sendInvalidRequest(res, "That experiment id is not valid.");
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
  if (kd_epochs !== undefined) args.push("--kd-epochs", String(kd_epochs));
  if (kd_lr !== undefined) args.push("--kd-lr", String(kd_lr));
  if (kd_temperature !== undefined) args.push("--kd-temperature", String(kd_temperature));
  if (kd_alpha !== undefined) args.push("--kd-alpha", String(kd_alpha));
  if (kd_batch_size !== undefined) args.push("--kd-batch-size", String(kd_batch_size));
  // Phase 14: optional compute backend selection, see training.js for
  // the same pattern -- omitted is byte-for-byte the pre-Phase-14 behavior.
  if (backend !== undefined) args.push("--backend", String(backend));

  runEngine({
    args,
    stage: "unlearning",
    res,
    experimentId: String(experiment_id),
    onSuccess: (parsed) => res.status(200).json(backend !== undefined ? parsed : { status: parsed }),
  });
});

// GET /api/unlearning/:experimentId -> re-read the most recently
// persisted unlearning status without re-running anything
// (get_unlearning_status()).
router.get("/:experimentId", (req, res) => {
  const { experimentId } = req.params;
  const artifact = readArtifact(experimentId, "unlearning_status.json");
  if (artifact.state === "missing") {
    return sendNotFound(res, `No unlearning status found for experiment "${experimentId}"`);
  }
  if (artifact.state === "corrupt") return sendCorruptArtifact(res, "unlearning status", experimentId);
  res.status(200).json({ status: artifact.data });
});

export default router;
