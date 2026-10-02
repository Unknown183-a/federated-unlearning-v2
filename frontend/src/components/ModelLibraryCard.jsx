// One trained experiment in the Quick Demo's "AVAILABLE FEDERATED
// MODELS" library (Dashboard Spec Ch.27). Only ever shown for
// experiments with stages.trained === true, so "READY" here always
// means a real global_model.pt checkpoint is on disk -- never a
// placeholder.

function formatPercent(value) {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export default function ModelLibraryCard({ experiment, onSelect }) {
  return (
    <div className="w-64 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-900">
          {experiment.dataset ?? "Unknown dataset"}
        </h3>
        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-800">
          Ready
        </span>
      </div>
      <p className="mt-1 text-xs text-gray-400">{experiment.experiment_id}</p>
      <dl className="mt-3 space-y-1 text-xs text-gray-600">
        <div className="flex justify-between">
          <dt className="font-medium text-gray-700">Clients</dt>
          <dd>{experiment.num_clients ?? "—"}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium text-gray-700">Rounds</dt>
          <dd>{experiment.federated_rounds ?? "—"}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="font-medium text-gray-700">Accuracy</dt>
          <dd>{formatPercent(experiment.final_accuracy)}</dd>
        </div>
        {experiment.stages.unlearned && (
          <div className="flex justify-between">
            <dt className="font-medium text-gray-700">Already Unlearned</dt>
            <dd>Client {experiment.target_client_id}</dd>
          </div>
        )}
      </dl>
      <button
        type="button"
        onClick={() => onSelect(experiment)}
        className="mt-4 w-full rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
      >
        Select
      </button>
    </div>
  );
}
