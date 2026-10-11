// Phase 15 -- one place that turns "a Python engine failed" into a
// structured, presentation-safe API error (Dashboard Spec Ch.43).
//
// Before this phase every route answered a failure with
// `{ error: "Training failed", detail: <raw stderr> }` -- the whole
// Python traceback, file paths and all. That is hard to read on a
// projector and leaks server paths to the browser. Now every failure
// carries:
//
//   error      short human sentence (kept so older clients still work)
//   code       stable machine code the dashboard switches on
//   stage      which pipeline stage failed (human label)
//   detail     the technical error -- ONE line, length-capped
//   retryable  whether pressing "Retry" can plausibly help
//
// Nothing here ever reads or forwards credentials; `detail` is built
// only from the Python process's own error text.

export const STAGE_LABELS = {
  partition: "Data Partitioning",
  training: "Federated Training",
  gradient_ascent: "Gradient Ascent",
  knowledge_distillation: "Knowledge Distillation",
  unlearning: "Unlearning",
  evaluation: "Evaluation",
  retraining: "Full Retraining",
  release: "Model Release",
  dataset: "Dataset Loading",
  artifact: "Stored Artifact",
};

const MAX_DETAIL_LENGTH = 400;

/**
 * Reduce a Python stderr dump to its last meaningful line -- the
 * exception message. Tracebacks are noise for a professor and expose
 * absolute paths; the last line ("ValueError: steps must be >= 1") is
 * the part a person can act on.
 */
export function conciseDetail(stderr) {
  const lines = String(stderr || "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length === 0) return "";
  let last = lines[lines.length - 1];
  // Drop the "ValueError: " style prefix only when it is a bare
  // exception class name, so "No client 9 in ..." reads naturally.
  last = last.replace(/^[A-Za-z_.]+(Error|Exception):\s*/, "");
  return last.length > MAX_DETAIL_LENGTH ? `${last.slice(0, MAX_DETAIL_LENGTH)}…` : last;
}

// Ordered: the first matching rule wins.
const RULES = [
  {
    test: /no client \d+ in this experiment/i,
    code: "CLIENT_UNAVAILABLE",
    status: 400,
    retryable: false,
    message: "Selected client is not available in this experiment.",
  },
  {
    test: /serves precomputed experiments only|read-only/i,
    code: "BACKEND_NOT_SUPPORTED",
    status: 409,
    retryable: false,
    message: "The selected compute backend can only replay stored experiments.",
  },
  {
    test: /no compute backend could complete|is not configured|connection (refused|reset|aborted)|timed out|timeout|unreachable|failed mid-run|backend .*unavailable/i,
    code: "BACKEND_UNAVAILABLE",
    status: 503,
    retryable: true,
    message: "The selected compute backend is unavailable.",
  },
  {
    test: /unlearning has not completed|no unlearning status found/i,
    code: "UNLEARNING_INCOMPLETE",
    status: 409,
    retryable: false,
    message: "Unlearning has not finished for this experiment.",
  },
  {
    test: /no fl history found|no [a-z ]*(checkpoint|model) (found|exists)|no trained|checkpoint.*(not found|missing)|no such file.*\.pt/i,
    code: "MODEL_UNAVAILABLE",
    status: 404,
    retryable: false,
    message: "No trained checkpoint exists for this configuration.",
  },
  {
    test: /no partition found/i,
    code: "PARTITION_UNAVAILABLE",
    status: 404,
    retryable: false,
    message: "No data partition exists for this experiment yet.",
  },
  {
    test: /unknown dataset|failed to download|urlopen error|name or service not known|http error \d{3}|dataset.*(not found|unavailable|could not be loaded)|can't find dataset/i,
    code: "DATASET_UNAVAILABLE",
    status: 503,
    retryable: true,
    message: "Dataset could not be loaded.",
  },
];

// What a generic (unrecognised) failure is called, per stage.
const STAGE_DEFAULTS = {
  partition: { code: "PARTITION_FAILED", message: "Partitioning failed." },
  training: { code: "TRAINING_FAILED", message: "Training failed." },
  unlearning: { code: "UNLEARNING_FAILED", message: "Unlearning failed." },
  evaluation: { code: "EVALUATION_FAILED", message: "Evaluation failed." },
  retraining: { code: "RETRAINING_FAILED", message: "Retraining comparison failed." },
};

/**
 * @param {object} args
 * @param {"partition"|"training"|"unlearning"|"evaluation"|"retraining"} args.stage
 * @param {string} [args.stderr]        raw stderr of the Python process
 * @param {Error}  [args.spawnError]    set if the process could not start at all
 * @param {string} [args.failedStage]   finer stage if the engine recorded one
 *                                      (e.g. "gradient_ascent" from unlearning_status.json)
 * @param {string} [args.persistedError] error text the engine itself persisted
 */
export function classifyFailure({ stage, stderr = "", spawnError = null, failedStage = null, persistedError = null }) {
  const fallback = STAGE_DEFAULTS[stage] || { code: "ENGINE_FAILED", message: "The engine failed." };

  if (spawnError) {
    return {
      http: 500,
      body: {
        error: "Could not start the compute engine.",
        code: "ENGINE_START_FAILED",
        stage: STAGE_LABELS[stage] || stage,
        detail: conciseDetail(spawnError.message),
        retryable: true,
      },
    };
  }

  const detail = conciseDetail(stderr) || persistedError || "";
  const haystack = `${stderr}\n${persistedError || ""}`;
  const rule = RULES.find((r) => r.test.test(haystack));
  const stageKey = failedStage || stage;

  if (rule) {
    return {
      http: rule.status,
      body: {
        error: rule.message,
        code: rule.code,
        stage: STAGE_LABELS[stageKey] || STAGE_LABELS[stage] || stage,
        detail,
        retryable: rule.retryable,
      },
    };
  }

  return {
    http: 400,
    body: {
      error: fallback.message,
      code: fallback.code,
      stage: STAGE_LABELS[stageKey] || STAGE_LABELS[stage] || stage,
      detail,
      // An unrecognised failure is worth one retry (transient OOM,
      // flaky download) -- the UI still shows the real error text.
      retryable: true,
    },
  };
}

/** Send a classified failure on an Express response. */
export function sendFailure(res, args) {
  if (res.headersSent) return;
  const { http, body } = classifyFailure(args);
  res.status(http).json(body);
}

/** Output of a Python engine that was not valid JSON. */
export function sendBadOutput(res, stage) {
  if (res.headersSent) return;
  res.status(500).json({
    error: "The engine returned an unreadable response.",
    code: "ENGINE_BAD_OUTPUT",
    stage: STAGE_LABELS[stage] || stage,
    detail: "The Python engine finished but its output was not valid JSON.",
    retryable: true,
  });
}

/** A request body that is missing required fields. */
export function sendInvalidRequest(res, message) {
  res.status(400).json({ error: message, code: "INVALID_REQUEST", retryable: false });
}

/** A stored artifact that exists but cannot be parsed. */
export function sendCorruptArtifact(res, what, experimentId) {
  res.status(500).json({
    error: `The stored ${what} for experiment "${experimentId}" is unreadable.`,
    code: "ARTIFACT_CORRUPT",
    stage: STAGE_LABELS.artifact,
    detail: "The file exists but is not valid JSON (it may have been interrupted mid-write).",
    retryable: false,
  });
}

/** An artifact that exists but whose run never finished. */
export function sendIncompleteArtifact(res, what, experimentId, status) {
  res.status(409).json({
    error: `The stored ${what} for experiment "${experimentId}" is incomplete and will not be shown as a result.`,
    code: "ARTIFACT_INCOMPLETE",
    stage: STAGE_LABELS.artifact,
    detail: `status: ${status ?? "unknown"}`,
    retryable: false,
  });
}

export function sendNotFound(res, message, code = "NOT_FOUND") {
  res.status(404).json({ error: message, code, retryable: false });
}
