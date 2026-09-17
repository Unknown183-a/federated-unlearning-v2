import { useState } from "react";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import PartitionSummary from "../components/PartitionSummary.jsx";
import ClientCardGrid from "../components/ClientCardGrid.jsx";
import DistributionHeatmap from "../components/DistributionHeatmap.jsx";

export default function DataDistribution() {
  const { config } = useExperimentConfig();
  const [partition, setPartition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const canPartition = Boolean(config.dataset);

  async function runPartitioning() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/partition", {
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
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Request failed: ${res.status}`);
      }
      const data = await res.json();
      setPartition(data.partition);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Data Distribution</h1>

      {!canPartition && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Choose a dataset on Experiment Setup first.
        </p>
      )}

      {canPartition && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Splitting <strong className="font-semibold">{config.dataset}</strong> across{" "}
            <strong className="font-semibold">{config.num_clients}</strong> clients (
            {config.partition_strategy === "iid" ? "IID" : "Non-IID"}, seed{" "}
            {config.seed}).
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

      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          Could not partition dataset: {error}
        </p>
      )}

      {partition && <PartitionSummary partition={partition} />}
      {partition && <ClientCardGrid partition={partition} />}
      {partition && <DistributionHeatmap partition={partition} />}
    </section>
  );
}
