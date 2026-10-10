import { useEffect, useState } from "react";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import { apiFetch, errorFromResponse } from "../lib/api.js";
import ErrorPanel from "../components/ErrorPanel.jsx";
import ProvenanceBadge from "../components/ProvenanceBadge.jsx";
import ExperimentConfigPanel from "../components/ExperimentConfigPanel.jsx";
import DemoReplayNote from "../components/DemoReplayNote.jsx";
import PartitionSummary from "../components/PartitionSummary.jsx";
import ClientCardGrid from "../components/ClientCardGrid.jsx";
import DistributionHeatmap from "../components/DistributionHeatmap.jsx";

export default function DataDistribution() {
  const { config, refreshStages, appMode } = useExperimentConfig();
  const demo = appMode === "demo";
  const [partition, setPartition] = useState(null);
  const [resultKind, setResultKind] = useState(null); // "measured" | "precomputed"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const canPartition = Boolean(config.dataset);

  // Phase 15: a stored experiment's partition is loaded and shown
  // (labelled Precomputed) instead of the page staying empty until
  // "Run Partitioning" is pressed. That empty page meant a loaded or
  // demo experiment could not be replayed from the first screen.
  useEffect(() => {
    setPartition(null);
    setResultKind(null);
    setError(null);
    if (!config.experiment_id) return undefined;
    let ignore = false;
    fetch(`/api/partition/${encodeURIComponent(config.experiment_id)}`)
      .then(async (res) => {
        if (ignore) return;
        if (res.ok) {
          const data = await res.json();
          setPartition(data.partition);
          setResultKind("precomputed");
        } else if (res.status !== 404) {
          // 404 just means "not partitioned yet"; anything else is shown.
          const failure = await errorFromResponse(res);
          if (!ignore) setError(failure);
        }
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, [config.experiment_id]);

  async function runPartitioning() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch("/api/partition", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset: config.dataset,
          num_clients: config.num_clients,
          partition_strategy: config.partition_strategy,
          seed: config.seed,
          experiment_id: config.experiment_id,
        }),
      });
      setPartition(data.partition);
      setResultKind("measured");
      refreshStages();
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Data Distribution</h1>
        {resultKind && <ProvenanceBadge kind={resultKind} className="shrink-0" />}
      </div>

      {demo && <DemoReplayNote stage="data partition" hasResult={!!partition} />}

      {!demo && !canPartition && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Choose a dataset on Experiment Setup first.
        </p>
      )}

      {!demo && canPartition && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Splitting <strong className="font-semibold">{config.dataset}</strong> across{" "}
            <strong className="font-semibold">{config.num_clients}</strong> clients (
            {config.partition_strategy === "iid" ? "IID" : "Non-IID"}, seed {config.seed}).
          </p>
          <button
            onClick={runPartitioning}
            disabled={loading}
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Partitioning…" : "Run Partitioning"}
          </button>
        </div>
      )}

      <ErrorPanel error={error} onRetry={runPartitioning} />

      {partition && <PartitionSummary partition={partition} />}
      {partition && <ClientCardGrid partition={partition} />}
      {partition && <DistributionHeatmap partition={partition} />}

      <ExperimentConfigPanel experimentId={config.experiment_id} />
    </section>
  );
}
