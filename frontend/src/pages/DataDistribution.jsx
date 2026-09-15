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
    <section>
      <h1>Data Distribution</h1>

      {!canPartition && (
        <p role="alert">Choose a dataset on Experiment Setup first.</p>
      )}

      {canPartition && (
        <>
          <p>
            Splitting <strong>{config.dataset}</strong> across{" "}
            <strong>{config.num_clients}</strong> clients (
            {config.partition_strategy === "iid" ? "IID" : "Non-IID"}, seed{" "}
            {config.seed}).
          </p>
          <button onClick={runPartitioning} disabled={loading}>
            {loading ? "Partitioning…" : "Run Partitioning"}
          </button>
        </>
      )}

      {error && <p role="alert">Could not partition dataset: {error}</p>}

      {partition && <PartitionSummary partition={partition} />}

      {partition && <ClientCardGrid partition={partition} />}

      {partition && <DistributionHeatmap partition={partition} />}
    </section>
  );
}
