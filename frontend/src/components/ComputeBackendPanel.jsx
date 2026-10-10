import { useCallback, useEffect, useState } from "react";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";

// Compute Backend selector + status panel (Phase 14, Dashboard Spec
// Ch.71 / Ch.72). Shows every backend's live status, lets the user
// pick Auto or pin one, and -- in Auto mode -- shows exactly which
// backend it would pick right now and why the ones above it were
// skipped, so a fallback is visible before a run, not only after.
//
// Only credential-free status JSON from GET /api/compute/status ever
// reaches this component: base URLs and API keys live in server-side
// environment variables read by core/compute/ and never serialized.

const OPTIONS = [
  { value: "auto", label: "Auto" },
  { value: "college_gpu", label: "College GPU" },
  { value: "colab", label: "Google Colab" },
  { value: "local", label: "Local" },
  { value: "demo", label: "Demo (Precomputed)" },
];

function StatusDot({ available }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-2.5 w-2.5 rounded-full ${available ? "bg-emerald-500" : "bg-gray-300"}`}
    />
  );
}

export default function ComputeBackendPanel() {
  const { config, updateConfig } = useExperimentConfig();
  const [status, setStatus] = useState(null);
  const [loadState, setLoadState] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  const refresh = useCallback(() => {
    setLoadState("loading");
    setError(null);
    fetch("/api/compute/status")
      .then((res) => {
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setStatus(data);
        setLoadState("ready");
      })
      .catch((err) => {
        setError(err.message);
        setLoadState("error");
      });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const byKind = status ? Object.fromEntries(status.backends.map((b) => [b.backend, b])) : {};
  const selected = config.compute_backend;
  const pinned = selected !== "auto" ? byKind[selected] : null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Compute Backend</h3>
          <p className="mt-1 text-sm text-gray-500">
            Where training, unlearning, and evaluation run. Results look identical either way.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="rounded-md border border-gray-200 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50"
        >
          Refresh
        </button>
      </div>

      <fieldset className="mt-4">
        <legend className="sr-only">Compute backend</legend>
        <div className="flex flex-wrap gap-2">
          {OPTIONS.map((option) => {
            const info = byKind[option.value];
            const isSelected = selected === option.value;
            return (
              <label
                key={option.value}
                className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium focus-within:ring-2 focus-within:ring-indigo-400 ${
                  isSelected
                    ? "border-indigo-600 bg-indigo-50 text-indigo-800"
                    : "border-gray-200 text-gray-700 hover:bg-gray-50"
                }`}
              >
                <input
                  type="radio"
                  name="compute-backend"
                  value={option.value}
                  checked={isSelected}
                  onChange={() => updateConfig({ compute_backend: option.value })}
                  className="sr-only"
                />
                {info && <StatusDot available={info.available} />}
                {option.label}
                {info && (
                  <span className="text-xs font-normal text-gray-500">
                    {info.available ? "available" : "unavailable"}
                  </span>
                )}
              </label>
            );
          })}
        </div>
      </fieldset>

      {loadState === "loading" && <p className="mt-4 text-sm text-gray-500">Checking backends…</p>}
      {loadState === "error" && (
        <p role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          Could not check compute backends: {error}
        </p>
      )}

      {loadState === "ready" && selected === "auto" && (
        <div className="mt-4 rounded-md bg-gray-50 px-3 py-3 text-sm text-gray-700">
          <p>
            Auto will use{" "}
            <strong className="font-semibold">{byKind[status.auto_selected]?.name}</strong> right now.
          </p>
          {status.auto_trace.length > 1 && (
            <ul className="mt-2 list-inside list-disc text-xs text-gray-600">
              {status.auto_trace.slice(0, -1).map((t) => (
                <li key={t.backend}>
                  Skipping {t.name}: {t.detail}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {loadState === "ready" && pinned && (
        <div
          className={`mt-4 rounded-md px-3 py-3 text-sm ${
            pinned.available ? "bg-gray-50 text-gray-700" : "bg-red-50 text-red-800"
          }`}
        >
          <p>
            <strong className="font-semibold">{pinned.name}</strong>: {pinned.detail}
          </p>
          {!pinned.available && (
            <p className="mt-1 text-xs">
              This backend is pinned, so runs will fail rather than silently use a different one. Switch
              to Auto to fall back automatically.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
