// Phase 15 -- the one place a route launches a Python engine.
//
// Every POST route used to repeat the same ~25 lines of spawn /
// collect / parse / respond. Centralising it gives all of them the
// same structured failures (see errors.js), the same timeout, and the
// same "never leave the request hanging" guarantee.
import { spawn } from "child_process";
import { REPO_ROOT, readArtifact } from "./artifacts.js";
import { STAGE_LABELS, sendBadOutput, sendFailure } from "./errors.js";

// A live run that has not answered after this long is treated as a
// failure, so the dashboard shows an error and a fallback option
// instead of an endless spinner during a presentation. Spec Ch.37's
// "maximum practical demo" is ~10 minutes; the default leaves headroom.
const DEFAULT_TIMEOUT_MS = 15 * 60 * 1000;

function timeoutMs() {
  const fromEnv = Number(process.env.ENGINE_TIMEOUT_MS);
  return Number.isFinite(fromEnv) && fromEnv > 0 ? fromEnv : DEFAULT_TIMEOUT_MS;
}

/**
 * @param {object} opts
 * @param {string[]} opts.args          python arguments, e.g. ["-m", "core.federated.cli", ...]
 * @param {"partition"|"training"|"unlearning"|"evaluation"|"retraining"|"release"} opts.stage
 * @param {import("express").Response} opts.res
 * @param {string} [opts.experimentId]  lets an unlearning failure report *which* stage failed
 * @param {(parsed: any) => void} opts.onSuccess  called with the parsed JSON stdout
 */
export function runEngine({ args, stage, res, experimentId, onSuccess }) {
  const py = spawn(process.env.PYTHON_BIN || "python3", args, { cwd: REPO_ROOT });

  let stdout = "";
  let stderr = "";
  py.stdout.on("data", (chunk) => (stdout += chunk));
  py.stderr.on("data", (chunk) => (stderr += chunk));

  // On timeout, answer the browser immediately and then kill the
  // process -- do not wait for the process's own "close" event, because
  // a child that outlives its parent can keep the output pipes open and
  // delay that event long after the deadline.
  const timer = setTimeout(() => {
    if (!res.headersSent) {
      res.status(504).json({
        error: "The run took too long and was stopped.",
        code: "ENGINE_TIMEOUT",
        stage: STAGE_LABELS[stage] || stage,
        detail: `No result after ${Math.round(timeoutMs() / 1000)} seconds.`,
        retryable: true,
      });
    }
    py.kill("SIGKILL");
  }, timeoutMs());

  py.on("error", (spawnError) => {
    clearTimeout(timer);
    sendFailure(res, { stage, spawnError });
  });

  py.on("close", (code) => {
    clearTimeout(timer);
    if (res.headersSent) return;

    if (code !== 0) {
      // The unlearning engine records *which* of its two stages failed
      // (and why) in unlearning_status.json before it re-raises, so a
      // failure can say "Gradient Ascent" vs "Knowledge Distillation".
      let failedStage = null;
      let persistedError = null;
      if (stage === "unlearning" && experimentId) {
        const persisted = readArtifact(experimentId, "unlearning_status.json");
        if (persisted.state === "ok" && persisted.data.status === "failed") {
          failedStage = persisted.data.stage || null;
          persistedError = persisted.data.error || null;
        }
      }
      return sendFailure(res, { stage, stderr, failedStage, persistedError });
    }

    let parsed;
    try {
      parsed = JSON.parse(stdout);
    } catch {
      return sendBadOutput(res, stage);
    }
    onSuccess(parsed);
  });
}
