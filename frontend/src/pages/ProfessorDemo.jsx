import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../lib/api.js";
import ErrorPanel from "../components/ErrorPanel.jsx";
import ProvenanceBadge from "../components/ProvenanceBadge.jsx";
import { DEMO_STEPS } from "../components/DemoGuideBar.jsx";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";

// Phase 15 -- Professor Demo Mode launcher (Dashboard Spec Ch.37).
//
// Rules this page enforces:
//  * it only offers experiments whose ENTIRE story is stored
//    (partition -> training -> unlearning -> evaluation -> retraining
//    comparison), so the demo can be replayed with no GPU and no
//    backend reachable;
//  * it never trains anything -- START DEMO only loads a stored
//    experiment and opens the first page;
//  * nothing here is invented: the cards show the stored experiment's
//    own dataset, client count, target client and seed.

export default function ProfessorDemo() {
  const { config, loadExperiment, setAppMode } = useExperimentConfig();
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState(null);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  const load = useCallback(() => {
    setError(null);
    apiFetch("/api/experiments?replayable_only=true")
      .then((body) => {
        setExperiments(body.experiments);
        setSelectedId((cur) => cur ?? body.experiments.find((e) => e.experiment_id === config.experiment_id)?.experiment_id ?? body.experiments[0]?.experiment_id ?? null);
      })
      .catch(setError);
  }, [config.experiment_id]);

  useEffect(load, [load]);

  const selected = experiments?.find((e) => e.experiment_id === selectedId) ?? null;

  function startDemo() {
    if (!selected) return;
    loadExperiment(selected);
    setAppMode("demo");
    navigate(DEMO_STEPS[0].path);
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-2xl font-semibold text-gray-900">Professor Demo</h2>
        <ProvenanceBadge kind="precomputed" />
      </div>
      <p className="mt-2 max-w-3xl text-gray-600">
        A guided ~10 minute walkthrough that replays a stored experiment from start to finish. It does not train anything, so
        it works even with no GPU or live backend.
      </p>

      <ErrorPanel className="mt-6" error={error} onRetry={load} />

      {!error && experiments === null && <p className="mt-6 text-sm text-gray-500">Looking for stored experiments…</p>}

      {experiments && experiments.length === 0 && (
        <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-900">No complete stored experiment found.</p>
          <p className="mt-1 text-sm text-amber-800">
            A demo needs one experiment that has finished every stage. In Research Mode, run: Setup → Data Distribution →
            Federated Learning → Client Selection → Unlearning → Evaluation → Retraining Comparison. It will then appear here.
          </p>
        </div>
      )}

      {experiments && experiments.length > 0 && (
        <>
          <h3 className="mt-8 text-sm font-semibold uppercase tracking-wide text-gray-500">Choose the demo experiment</h3>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {experiments.map((e) => {
              const active = e.experiment_id === selectedId;
              return (
                <li key={e.experiment_id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(e.experiment_id)}
                    aria-pressed={active}
                    className={`w-full rounded-lg border p-4 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                      active ? "border-indigo-500 bg-indigo-50" : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                  >
                    <p className="text-sm font-semibold text-gray-900">{e.dataset} · {e.num_clients} clients</p>
                    <p className="mt-1 text-xs text-gray-600">
                      {e.partition_strategy === "iid" ? "IID" : "Non-IID"} · {e.model} · {e.federated_rounds} rounds · seed {e.seed}
                    </p>
                    <p className="mt-1 text-xs text-gray-600">Target client: {e.target_client_id ?? "—"}</p>
                    <p className="mt-1 truncate font-mono text-[11px] text-gray-400">{e.experiment_id}</p>
                  </button>
                </li>
              );
            })}
          </ul>

          <button
            type="button"
            onClick={startDemo}
            disabled={!selected}
            className="mt-6 rounded-md bg-indigo-600 px-6 py-3 text-base font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
          >
            START DEMO
          </button>

          <h3 className="mt-10 text-sm font-semibold uppercase tracking-wide text-gray-500">The walkthrough</h3>
          <ol className="mt-3 space-y-2">
            {DEMO_STEPS.map((s, i) => (
              <li key={s.path} className="flex gap-3 text-sm text-gray-700">
                <span className="w-5 font-semibold text-indigo-600">{i + 1}.</span>
                <span>
                  <span className="font-medium">{s.label}</span> (~{s.minutes} min) — {s.say}
                </span>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
