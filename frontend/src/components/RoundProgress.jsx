// Round progress bar + live per-client checklist (Dashboard Spec Ch.9).
const STAGE_LABEL = {
  idle: "Waiting to start",
  clients: "Local training",
  aggregating: "Aggregating (FedAvg)",
  updated: "Global model updated",
  done: "Round complete",
};

export default function RoundProgress({ currentRound, totalRounds, clients, stage, progress, replay }) {
  const aggregationDone = stage === "aggregating" || stage === "updated" || stage === "done";
  const modelUpdated = stage === "updated" || stage === "done";

  return (
    <section
      aria-labelledby="round-progress-heading"
      className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
    >
      <div className="flex items-center justify-between">
        <h2 id="round-progress-heading" className="text-base font-semibold text-gray-900">
          {replay ? "Replaying Federated Training" : "Federated Training"}
        </h2>
        <span className="text-sm font-medium text-gray-500">
          Round {currentRound} / {totalRounds}
        </span>
      </div>

      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-indigo-600 transition-[width] duration-150 ease-linear"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-gray-500">{STAGE_LABEL[stage] || STAGE_LABEL.idle}</p>

      <div className="mt-6 grid gap-6 sm:grid-cols-[1fr_auto]">
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-gray-500">Client Updates</h3>
          <ul className="mt-2 flex flex-wrap gap-2">
            {clients.map((c) => (
              <li
                key={c.client_id}
                className={`flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium ${
                  c.completed
                    ? "border-green-200 bg-green-50 text-green-700"
                    : "border-gray-200 bg-gray-50 text-gray-400"
                }`}
              >
                <span aria-hidden="true">{c.completed ? "✓" : "…"}</span>
                Client {c.client_id}
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-3 sm:w-44">
          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-gray-500">Aggregation</h3>
            <p className={`mt-1 text-sm font-medium ${aggregationDone ? "text-green-700" : "text-gray-400"}`}>
              {aggregationDone ? "✓ FedAvg" : "… FedAvg"}
            </p>
          </div>
          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-gray-500">Global Model</h3>
            <p className={`mt-1 text-sm font-medium ${modelUpdated ? "text-green-700" : "text-gray-400"}`}>
              {modelUpdated ? "✓ Updated" : "… Updated"}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
