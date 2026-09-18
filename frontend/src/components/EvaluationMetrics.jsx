// Page 7 — Evaluation metric cards (Dashboard Spec Ch.21-22, Phase 10).
// Four before/after metric cards (global accuracy, forget-client
// accuracy, retained-client accuracy, MIA success) plus a runtime
// breakdown card. Values are always the real measured before/after
// numbers from core.evaluation -- nothing here is estimated.
//
// The dedicated grouped-bar "Before vs After Visualization" (Ch.23)
// and full-retraining comparison (Ch.24) are a separate, later
// screen (Phase 11 / RetrainingComparison.jsx) -- this component is
// just Page 7's four metric cards + runtime.

function pct(value) {
  return `${(value * 100).toFixed(2)}%`;
}

function delta(before, after) {
  const diff = (after - before) * 100;
  const sign = diff > 0 ? "+" : "";
  return `${sign}${diff.toFixed(2)} pts`;
}

function MetricCard({ label, before, after, goodDirection, note }) {
  const diff = after - before;
  // goodDirection: "up" means higher-after is the desired outcome
  // (global/retained accuracy), "down" means lower-after is desired
  // (MIA success -- should move toward chance after effective
  // forgetting). Neither direction is enforced -- just colored so a
  // regression is visible at a glance, per Ch.23: "If a metric gets
  // worse, show that honestly."
  const improved = goodDirection === "up" ? diff >= 0 : diff <= 0;
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</h3>
      <dl className="mt-3 space-y-1.5">
        <div className="flex items-baseline justify-between">
          <dt className="text-xs text-gray-500">Before</dt>
          <dd className="text-sm font-semibold text-gray-900">{pct(before)}</dd>
        </div>
        <div className="flex items-baseline justify-between">
          <dt className="text-xs text-gray-500">After</dt>
          <dd className="text-sm font-semibold text-gray-900">{pct(after)}</dd>
        </div>
      </dl>
      <p className={`mt-3 text-xs font-medium ${improved ? "text-emerald-700" : "text-rose-700"}`}>
        {delta(before, after)}
      </p>
      {note && <p className="mt-1 text-xs text-gray-400">{note}</p>}
    </div>
  );
}

export default function EvaluationMetrics({ before, after, runtime }) {
  return (
    <section aria-labelledby="evaluation-metrics-heading" className="space-y-4">
      <div>
        <h2 id="evaluation-metrics-heading" className="text-base font-semibold text-gray-900">
          Evaluation
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          All five metrics, measured before and after Gradient Ascent + Knowledge Distillation.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Global Accuracy"
          before={before.global_accuracy}
          after={after.global_accuracy}
          goodDirection="up"
        />
        <MetricCard
          label="Forget-Client Accuracy"
          before={before.forget_client_accuracy}
          after={after.forget_client_accuracy}
          goodDirection="down"
          note="Should drop if the client's information was actually removed."
        />
        <MetricCard
          label="Retained-Client Accuracy"
          before={before.retained_client_accuracy}
          after={after.retained_client_accuracy}
          goodDirection="up"
          note="Mean across every non-target client."
        />
        <MetricCard
          label="MIA Success"
          before={before.mia_success}
          after={after.mia_success}
          goodDirection="down"
          note="50% = chance level (attacker can no longer tell)."
        />
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Runtime</h3>
        <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-gray-500">Gradient Ascent</dt>
            <dd className="mt-0.5 text-sm font-semibold text-gray-900">
              {runtime.gradient_ascent_seconds != null ? `${runtime.gradient_ascent_seconds.toFixed(1)}s` : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Knowledge Distillation</dt>
            <dd className="mt-0.5 text-sm font-semibold text-gray-900">
              {runtime.knowledge_distillation_seconds != null
                ? `${runtime.knowledge_distillation_seconds.toFixed(1)}s`
                : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Total Unlearning Time</dt>
            <dd className="mt-0.5 text-sm font-semibold text-gray-900">
              {runtime.total_unlearning_seconds != null ? `${runtime.total_unlearning_seconds.toFixed(1)}s` : "—"}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
