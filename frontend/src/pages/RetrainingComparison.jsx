import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import RetrainingComparisonChart from "../components/RetrainingComparisonChart.jsx";
import RuntimeComparisonChart from "../components/RuntimeComparisonChart.jsx";

// Page 8 -- Retraining Comparison (Dashboard Spec Ch.23-25, Ch.32 Page 8,
// Phase 11).
//
// Prove unlearning was worth doing: compare the unlearned model against
// both the original model and a from-scratch retraining baseline that
// excludes the target client entirely. The retraining baseline is
// expensive (roughly as costly as the original training run) so, per
// Ch.37, it is run on demand rather than automatically -- this page
// mirrors Evaluation.jsx's gating + stored-vs-measured pattern, but
// gates on a *stored evaluation* (Phase 10) rather than re-measuring
// anything itself.

function ProtocolNote({ protocol }) {
  if (!protocol || protocol.hyperparameters_recorded) return null;
  return (
    <p className="mt-1 text-xs text-gray-400">
      This experiment's original training history predates Phase 11's lr/batch-size recording, so
      the retraining baseline used this project's standing defaults for those two settings.
    </p>
  );
}

export default function RetrainingComparison() {
  const { config } = useExperimentConfig();

  // loading | ready | missing -- "ready" means Phase 10's evaluation is stored.
  const [gateStatus, setGateStatus] = useState("loading");
  // idle | loading | error | ready
  const [runStatus, setRunStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [resultKind, setResultKind] = useState(null); // "measured" | "stored"

  useEffect(() => {
    if (!config.experiment_id) return;
    let ignore = false;
    fetch(`/api/evaluation/${encodeURIComponent(config.experiment_id)}`)
      .then(async (res) => {
        if (ignore) return;
        if (!res.ok) return setGateStatus("missing");
        const data = await res.json();
        setGateStatus(data.results && data.results.status === "complete" ? "ready" : "missing");
      })
      .catch(() => {
        if (!ignore) setGateStatus("missing");
      });
    return () => {
      ignore = true;
    };
  }, [config.experiment_id]);

  // If a retraining baseline is already stored for this experiment,
  // load the cheap comparison instead of requiring a re-run of the
  // expensive baseline.
  useEffect(() => {
    if (!config.experiment_id || gateStatus !== "ready") return;
    let ignore = false;
    fetch(`/api/retraining/${encodeURIComponent(config.experiment_id)}/comparison`)
      .then(async (res) => {
        if (ignore || !res.ok) return;
        const data = await res.json();
        if (data.comparison && data.comparison.status === "complete") {
          setResultKind("stored");
          setComparison(data.comparison);
          setRunStatus("ready");
        }
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, [config.experiment_id, gateStatus]);

  const runRetrainingBaseline = useCallback(async () => {
    setRunStatus("loading");
    setError(null);
    try {
      const res = await fetch("/api/retraining", {
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
      setComparison(data.comparison);
      setRunStatus("ready");
    } catch (err) {
      setError(err.message);
      setRunStatus("error");
    }
  }, [config.experiment_id]);

  return (
    <section className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Retraining Comparison</h1>
          <p className="mt-1 text-sm text-gray-500">
            Original vs Unlearned (GA + KD) vs a full-retraining-from-scratch baseline that
            excludes the target client entirely.
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
          No evaluation results found for this experiment yet -- finish{" "}
          <Link to="/evaluation" className="font-medium underline">
            Evaluation
          </Link>{" "}
          first.
        </p>
      )}

      {gateStatus === "ready" && runStatus !== "ready" && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Retrain from scratch, excluding this experiment's target client, for{" "}
            <strong className="font-semibold">{config.experiment_id}</strong>. This re-runs the
            full federated training protocol on the remaining clients, so it typically costs about
            as much time as the original training run.
          </p>
          <button
            onClick={runRetrainingBaseline}
            disabled={runStatus === "loading"}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {runStatus === "loading" ? "Retraining…" : "Run Retraining Baseline"}
          </button>
          {runStatus === "loading" && (
            <div className="mt-3 flex items-center gap-2 text-xs font-medium text-rose-600">
              <svg className="h-4 w-4 animate-spin text-rose-500" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <span>Live — retraining from scratch and re-evaluating on the server.</span>
            </div>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {comparison && (
        <>
          <RetrainingComparisonChart metrics={comparison.metrics} />
          <RuntimeComparisonChart runtime={comparison.runtime} />

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-semibold text-gray-900">Reading This Result</h3>
            <dl className="mt-3 grid gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Forgetting</dt>
                <dd className="mt-1 text-xs text-gray-600">
                  Target-client accuracy and MIA should both move toward the retrained baseline,
                  not stay close to the original.
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Utility</dt>
                <dd className="mt-1 text-xs text-gray-600">
                  Global and retained-client accuracy should stay close to both the original and
                  the retrained model.
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Efficiency</dt>
                <dd className="mt-1 text-xs text-gray-600">
                  Unlearning runtime should be a small fraction of full retraining -- shown above,
                  never assumed.
                </dd>
              </div>
            </dl>
            <p className="mt-3 text-xs text-gray-400">
              Retraining excluded client {comparison.target_client_id} and trained on{" "}
              {comparison.retraining_run.num_clients_trained} remaining client
              {comparison.retraining_run.num_clients_trained === 1 ? "" : "s"}. Retrained numbers
              come from that separate run, not from the original experiment.
            </p>
            <ProtocolNote protocol={comparison.retraining_run.protocol} />
          </div>
        </>
      )}
    </section>
  );
}
