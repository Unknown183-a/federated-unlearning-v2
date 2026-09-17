import MetricLineChart from "./MetricLineChart.jsx";

// Gradient Ascent's own live panel (Dashboard Spec Ch.15-16). Every
// number here comes from a real, already-measured step in the
// backend's step_history -- `currentStep` only ever points at a step
// that has actually happened (Phase 08's real values, replayed
// progressively rather than streamed -- see Unlearning.jsx).
function Bar({ label, value, colorClass }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div>
      <div className="flex items-baseline justify-between text-xs">
        <span className="font-medium uppercase tracking-wide text-gray-500">{label}</span>
        <span className="font-semibold text-gray-900">{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className={`h-full rounded-full transition-[width] duration-150 ease-linear ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function GradientAscentPanel({ targetClientId, currentStep, totalSteps, revealedHistory }) {
  const latest = revealedHistory[revealedHistory.length - 1];
  const lossData = revealedHistory.map((s) => ({ round: s.step, value: s.loss }));

  return (
    <section aria-labelledby="ga-panel-heading" className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="ga-panel-heading" className="text-base font-semibold text-gray-900">
            Gradient Ascent
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Target Client: <strong className="font-semibold text-gray-900">Client {targetClientId}</strong>
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-800">
          Removing client influence…
        </span>
      </div>

      <p className="mt-3 text-sm text-gray-600">
        Ascending (not descending) the loss on the target client&rsquo;s own data, so the model
        gets deliberately worse at it -- undoing what it picked up from that client during FedAvg.
      </p>

      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-rose-600 transition-[width] duration-150 ease-linear"
          style={{ width: `${totalSteps ? Math.round((currentStep / totalSteps) * 100) : 0}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-gray-500">
        Iteration {currentStep} / {totalSteps}
      </p>

      {latest && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Bar label="Target Client Loss" value={Math.min(latest.loss / 4, 1)} colorClass="bg-rose-600" />
          <Bar label="Target Client Accuracy" value={latest.accuracy} colorClass="bg-gray-500" />
        </div>
      )}

      <div className="mt-6">
        <MetricLineChart
          title="Target-Client Loss vs Iteration"
          data={lossData}
          totalRounds={totalSteps}
          color="#e11d48"
          formatY={(v) => v.toFixed(2)}
          yLabel="loss"
          emptyHint="Waiting for the first ascent step…"
        />
      </div>
    </section>
  );
}
