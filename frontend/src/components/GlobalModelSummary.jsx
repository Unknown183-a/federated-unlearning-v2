const MODEL_LABEL = {
  cnn: "CNN",
  resnet: "ResNet",
};

// Presents the trained global model as a first-class object (Phase 07
// Ch.11): architecture, final accuracy/loss, and the experiment it came
// from. `history` is the same fl_history shape Phase 06 consumes.
export default function GlobalModelSummary({ history }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-base font-semibold text-gray-900">Global Model</h2>
      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Architecture</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {MODEL_LABEL[history.model] || history.model}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Dataset</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{history.dataset}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Experiment ID</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{history.experiment_id}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Final Accuracy</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {(history.final_accuracy * 100).toFixed(1)}%
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Final Loss</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{history.final_loss.toFixed(3)}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Rounds Trained</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {history.rounds} × {history.local_epochs} local epoch(s)
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Clients</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{history.num_clients}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Seed</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{history.seed}</dd>
        </div>
      </dl>
    </div>
  );
}
