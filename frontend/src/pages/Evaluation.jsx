import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import EvaluationMetrics from "../components/EvaluationMetrics.jsx";

// Page 7 -- Evaluation (Dashboard Spec Ch.21-22, Ch.32 Page 7, Phase 10).
//
// Mirrors Unlearning.jsx's gating + stored-vs-measured pattern: a
// completed unlearning run (Phase 08+09) is required before evaluation
// can run at all, and a previously persisted result is loaded and
// shown as "Stored Experiment" rather than silently re-running the
// (real, non-trivial) accuracy/MIA computation on every page visit.

export default function Evaluation() {
  const { config } = useExperimentConfig();

  const [gateStatus, setGateStatus] = useState("loading"); // loading | ready | missing
  const [runStatus, setRunStatus] = useState("idle"); // idle | loading | error | ready
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [resultKind, setResultKind] = useState(null); // "measured" | "stored"

  // A completed unlearning run is required before evaluation can run.
  useEffect(() => {
    if (!config.experiment_id) return;
    let ignore = false;
    fetch(`/api/unlearning/${encodeURIComponent(config.experiment_id)}`)
      .then(async (res) => {
        if (ignore) return;
        if (!res.ok) return setGateStatus("missing");
        const data = await res.json();
        setGateStatus(data.status && data.status.status === "complete" ? "ready" : "missing");
      })
      .catch(() => {
        if (!ignore) setGateStatus("missing");
      });
    return () => {
      ignore = true;
    };
  }, [config.experiment_id]);

  // If this experiment already has persisted evaluation results, load
  // them instead of requiring a re-run.
  useEffect(() => {
    if (!config.experiment_id || gateStatus !== "ready") return;
    let ignore = false;
    fetch(`/api/evaluation/${encodeURIComponent(config.experiment_id)}`)
      .then(async (res) => {
        if (ignore || !res.ok) return;
        const data = await res.json();
        if (data.results && data.results.status === "complete") {
          setResultKind("stored");
          setResults(data.results);
          setRunStatus("ready");
        }
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, [config.experiment_id, gateStatus]);

  async function runEvaluation() {
    setRunStatus("loading");
    setError(null);
    setResults(null);
    try {
      const res = await fetch("/api/evaluation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experiment_id: config.experiment_id }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setResultKind("measured");
      setResults(data.results);
      setRunStatus("ready");
    } catch (err) {
      setError(err.message);
      setRunStatus("error");
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evaluation</h1>
          <p className="mt-1 text-sm text-gray-500">
            Global, forget-client, and retained-client accuracy, a Membership Inference Attack,
            and runtime -- measured before and after unlearning.
          </p>
        </div>
        {resultKind && (
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
              resultKind === "measured" ? "bg-indigo-100 text-indigo-800" : "bg-amber-100 text-amber-800"
            }`}
          >
            {resultKind === "measured" ? "Measured" : "Stored Experiment"}
          </span>
        )}
      </div>

      {gateStatus === "missing" && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No completed unlearning run found for this experiment yet -- finish{" "}
          <Link to="/unlearning" className="font-medium underline">
            Unlearning
          </Link>{" "}
          first.
        </p>
      )}

      {gateStatus === "ready" && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Run the Evaluation Engine for experiment{" "}
            <strong className="font-semibold">{config.experiment_id}</strong>.
          </p>
          <button
            onClick={runEvaluation}
            disabled={runStatus === "loading"}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {runStatus === "loading" ? "Evaluating…" : "Run Evaluation"}
          </button>
          {runStatus === "loading" && (
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-rose-600">
              <svg className="h-4 w-4 animate-spin text-rose-500" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <span>Live — computing accuracy and running the MIA on the server.</span>
            </div>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {results && (
        <EvaluationMetrics before={results.before} after={results.after} runtime={results.runtime} />
      )}
    </section>
  );
}
