import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";

// Page 9 -- Experiment History (Dashboard Spec Ch.32 Page 9, Phase 12).
//
// Every experiment that has at least a saved partition, regardless of
// how far it got, newest first (GET /api/experiments -- the Phase 12
// registry route aggregates each phase's own stored artifacts, so this
// page never duplicates state the Python core already owns). "Open"
// loads that experiment's id into the shared config and lands on
// Client Selection, the same re-entry point the Quick Demo uses --
// every later page (Unlearning, Evaluation, Comparison) already
// replays its own stored result instead of re-running anything, so
// this satisfies "loaded and replayed through Pages 5-8 without
// retraining" for whichever of those stages this experiment reached.

const STATUS_STYLES = {
  Compared: "bg-emerald-100 text-emerald-800",
  Evaluated: "bg-indigo-100 text-indigo-800",
  Unlearned: "bg-amber-100 text-amber-800",
  Trained: "bg-gray-100 text-gray-700",
  Partitioned: "bg-gray-100 text-gray-500",
};

function formatDate(ms) {
  if (!ms) return "—";
  return new Date(ms).toLocaleString();
}

export default function ExperimentHistory() {
  const navigate = useNavigate();
  const { loadExperiment } = useExperimentConfig();

  const [experiments, setExperiments] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    fetch("/api/experiments")
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!ignore) {
          setExperiments(data.experiments);
          setStatus("ready");
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message);
          setStatus("error");
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const openExperiment = useCallback(
    (experiment) => {
      loadExperiment(experiment);
      navigate("/client-selection");
    },
    [loadExperiment, navigate]
  );

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Experiment History</h1>
        <p className="mt-1 text-sm text-gray-500">
          Every experiment that has been partitioned, trained, unlearned, evaluated, or compared
          against retraining. Reopen any of them to pick up where it left off.
        </p>
      </div>

      {status === "loading" && <p className="text-sm text-gray-500">Loading experiment history…</p>}
      {status === "error" && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          Could not load experiment history: {error}
        </p>
      )}
      {status === "ready" && experiments.length === 0 && (
        <p className="text-sm text-gray-500">
          No experiments yet -- start one from the Overview page to see it here.
        </p>
      )}

      {status === "ready" && experiments.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Experiment</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Dataset</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Clients</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Target</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Updated</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {experiments.map((experiment) => (
                <tr key={experiment.experiment_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-900">{experiment.experiment_id}</td>
                  <td className="px-4 py-3 text-gray-600">{experiment.dataset ?? "—"}</td>
                  <td className="px-4 py-3 text-gray-600">{experiment.num_clients ?? "—"}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {experiment.target_client_id !== null && experiment.target_client_id !== undefined
                      ? `C${experiment.target_client_id}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        STATUS_STYLES[experiment.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {experiment.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">{formatDate(experiment.updated_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => openExperiment(experiment)}
                      className="rounded-md border border-gray-200 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50"
                    >
                      Open
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
