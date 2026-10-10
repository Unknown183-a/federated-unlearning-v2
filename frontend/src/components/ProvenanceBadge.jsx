// Phase 15 -- the single "where did this number come from?" label
// (Dashboard Spec Ch.46 / Ch.71.13). Before this phase four pages each
// carried their own copy of a Measured / Stored chip and other screens
// had none. Every result screen now uses this one component, so the
// four kinds mean the same thing everywhere.
//
//   measured     computed live in this session by a real run
//   precomputed  read back from a stored experiment (a replay)
//   live         a run that is happening right now
//   illustrative a conceptual drawing -- NEVER a real result
export const PROVENANCE = {
  measured: {
    label: "Measured",
    help: "Computed by a real run in this session.",
    className: "bg-indigo-100 text-indigo-800",
  },
  precomputed: {
    label: "Precomputed · Stored Experiment",
    help: "Read from a stored experiment. This is a replay of a real earlier run, not a new computation.",
    className: "bg-amber-100 text-amber-800",
  },
  live: {
    label: "Live",
    help: "A run that is in progress right now.",
    className: "bg-rose-100 text-rose-800",
  },
  illustrative: {
    label: "Illustrative",
    help: "A conceptual diagram. It does not show results from any experiment.",
    className: "border border-dashed border-gray-400 bg-white text-gray-600",
  },
};

// The pages historically used "stored" for precomputed results.
const ALIASES = { stored: "precomputed" };

export default function ProvenanceBadge({ kind, className = "" }) {
  const key = ALIASES[kind] || kind;
  const spec = PROVENANCE[key];
  if (!spec) return null;
  return (
    <span
      title={spec.help}
      data-provenance={key}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${spec.className} ${className}`}
    >
      {key === "live" && <span className="mr-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-rose-600" aria-hidden="true" />}
      {spec.label}
    </span>
  );
}

/** A one-glance legend of all four kinds, for the Overview page. */
export function ProvenanceLegend() {
  return (
    <ul className="grid gap-3 sm:grid-cols-2" aria-label="Result labels">
      {Object.keys(PROVENANCE).map((key) => (
        <li key={key} className="flex items-start gap-3">
          <ProvenanceBadge kind={key} className="flex-shrink-0" />
          <span className="text-sm text-gray-600">{PROVENANCE[key].help}</span>
        </li>
      ))}
    </ul>
  );
}
