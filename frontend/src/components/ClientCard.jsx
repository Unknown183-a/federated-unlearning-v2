const STRATEGY_LABEL = {
  iid: "IID",
  non_iid: "Non-IID",
};

// Top classes by sample count for this client (Dashboard Spec Ch.7.1
// "Dominant Classes"). class_counts is keyed by class id -> sample count.
function dominantClasses(classCounts, limit = 3) {
  return Object.entries(classCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([classId]) => Number(classId));
}

export default function ClientCard({ client, strategy, selectable, selected, onSelect }) {
  const dominant = dominantClasses(client.class_counts);

  // "selectable" is only ever true on Client Selection -- "selected"
  // there always means "the current unlearning target", so this uses
  // the shared target color (rose), not a generic selection color, to
  // stay consistent with how the target client is highlighted
  // everywhere else (ClientInfluenceBars, GradientAscentPanel) --
  // Phase 13's "target-client highlighting" task.
  const interactionProps = selectable
    ? {
        role: "button",
        tabIndex: 0,
        onClick: () => onSelect(client.client_id),
        onKeyDown: (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect(client.client_id);
          }
        },
      }
    : {};

  return (
    <article
      aria-label={`Client ${client.client_id}${selectable ? (selected ? ", selected as unlearning target" : ", select as unlearning target") : ""}`}
      aria-pressed={selectable ? selected : undefined}
      {...interactionProps}
      className={`rounded-lg border bg-white p-4 shadow-sm ${
        selectable ? "cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-2" : ""
      } ${
        selected
          ? "border-rose-500 ring-2 ring-rose-200"
          : "border-gray-200"
      } ${selectable && !selected ? "hover:border-rose-300" : ""}`}
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-900">Client {client.client_id}</h3>
        {selectable && selected && (
          <span className="shrink-0 rounded-full bg-rose-600 px-2 py-0.5 text-xs font-semibold text-white">
            Target
          </span>
        )}
      </div>
      <dl className="mt-2 space-y-2 text-sm">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Samples</dt>
          <dd className="text-gray-900">{client.num_samples.toLocaleString()}</dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Classes</dt>
          <dd className="text-gray-900">{client.num_classes_present}</dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Dominant Classes</dt>
          <dd>
            {dominant.length ? (
              <ul className="mt-0.5 list-inside list-disc text-gray-700">
                {dominant.map((c) => (
                  <li key={c}>Class {c}</li>
                ))}
              </ul>
            ) : (
              <span className="text-gray-500">None</span>
            )}
          </dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Distribution</dt>
          <dd>
            <span className="inline-block rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
              {STRATEGY_LABEL[strategy] || strategy}
            </span>
          </dd>
        </div>
      </dl>
    </article>
  );
}
