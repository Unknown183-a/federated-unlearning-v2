import { Link } from "react-router-dom";
import { toApiError } from "../lib/api.js";

// Phase 15 -- the one error display (Dashboard Spec Ch.43).
//
// It answers three questions in plain words: what failed, which stage
// it failed in, and what can be done next. The technical text is kept
// but tucked behind "Technical details" so a projector audience sees a
// calm message first. `onRetry` is only offered when the failure could
// plausibly succeed on a second try.

const ACTIONS = {
  DATASET_UNAVAILABLE: {
    title: "Dataset could not be loaded",
    hint: "Check the dataset files or your connection, then try again.",
  },
  MODEL_UNAVAILABLE: {
    title: "No trained model for this configuration",
    hint: "Train this configuration first, or open a stored experiment that already has a trained model.",
    links: [
      { to: "/training", label: "Run Training" },
      { to: "/history", label: "Select Another Experiment" },
    ],
  },
  PARTITION_UNAVAILABLE: {
    title: "No data partition yet",
    hint: "Create the partition on the Data Distribution page first.",
    links: [{ to: "/distribution", label: "Go to Data Distribution" }],
  },
  CLIENT_UNAVAILABLE: {
    title: "That client is not available",
    hint: "Pick a different client for this experiment.",
    links: [{ to: "/client-selection", label: "Select Another Client" }],
  },
  UNLEARNING_INCOMPLETE: {
    title: "Unlearning has not finished",
    hint: "Evaluation needs a completed unlearning run.",
    links: [{ to: "/unlearning", label: "Return to Unlearning" }],
  },
  UNLEARNING_FAILED: {
    title: "Unlearning failed",
    hint: "The model was not changed. You can retry, or go back and choose a stored experiment.",
    links: [
      { to: "/client-selection", label: "Return to Experiment" },
      { to: "/history", label: "Select Another Experiment" },
    ],
  },
  EVALUATION_FAILED: {
    title: "Evaluation failed",
    hint: "No results are shown, because incomplete metrics would be misleading.",
  },
  ARTIFACT_INCOMPLETE: {
    title: "This stored result is incomplete",
    hint: "It was not shown, because incomplete metrics would be misleading. Re-run that stage or pick another experiment.",
    links: [{ to: "/history", label: "Select Another Experiment" }],
  },
  ARTIFACT_CORRUPT: {
    title: "This stored result is unreadable",
    hint: "The file may have been interrupted while it was being saved.",
    links: [{ to: "/history", label: "Select Another Experiment" }],
  },
  BACKEND_UNAVAILABLE: {
    title: "The compute backend is unavailable",
    hint: "Stored experiments can still be replayed. Choose another backend, or use Demo (Precomputed).",
  },
  BACKEND_NOT_SUPPORTED: {
    title: "This backend only replays stored experiments",
    hint: "Choose Local or a GPU backend to run something new, or keep replaying the stored result.",
  },
  ENGINE_TIMEOUT: {
    title: "The run took too long",
    hint: "It was stopped. Try again, or replay a stored experiment instead.",
  },
  SERVER_UNREACHABLE: {
    title: "The dashboard server is not reachable",
    hint: "Start the backend and try again.",
  },
};

export default function ErrorPanel({ error, onRetry, className = "" }) {
  if (!error) return null;
  const err = toApiError(error);
  const known = ACTIONS[err.code];
  const title = known?.title || err.message;
  // Retry only when the backend (or the network) says it might help.
  const canRetry = typeof onRetry === "function" && err.retryable;

  return (
    <div
      role="alert"
      data-error-code={err.code}
      className={`rounded-lg border border-red-200 bg-red-50 p-4 ${className}`}
    >
      <p className="text-sm font-semibold text-red-800">{title}</p>
      {err.stage && (
        <p className="mt-0.5 text-xs font-medium uppercase tracking-wide text-red-700">
          Failed at: {err.stage}
        </p>
      )}
      {known && err.message !== title && <p className="mt-2 text-sm text-red-800">{err.message}</p>}
      {known?.hint && <p className="mt-2 text-sm text-red-700">{known.hint}</p>}

      {(canRetry || known?.links) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {canRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-md bg-red-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
            >
              Retry
            </button>
          )}
          {(known?.links || []).map((l) => (
            <Link
              key={l.to + l.label}
              to={l.to}
              className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}

      {err.detail && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs font-medium text-red-700">Technical details</summary>
          <p className="mt-1 break-words font-mono text-xs text-red-800">{err.detail}</p>
        </details>
      )}
    </div>
  );
}
