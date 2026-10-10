import { Router } from "express";
import { existsSync, readdirSync, readFileSync, statSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { validateExperimentIdParam } from "../artifacts.js";
import { sendNotFound } from "../errors.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
// backend/src/routes/ -> repo root
const REPO_ROOT = join(__dirname, "..", "..", "..");
const EXPERIMENTS_DIR = join(REPO_ROOT, "experiments");
const MANIFEST_PATH = join(REPO_ROOT, "core", "datasets", "manifest.json");

// Phase 12 -- Experiment Artifact Registry (Dashboard Spec Ch.29/30,
// Page 9 "Experiment History" + the Quick Demo's "Model Library").
//
// This repo's "machine-readable manifest" (Ch.30) is already
// distributed across each phase's own artifact files --
// partition.json (Phase 03), fl_history.json (Phase 05),
// unlearning_status.json (Phase 08+09), evaluation_results.json
// (Phase 10), retraining_results.json (Phase 11) -- written by the
// Python core and read back by the other routes. Rather than inventing
// a second, parallel manifest file that could drift out of sync with
// those (the Ch.69 "source of truth" rule cuts against duplicating
// state), this route just aggregates whichever of those files already
// exist for each experiment_id into one summary per experiment.
//
// This is pure read-only aggregation of already-computed JSON -- no
// training, no evaluation, no new ML logic (explicitly out of scope
// for this phase) -- so it lives directly in the Express layer rather
// than shelling out to Python, same as the plain-JSON GET handlers in
// the other route files.

function readJsonIfExists(path) {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch {
    // A partially-written or corrupted artifact shouldn't take down the
    // whole listing -- treat it as absent for this experiment.
    return null;
  }
}

function latestMtimeMs(paths) {
  let latest = 0;
  for (const path of paths) {
    if (!existsSync(path)) continue;
    const mtime = statSync(path).mtimeMs;
    if (mtime > latest) latest = mtime;
  }
  return latest;
}

function statusLabel(stages) {
  if (stages.compared) return "Compared";
  if (stages.evaluated) return "Evaluated";
  if (stages.unlearned) return "Unlearned";
  if (stages.trained) return "Trained";
  if (stages.partitioned) return "Partitioned";
  return "Empty";
}

export function summarizeExperiment(experimentId) {
  const dir = join(EXPERIMENTS_DIR, experimentId);

  const partitionPath = join(dir, "partition.json");
  const flHistoryPath = join(dir, "fl_history.json");
  const globalModelPath = join(dir, "global_model.pt");
  const unlearningStatusPath = join(dir, "unlearning_status.json");
  const evaluationResultsPath = join(dir, "evaluation_results.json");
  const retrainingResultsPath = join(dir, "retraining_results.json");

  const partition = readJsonIfExists(partitionPath);
  const flHistory = readJsonIfExists(flHistoryPath);
  const unlearningStatus = readJsonIfExists(unlearningStatusPath);
  const evaluationResults = readJsonIfExists(evaluationResultsPath);
  const retrainingResults = readJsonIfExists(retrainingResultsPath);

  const stages = {
    partitioned: Boolean(partition),
    trained: Boolean(flHistory) && existsSync(globalModelPath),
    unlearned: Boolean(unlearningStatus) && unlearningStatus.status === "complete",
    evaluated: Boolean(evaluationResults) && evaluationResults.status === "complete",
    compared: Boolean(retrainingResults) && retrainingResults.status === "complete",
  };

  return {
    experiment_id: experimentId,
    dataset: flHistory?.dataset ?? partition?.dataset ?? null,
    num_clients: partition?.num_clients ?? flHistory?.num_clients ?? null,
    partition_strategy: partition?.strategy ?? null,
    model: flHistory?.model ?? null,
    federated_rounds: flHistory?.rounds ?? null,
    seed: flHistory?.seed ?? partition?.seed ?? null,
    final_accuracy: flHistory?.final_accuracy ?? null,
    target_client_id: unlearningStatus?.target_client_id ?? evaluationResults?.target_client_id ?? null,
    stages,
    // Phase 15: true only when the whole research story (Dataset ->
    // ... -> Retraining Comparison) can be replayed from stored
    // artifacts alone, with no live backend. Professor Demo Mode
    // prefers these experiments.
    replayable: Object.values(stages).every(Boolean),
    status: statusLabel(stages),
    updated_at: latestMtimeMs([
      partitionPath,
      flHistoryPath,
      globalModelPath,
      unlearningStatusPath,
      evaluationResultsPath,
      retrainingResultsPath,
    ]),
  };
}

export function listExperimentSummaries() {
  if (!existsSync(EXPERIMENTS_DIR)) return [];
  const entries = readdirSync(EXPERIMENTS_DIR, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

  return entries
    .map((experimentId) => summarizeExperiment(experimentId))
    .filter((summary) => summary.status !== "Empty")
    .sort((a, b) => b.updated_at - a.updated_at);
}

const router = Router();
router.param("experimentId", validateExperimentIdParam);

// GET /api/experiments -> every experiment with at least a saved
// partition, newest first. Page 9 (Experiment History) shows all of
// these regardless of how far each one got.
//
// GET /api/experiments?trained_only=true -> only experiments with a
// usable trained global model (Phase 05 complete) -- the Quick Demo's
// "AVAILABLE FEDERATED MODELS" library (Ch.27), which starts a user
// straight at Client Selection without running training themselves.
router.get("/", (req, res) => {
  const summaries = listExperimentSummaries();
  const trainedOnly = req.query.trained_only === "true";
  // Phase 15: ?replayable_only=true -> only experiments whose entire
  // story can be replayed from stored artifacts (Professor Demo Mode).
  const replayableOnly = req.query.replayable_only === "true";
  let filtered = summaries;
  if (trainedOnly) filtered = filtered.filter((s) => s.stages.trained);
  if (replayableOnly) filtered = filtered.filter((s) => s.replayable);
  res.status(200).json({ experiments: filtered });
});

function datasetConfig(datasetId) {
  const manifest = readJsonIfExists(MANIFEST_PATH);
  const entry = manifest && datasetId ? manifest[datasetId] : null;
  if (!entry) return null;
  return {
    name: entry.name,
    image_size: entry.image_size,
    channels: entry.channels,
    num_classes: entry.num_classes,
    num_train: entry.num_train,
    num_test: entry.num_test,
  };
}

const METHOD_LABELS = {
  "gradient_ascent+knowledge_distillation": "Gradient Ascent + Knowledge Distillation",
};

// Phase 15 -- Experiment Reproducibility (Dashboard Spec Ch.44) and the
// collapsible "Experiment Configuration" panel (Ch.45).
//
// Everything here is read straight from the stored artifacts. A field
// the artifacts do not contain is returned as null and the UI says
// "not recorded" -- it is never filled in with a default, because a
// made-up configuration shown next to a real result would be exactly
// the kind of fabricated value Ch.39 forbids. (Unlearning
// hyperparameters and software version are only present for runs made
// from Phase 15 onwards.)
export function buildReproducibility(experimentId) {
  const dir = join(EXPERIMENTS_DIR, experimentId);
  const partition = readJsonIfExists(join(dir, "partition.json"));
  const flHistory = readJsonIfExists(join(dir, "fl_history.json"));
  const unlearning = readJsonIfExists(join(dir, "unlearning_status.json"));
  const evaluation = readJsonIfExists(join(dir, "evaluation_results.json"));
  const retraining = readJsonIfExists(join(dir, "retraining_results.json"));
  const summary = summarizeExperiment(experimentId);

  const datasetId = flHistory?.dataset ?? partition?.dataset ?? null;
  const method = unlearning?.method ?? (unlearning ? "gradient_ascent+knowledge_distillation" : null);

  return {
    experiment_id: experimentId,
    dataset: datasetId,
    dataset_config: datasetConfig(datasetId),
    num_clients: partition?.num_clients ?? flHistory?.num_clients ?? null,
    partition_strategy: partition?.strategy ?? null,
    partition_alpha: partition?.alpha ?? null,
    seed: flHistory?.seed ?? partition?.seed ?? null,
    model: flHistory?.model ?? null,
    federated_rounds: flHistory?.rounds ?? null,
    local_epochs: flHistory?.local_epochs ?? null,
    learning_rate: flHistory?.lr ?? null,
    batch_size: flHistory?.batch_size ?? null,
    unlearning: unlearning
      ? {
          method,
          method_label: METHOD_LABELS[method] ?? method,
          target_client_id: unlearning.target_client_id ?? null,
          hyperparameters: unlearning.hyperparameters ?? null,
          status: unlearning.status ?? null,
        }
      : null,
    software: unlearning?.software ?? evaluation?.software ?? retraining?.software ?? null,
    stages: summary.stages,
    replayable: summary.replayable,
  };
}

// GET /api/experiments/:experimentId/reproducibility
router.get("/:experimentId/reproducibility", (req, res) => {
  const { experimentId } = req.params;
  if (!existsSync(join(EXPERIMENTS_DIR, experimentId))) {
    return sendNotFound(res, `No experiment found with id "${experimentId}"`);
  }
  res.status(200).json({ reproducibility: buildReproducibility(experimentId) });
});

// GET /api/experiments/:experimentId -> a single experiment's summary,
// for a detail view or a sanity check before "opening" it client-side.
router.get("/:experimentId", (req, res) => {
  const { experimentId } = req.params;
  if (!existsSync(join(EXPERIMENTS_DIR, experimentId))) {
    return sendNotFound(res, `No experiment found with id "${experimentId}"`);
  }
  res.status(200).json({ experiment: summarizeExperiment(experimentId) });
});

export default router;
