import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import GlobalModelSummary from "../components/GlobalModelSummary.jsx";
import ClientCardGrid from "../components/ClientCardGrid.jsx";
import { ApiError, errorFromResponse } from "../lib/api.js";
import ErrorPanel from "../components/ErrorPanel.jsx";
import ProvenanceBadge from "../components/ProvenanceBadge.jsx";
import ExperimentConfigPanel from "../components/ExperimentConfigPanel.jsx";

// Page 5 -- Global Model & Target Client Selection (Dashboard Spec Ch.11).
//
// Both pieces of state this page needs -- the trained fl_history (Phase
// 05) and the partition's client cards (Phase 04) -- already exist on
// disk for this experiment_id by the time someone reaches this page, so
// it just re-reads them (GET, not POST) rather than re-running anything.
export default function ClientSelection() {
  const { config, updateConfig } = useExperimentConfig();
  const navigate = useNavigate();
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
        // 404 = nothing stored yet. Anything else (corrupt file, server
        // trouble) is a real failure and is shown as one.
        const failed = [trainingRes, partitionRes].find((r) => !r.ok && r.status !== 404);
        if (failed) {
          const failure = await errorFromResponse(failed);
          if (!ignore) {
            setError(failure);
            setStatus("error");
          }
          return;
        }
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
        setError(err);
        setStatus("error");
      });

    return () => {
      ignore = true;
    };
  }, [config.experiment_id]);

  return (
    <section className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Client Selection</h1>
          <p className="mt-1 text-sm text-gray-500">
            Review the trained global model, then pick which client's data it should forget.
          </p>
        </div>
        {status === "ready" && <ProvenanceBadge kind="precomputed" className="shrink-0" />}
      </div>

      {status === "loading" && <p className="text-sm text-gray-500">Loading global model…</p>}

      {status === "missing" && (
        <ErrorPanel
          error={new ApiError({
            message: "No trained checkpoint exists for this configuration.",
            code: "MODEL_UNAVAILABLE",
            retryable: false,
          })}
        />
      )}

      {status === "error" && <ErrorPanel error={error} />}

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
            <div className="flex flex-wrap items-center gap-4">
              <p className="text-sm text-gray-700">
                Client <strong className="font-semibold">{config.target_client_id}</strong> is set as the
                target for unlearning.
              </p>
              {/* Dashboard Spec Ch.70: "Remove Influence button available".
                  It opens the Unlearning step for this client; the run
                  itself still starts there, so nothing is removed by
                  just clicking a client card. */}
              <button
                type="button"
                onClick={() => navigate("/unlearning")}
                className="rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400"
              >
                Remove Influence of Client {config.target_client_id} →
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Select a client card above to set it as the unlearning target.</p>
          )}
        </>
      )}

      <ExperimentConfigPanel experimentId={config.experiment_id} />
    </section>
  );
}
