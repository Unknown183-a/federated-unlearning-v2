// Shown after a measured run: which compute backend actually ran it,
// and -- crucially -- whether Auto mode had to fall back to get there.
// Phase 14: "failure detection + fallback messaging (never silent)".
// `trace` is the backend_trace the Python CLI returns: every backend
// Auto tried, in order, up to and including the one that served the run.

export default function BackendTraceNote({ trace }) {
  if (!trace || trace.length === 0) return null;
  const used = trace[trace.length - 1];
  const skipped = trace.slice(0, -1);

  return (
    <div
      role="status"
      className={`rounded-md px-3 py-2 text-xs ${
        skipped.length > 0 ? "bg-amber-50 text-amber-900" : "bg-gray-50 text-gray-600"
      }`}
    >
      <p className="font-semibold">
        Ran on: {used.name}
        {used.device ? ` (${used.device})` : ""}
      </p>
      {skipped.length > 0 && (
        <ul className="mt-1 list-inside list-disc">
          {skipped.map((s) => (
            <li key={s.backend}>
              Fell back past {s.name}: {s.detail}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
