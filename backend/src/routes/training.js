import { Router } from "express";
import { readArtifact, isValidExperimentId, validateExperimentIdParam } from "../artifacts.js";
import { runEngine } from "../runEngine.js";
import { sendCorruptArtifact, sendInvalidRequest, sendNotFound } from "../errors.js";

const router = Router();
router.param("experimentId", validateExperimentIdParam);

// POST /api/training -> run core/federated (Python) FedAvg loop for this
// experiment, persist the round-by-round history to
// experiments/<id>/fl_history.json, and return it (Phase 05: FL Engine
// + API). Requires that /api/partition has already been run for this
// experiment_id -- the training CLI loads that saved partition.
//
// Phase 15: failures come back as structured errors (see errors.js),
// and the experiment id is validated before it reaches the filesystem.
router.post("/", (req, res) => {
  const { experiment_id, model, federated_rounds, local_epochs, seed, backend } = req.body || {};

  if (!experiment_id || !model || !federated_rounds || !local_epochs || seed === undefined) {
    return sendInvalidRequest(
      res,
      "experiment_id, model, federated_rounds, local_epochs, and seed are all required"
    );
  }
  if (!isValidExperimentId(String(experiment_id))) {
    return sendInvalidRequest(res, "That experiment id is not valid.");
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
  // Phase 14: optional compute backend selection (college_gpu | colab |
  // local | demo | auto). Omitted -> identical to pre-Phase-14 behavior,
  // run in-process; the CLI's output shape only changes when this flag
  // is present (adds backend_trace alongside history).
  if (backend !== undefined) args.push("--backend", String(backend));

  runEngine({
    args,
    stage: "training",
    res,
    experimentId: String(experiment_id),
    onSuccess: (parsed) => res.status(200).json(backend !== undefined ? parsed : { history: parsed }),
  });
});

// GET /api/training/:experimentId -> re-read a previously computed FL
// history without re-running training (get_fl_history()).
router.get("/:experimentId", (req, res) => {
  const { experimentId } = req.params;
  const artifact = readArtifact(experimentId, "fl_history.json");
  if (artifact.state === "missing") {
    return sendNotFound(
      res,
      `No trained checkpoint exists for experiment "${experimentId}".`,
      "MODEL_UNAVAILABLE"
    );
  }
  if (artifact.state === "corrupt") return sendCorruptArtifact(res, "training history", experimentId);
  res.status(200).json({ history: artifact.data });
});

export default router;
