import { useEffect, useState } from "react";
import DatasetCard from "../components/DatasetCard.jsx";
import ExperimentConfigForm from "../components/ExperimentConfigForm.jsx";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";

export default function ExperimentSetup() {
  const [datasets, setDatasets] = useState([]);
  const [error, setError] = useState(null);
  const { config, updateConfig } = useExperimentConfig();

  useEffect(() => {
    fetch("/api/datasets")
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res.json();
      })
      .then((data) => setDatasets(data.datasets))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <section className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Experiment Setup</h1>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">Choose a dataset</h2>
        {error && (
          <p role="alert" className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            Could not load datasets: {error}
          </p>
        )}
        <div className="mt-4 flex flex-wrap gap-4">
          {datasets.map((dataset) => (
            <DatasetCard
              key={dataset.id}
              dataset={dataset}
              selected={config.dataset === dataset.id}
              onSelect={(id) => updateConfig({ dataset: id })}
            />
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">Configure the experiment</h2>
        <div className="mt-4">
          <ExperimentConfigForm />
        </div>
      </div>
    </section>
  );
}
