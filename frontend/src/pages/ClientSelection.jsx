import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import GlobalModelSummary from "../components/GlobalModelSummary.jsx";
import ClientCardGrid from "../components/ClientCardGrid.jsx";

// Page 5 -- Global Model & Target Client Selection (Dashboard Spec Ch.11).
//
// Both pieces of state this page needs -- the trained fl_history (Phase
// 05) and the partition's client cards (Phase 04) -- already exist on
// disk for this experiment_id by the time someone reaches this page, so
// it just re-reads them (GET, not POST) rather than re-running anything.
export default function ClientSelection() {
  const { config, updateConfig } = useExperimentConfig();
  const [history, setHistory] = useState(null);
  const [partition, setPartition] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | missing | error
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!config.experiment_id) return;
    let ignore = false;
    setStatus("loading");
    setError(null);

    Promise.all([
      fetch(`/api/training/${encodeURIComponent(config.experiment_id)}`),
      fetch(`/api/partition/${encodeURIComponent(config.experiment_id)}`),
    ])
      .then(async ([trainingRes, partitionRes]) => {
        if (ignore) return;
        if (!trainingRes.ok || !partitionRes.ok) {
          setStatus("missing");
          return;
        }
        const trainingData = await trainingRes.json();
        const partitionData = await partitionRes.json();
        setHistory(trainingData.history);
        setPartition(partitionData.partition);
        setStatus("ready");
      })
      .catch((err) => {
        if (ignore) return;
        setError(err.message);
        setStatus("error");
      });

    return () => {
      ignore = true;
    };
  }, [config.experiment_id]);

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Client Selection</h1>
        <p className="mt-1 text-sm text-gray-500">
          Review the trained global model, then pick which client's data it should forget.
        </p>
      </div>

      {status === "loading" && <p className="text-sm text-gray-500">Loading global model…</p>}

      {status === "missing" && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No trained model found for this experiment yet — run training on{" "}
          <Link to="/training" className="font-medium underline">
            Federated Learning
          </Link>{" "}
          first.
        </p>
      )}

      {status === "error" && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          Could not load this experiment: {error}
        </p>
      )}

      {status === "ready" && history && (
        <>
          <GlobalModelSummary history={history} />

          <ClientCardGrid
            partition={partition}
            heading="Choose a Target Client"
            selectable
            selectedClientId={config.target_client_id}
            onSelect={(clientId) => updateConfig({ target_client_id: clientId })}
          />

          {config.target_client_id !== null && config.target_client_id !== undefined ? (
            <p className="text-sm text-gray-700">
              Client <strong className="font-semibold">{config.target_client_id}</strong> is set as the
              target for unlearning. Continue to{" "}
              <Link to="/unlearning" className="font-medium text-indigo-600 underline">
                Unlearning
              </Link>
              .
            </p>
          ) : (
            <p className="text-sm text-gray-500">Select a client card above to set it as the unlearning target.</p>
          )}
        </>
      )}
    </section>
  );
}
