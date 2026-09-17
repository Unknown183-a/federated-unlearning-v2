// Server/client FedAvg loop diagram (Dashboard Spec Ch.8 -- "This
// diagram must be visible in the dashboard"). Plain flexbox rather
// than SVG since the shapes are simple boxes and arrows; stage
// highlighting mirrors whatever RoundProgress is showing.
const MAX_VISIBLE_CLIENTS = 6;

export default function FedAvgDiagram({ clients, stage }) {
  const visible = clients.slice(0, MAX_VISIBLE_CLIENTS);
  const overflow = clients.length - visible.length;
  const trainingActive = stage === "clients";
  const aggregating = stage === "aggregating";
  const updated = stage === "updated" || stage === "done";

  return (
    <section
      aria-labelledby="fedavg-diagram-heading"
      className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
    >
      <h2 id="fedavg-diagram-heading" className="text-base font-semibold text-gray-900">
        FedAvg Loop
      </h2>
      <div className="mt-6 flex flex-col items-center gap-2">
        <div
          className={`rounded-md border-2 px-4 py-2 text-center text-sm font-semibold transition-colors ${
            updated ? "border-indigo-600 bg-indigo-50 text-indigo-800" : "border-gray-300 bg-gray-50 text-gray-600"
          }`}
        >
          Server — Global Model
        </div>
        <span className="text-xs text-gray-400">↓ broadcast global model ↓</span>

        <div className="flex flex-wrap justify-center gap-3">
          {visible.map((c) => (
            <div
              key={c.client_id}
              className={`rounded-md border px-3 py-2 text-center text-xs font-medium transition-colors ${
                c.completed
                  ? "border-green-300 bg-green-50 text-green-700"
                  : trainingActive
                  ? "animate-pulse border-indigo-400 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 bg-gray-50 text-gray-500"
              }`}
            >
              Client {c.client_id}
              <div className="text-[10px] font-normal text-gray-400">local data · local train</div>
            </div>
          ))}
          {overflow > 0 && (
            <div className="flex items-center rounded-md border border-dashed border-gray-300 px-3 py-2 text-xs text-gray-400">
              +{overflow} more
            </div>
          )}
        </div>

        <span className="text-xs text-gray-400">↑ model updates ↑</span>
        <div
          className={`rounded-md border-2 px-4 py-2 text-center text-sm font-semibold transition-colors ${
            aggregating || updated
              ? "border-indigo-600 bg-indigo-50 text-indigo-800"
              : "border-gray-300 bg-gray-50 text-gray-600"
          }`}
        >
          FedAvg
        </div>
        <span className="text-xs text-gray-400">↓ updated global model ↓</span>
        <div className={`text-sm font-medium ${updated ? "text-indigo-700" : "text-gray-400"}`}>
          {updated ? "Global model updated — next round" : "Waiting for this round to complete"}
        </div>
      </div>
    </section>
  );
}
