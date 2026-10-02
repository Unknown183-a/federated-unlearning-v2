import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import ModelLibraryCard from "../components/ModelLibraryCard.jsx";

// Page 1 -- Overview (Dashboard Spec Ch.1-2, Ch.32 Page 1, Phase 12).
//
// The landing page's two large choices (Ch.2): a from-scratch
// "Complete Experiment" (Phases 01-11, starting at Setup) or a "Quick
// Demo" that skips straight to Client Selection using an
// already-trained model from the library (Ch.27-28). Both paths reuse
// the exact same downstream pages -- this page only decides which
// experiment_id those pages will read.

export default function Overview() {
  const navigate = useNavigate();
  const { loadExperiment } = useExperimentConfig();

  const [showLibrary, setShowLibrary] = useState(false);
  const [models, setModels] = useState([]);
  const [status, setStatus] = useState("idle"); // idle | loading | ready | error
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!showLibrary) return;
    let ignore = false;
    setStatus("loading");
    setError(null);
    fetch("/api/experiments?trained_only=true")
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!ignore) {
          setModels(data.experiments);
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
  }, [showLibrary]);

  const selectModel = useCallback(
    (experiment) => {
      loadExperiment(experiment);
      navigate("/client-selection");
    },
    [loadExperiment, navigate]
  );

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Federated Unlearning Lab</h1>
        <p className="mt-2 max-w-3xl text-sm text-gray-600">
          A dataset is distributed among multiple federated clients, a global model is learned
          without centralizing client data, a specific client's influence can then be targeted for
          removal, Gradient Ascent and Knowledge Distillation produce an unlearned model, and the
          resulting forgetting, retained utility, privacy behavior, and computational cost are
          evaluated against the original and retrained models.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900">Complete FL + Unlearning</h2>
          <p className="mt-2 flex-1 text-sm text-gray-500">
            Dataset → Partition → Federated Learning → Unlearning → Evaluation. Runs the full
            pipeline from scratch for a new experiment.
          </p>
          <button
            type="button"
            onClick={() => navigate("/setup")}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            Start Complete Experiment
          </button>
        </div>

        <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900">Quick Unlearning Demo</h2>
          <p className="mt-2 flex-1 text-sm text-gray-500">
            Pretrained Model → Client → Unlearn → Evaluation. Skips federated training by loading
            an already-trained model from the library.
          </p>
          <button
            type="button"
            onClick={() => setShowLibrary((v) => !v)}
            className="mt-4 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700"
          >
            {showLibrary ? "Hide Model Library" : "Start Quick Demo"}
          </button>
        </div>
      </div>

      {showLibrary && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900">Available Federated Models</h3>
          <p className="mt-1 text-sm text-gray-500">
            Pick an already-trained model to jump straight to Client Selection -- no training
            required.
          </p>

          {status === "loading" && <p className="mt-4 text-sm text-gray-500">Loading model library…</p>}
          {status === "error" && (
            <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              Could not load the model library: {error}
            </p>
          )}
          {status === "ready" && models.length === 0 && (
            <p className="mt-4 text-sm text-gray-500">
              No trained models yet -- run a Complete Experiment through Federated Learning first.
            </p>
          )}
          {status === "ready" && models.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-4">
              {models.map((experiment) => (
                <ModelLibraryCard key={experiment.experiment_id} experiment={experiment} onSelect={selectModel} />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
