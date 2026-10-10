// Phase 15 -- one fetch helper for the whole dashboard.
//
// Every page used to do `fetch(...)`, check `res.ok`, and throw
// `new Error(body.error)`. That threw away the structured fields the
// backend now sends (code, stage, detail, retryable) and turned a dead
// server into the cryptic "Unexpected token <" or "Failed to fetch".
// `apiFetch` keeps those fields on an ApiError so <ErrorPanel> can show
// the right message and the right recovery buttons (Spec Ch.43).

export class ApiError extends Error {
  constructor({ message, code, stage, detail, status, retryable }) {
    super(message);
    this.name = "ApiError";
    this.code = code || "UNKNOWN";
    this.stage = stage || null;
    this.detail = detail || "";
    this.status = status ?? null;
    this.retryable = retryable ?? true;
  }
}

/**
 * fetch + JSON, throwing ApiError on any failure.
 * Resolves with the parsed JSON body.
 */
export async function apiFetch(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch {
    // The request never reached the server at all.
    throw new ApiError({
      message: "The dashboard server could not be reached.",
      code: "SERVER_UNREACHABLE",
      detail: "Check that the backend is running (npm run dev in /backend).",
      retryable: true,
    });
  }

  let body = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (!res.ok) {
    throw new ApiError({
      message: body?.error || `The request failed (HTTP ${res.status}).`,
      code: body?.code || (body ? "UNKNOWN" : "BAD_RESPONSE"),
      stage: body?.stage,
      detail: body?.detail,
      status: res.status,
      retryable: body?.retryable,
    });
  }
  if (body === null) {
    throw new ApiError({
      message: "The server sent a response the dashboard could not read.",
      code: "BAD_RESPONSE",
      status: res.status,
      retryable: true,
    });
  }
  return body;
}

/** Wrap anything thrown (ApiError, TypeError, string) into an ApiError. */
export function toApiError(err) {
  if (err instanceof ApiError) return err;
  return new ApiError({
    message: err?.message || "Something went wrong.",
    code: "UNKNOWN",
    retryable: true,
  });
}

// A metrics block is only a real result if all four numbers are real
// probabilities. Used to refuse to draw half-finished results (Ch.43:
// "do not show incomplete metrics as valid final results").
const METRIC_KEYS = ["global_accuracy", "forget_client_accuracy", "retained_client_accuracy", "mia_success"];

export function isCompleteMetrics(block) {
  return (
    !!block &&
    METRIC_KEYS.every((k) => typeof block[k] === "number" && block[k] >= 0 && block[k] <= 1)
  );
}

export function isCompleteEvaluation(results) {
  return !!results && results.status === "complete" && isCompleteMetrics(results.before) && isCompleteMetrics(results.after);
}

/** Build an ApiError from a non-OK fetch Response (for loaders that use plain fetch). */
export async function errorFromResponse(res) {
  let body = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  return new ApiError({
    message: body?.error || `The request failed (HTTP ${res.status}).`,
    code: body?.code || "UNKNOWN",
    stage: body?.stage,
    detail: body?.detail,
    status: res.status,
    retryable: body?.retryable,
  });
}
