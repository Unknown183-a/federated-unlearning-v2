// Runtime comparison bar (Page 8, Ch.25).
// "Use actual measured times. Do not claim a speedup unless measured."
// -- if either time is missing, no bars are drawn and no fraction is
// claimed; if unlearning was not actually faster, that is shown as-is
// rather than hidden or clamped.

function formatSeconds(seconds) {
  if (seconds == null) return "—";
  if (seconds >= 60) return `${(seconds / 60).toFixed(1)} min`;
  return `${seconds.toFixed(1)}s`;
}

export default function RuntimeComparisonChart({ runtime }) {
  const { unlearning_seconds, retraining_seconds, time_saved_fraction, unlearning_faster, speedup_factor } =
    runtime;

  const haveBoth = unlearning_seconds != null && retraining_seconds != null;
  const maxSeconds = haveBoth ? Math.max(unlearning_seconds, retraining_seconds, 1e-9) : 1;

  const bars = [
    { label: "Full Retraining", seconds: retraining_seconds, color: "#9ca3af" },
    { label: "Unlearning (GA + KD)", seconds: unlearning_seconds, color: "#6366f1" },
  ];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold text-gray-900">Runtime Comparison</h3>

      <div className="mt-4 space-y-3">
        {bars.map((bar) => (
          <div key={bar.label}>
            <div className="mb-1 flex items-baseline justify-between text-xs text-gray-500">
              <span>{bar.label}</span>
              <span className="font-semibold text-gray-900">{formatSeconds(bar.seconds)}</span>
            </div>
            <div className="h-3 w-full rounded bg-gray-100">
              <div
                className="h-3 rounded"
                style={{
                  width: bar.seconds != null ? `${(bar.seconds / maxSeconds) * 100}%` : "0%",
                  backgroundColor: bar.color,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 border-t border-gray-100 pt-4">
        {!haveBoth && (
          <p className="text-xs text-gray-400">
            Runtime for both runs is required to compare -- run unlearning, evaluation, and the
            retraining baseline for this experiment.
          </p>
        )}
        {haveBoth && unlearning_faster && (
          <p className="text-sm">
            <span className="font-semibold text-emerald-700">
              Time saved: {(time_saved_fraction * 100).toFixed(0)}%
            </span>
            <span className="ml-2 text-xs text-gray-500">
              ({speedup_factor.toFixed(1)}× faster than retraining from scratch)
            </span>
          </p>
        )}
        {haveBoth && !unlearning_faster && (
          <p className="text-sm font-semibold text-rose-700">
            Unlearning was not faster than retraining for this run (
            {Math.abs(time_saved_fraction * 100).toFixed(0)}% slower).
          </p>
        )}
      </div>
    </div>
  );
}
