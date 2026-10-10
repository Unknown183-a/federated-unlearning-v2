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

// POST /api/evaluation -> run core/evaluation (Python): global/forget-
// client/retained-client accuracy, MIA, and runtime, each measured
// before and after unlearning, persist to
// experiments/<id>/evaluation_results.json, and return it
// (Phase 10: Evaluation Engine -- evaluate_model() from the Dashboard
// Spec, Ch.36). Requires that /api/unlearning has already completed
// for this experiment_id (Phase 10 Depends On Phase 09).
router.post("/", (req, res) => {
  const { experiment_id, non_member_sample_size, device, backend } = req.body || {};

  if (!experiment_id) {
    return sendInvalidRequest(res, "experiment_id is required");
  }
  if (!isValidExperimentId(String(experiment_id))) {
    return sendInvalidRequest(res, "That experiment id is not valid.");
  }

  const args = ["-m", "core.evaluation.cli", "--experiment-id", String(experiment_id)];
  if (non_member_sample_size !== undefined) {
    args.push("--non-member-sample-size", String(non_member_sample_size));
  }
  if (device !== undefined) args.push("--device", String(device));
  // Phase 14: optional compute backend selection, see training.js for
  // the same pattern -- omitted is byte-for-byte the pre-Phase-14 behavior.
  if (backend !== undefined) args.push("--backend", String(backend));

  runEngine({
    args,
    stage: "evaluation",
    res,
    experimentId: String(experiment_id),
    onSuccess: (parsed) => res.status(200).json(backend !== undefined ? parsed : { results: parsed }),
  });
});

// GET /api/evaluation/:experimentId -> re-read the most recently
// persisted evaluation results without re-running anything.
//
// Phase 15 (Spec Ch.43, "Evaluation failure: do not show incomplete
// metrics as valid final results"): a results file whose status is not
// "complete" is refused with a 409 rather than served as if it were a
// real result.
router.get("/:experimentId", (req, res) => {
  const { experimentId } = req.params;
  const artifact = readArtifact(experimentId, "evaluation_results.json");
  if (artifact.state === "missing") {
    return sendNotFound(res, `No evaluation results found for experiment "${experimentId}"`);
  }
  if (artifact.state === "corrupt") return sendCorruptArtifact(res, "evaluation results", experimentId);
  if (artifact.data.status !== "complete") {
    return sendIncompleteArtifact(res, "evaluation results", experimentId, artifact.data.status);
  }
  res.status(200).json({ results: artifact.data });
});

export default router;
