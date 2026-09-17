import MetricLineChart from "./MetricLineChart.jsx";

// Knowledge Distillation's live panel (Dashboard Spec Ch.17-18):
// teacher/student diagram, temperature, KD loss, and progress -- all
// from the real epoch_history the backend measured, revealed one
// epoch at a time (see Unlearning.jsx).
export default function KnowledgeDistillationPanel({
  temperature,
  alpha,
  currentEpoch,
  totalEpochs,
  revealedHistory,
}) {
  const latest = revealedHistory[revealedHistory.length - 1];
  const lossData = revealedHistory.map((e) => ({ round: e.epoch, value: e.kd_loss }));

  return (
    <section aria-labelledby="kd-panel-heading" className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 id="kd-panel-heading" className="text-base font-semibold text-gray-900">
        Knowledge Distillation
      </h2>
      <p className="mt-1 text-sm text-gray-500">
        Repairing collateral damage: the pre-ascent model teaches the post-ascent model back
        toward its original behavior on every client except the one being forgotten.
      </p>

      <div className="mt-5 flex flex-col items-center gap-1.5 text-center text-sm">
        <div className="rounded-md border-2 border-indigo-600 bg-indigo-50 px-4 py-2 font-semibold text-indigo-800">
          Original Model — Teacher
        </div>
        <span className="text-xs text-gray-400">↓ soft predictions ↓</span>
        <div className="rounded-md border-2 border-gray-400 bg-gray-50 px-6 py-3 font-semibold text-gray-700">
          KD Loss · Temperature {temperature}
        </div>
        <span className="text-xs text-gray-400">↓ update ↓</span>
        <div className="rounded-md border-2 border-teal-600 bg-teal-50 px-4 py-2 font-semibold text-teal-800">
          Unlearned Model — Student
        </div>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Temperature</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{temperature}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Hard-Label Weight (α)</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">{alpha}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Epoch</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {currentEpoch} / {totalEpochs}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Current KD Loss</dt>
          <dd className="mt-0.5 text-sm font-semibold text-gray-900">
            {latest ? latest.kd_loss.toFixed(3) : "—"}
          </dd>
        </div>
      </dl>

      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-teal-600 transition-[width] duration-150 ease-linear"
          style={{ width: `${totalEpochs ? Math.round((currentEpoch / totalEpochs) * 100) : 0}%` }}
        />
      </div>

      <div className="mt-6">
        <MetricLineChart
          title="KD Loss vs Epoch"
          data={lossData}
          totalRounds={totalEpochs}
          color="#0d9488"
          formatY={(v) => v.toFixed(2)}
          yLabel="kd loss"
          emptyHint="Waiting for the first distillation epoch…"
        />
      </div>
    </section>
  );
}
