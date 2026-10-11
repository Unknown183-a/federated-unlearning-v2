import { useCallback, useEffect, useState } from "react";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";
import { apiFetch } from "../lib/api.js";
import ErrorPanel from "../components/ErrorPanel.jsx";
import ProvenanceBadge from "../components/ProvenanceBadge.jsx";

// Phase 16 -- Model Updates.
//
// After unlearning, devices that already installed the old model still hold
// a copy that contains the forgotten client's influence. This page publishes
// the unlearned model as a new version and applies one of two policies:
//
//   Auto update      online devices switch immediately; offline ones switch
//                    when they reconnect; the old version is revoked at once.
//   Request + force  devices are asked and may accept until a deadline; any
//                    device that has not updated by then is updated
//                    automatically and the old version is revoked.
//
// The devices here are SIMULATED (there is no real app installed anywhere),
// so the page is labelled Illustrative. The rules themselves are real and
// live in core/distribution/.

const STATUS = {
  current: { label: "Up to date", className: "bg-emerald-100 text-emerald-800" },
  update_requested: { label: "Update requested", className: "bg-amber-100 text-amber-800" },
  blocked: { label: "Old model revoked", className: "bg-rose-100 text-rose-800" },
};

const EVENT_LABELS = {
  release_published: "Release",
  devices_added: "Devices",
  update_requested: "Request",
  auto_updated: "Auto update",
  user_accepted: "Accepted",
  forced_update: "Forced update",
  device_online: "Online",
  device_offline: "Offline",
  clock_advanced: "Clock",
};

function fmt(iso) {
  return iso ? new Date(iso).toLocaleString() : "—";
}

function Card({ title, children, aside }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
        {aside}
      </div>
      {children}
    </div>
  );
}

const btn =
  "rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50";
const btnPrimary =
  "rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50";

export default function ModelUpdates() {
  const { config } = useExperimentConfig();
  const experimentId = config.experiment_id;

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("request");
  const [graceHours, setGraceHours] = useState("48");
  const [note, setNote] = useState("");
  const [deviceCount, setDeviceCount] = useState("8");

  const base = `/api/releases/${encodeURIComponent(experimentId)}`;

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await apiFetch(base));
    } catch (err) {
      setData(null);
      setError(err);
    }
  }, [base]);

  useEffect(() => {
    load();
  }, [load]);

  const act = useCallback(
    async (path, method = "POST", body) => {
      setBusy(true);
      setError(null);
      setMessage("");
      try {
        const next = await apiFetch(`${base}${path}`, {
          method,
          headers: { "Content-Type": "application/json" },
          body: body ? JSON.stringify(body) : undefined,
        });
        setData(next);
        const done = next.result?.checked_in;
        if (done?.length) {
          const changed = done.filter((x) => x.version_after !== x.version_before).length;
          setMessage(`${changed} device(s) changed version.`);
        }
      } catch (err) {
        setError(err);
      } finally {
        setBusy(false);
      }
    },
    [base]
  );

  const latest = data?.releases?.[data.releases.length - 1];
  const hasOriginal = (data?.releases?.length ?? 0) > 0;
  const hasDevices = (data?.devices?.length ?? 0) > 0;

  return (
    <section className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Model Updates</h1>
          <p className="mt-1 text-sm text-gray-500">
            Devices that installed the old model still hold a copy that remembers the forgotten client. Publish the
            unlearned model as a new version and choose how devices must switch to it.
          </p>
        </div>
        <ProvenanceBadge kind="illustrative" className="shrink-0" />
      </div>

      <p className="rounded-md bg-gray-50 px-4 py-3 text-xs text-gray-600">
        The devices below are simulated and the clock is simulated, so you can see a deadline pass in seconds. The
        update rules are real. A copy of the old model file that someone keeps on their own device cannot be deleted
        from here; the revoked version only stops being allowed by apps that follow the policy.
      </p>

      <ErrorPanel error={error} onRetry={load} />
      {message && <p className="text-sm font-medium text-indigo-700">{message}</p>}

      {!data && !error && <p className="text-sm text-gray-500">Loading…</p>}

      {data && (
        <>
          <Card title="1. Publish the unlearned model">
            {!hasOriginal ? (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  First release the original trained model (version 1). It is what your devices have installed now.
                </p>
                <button className={btnPrimary} disabled={busy} onClick={() => act("/original")}>
                  Release original model (v1)
                </button>
                {data.publish_blocker && !data.publish_blocker.startsWith("Release the original") && (
                  <p className="text-xs text-amber-700">{data.publish_blocker}</p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <fieldset className="space-y-2" disabled={busy}>
                  <legend className="sr-only">Update policy</legend>
                  <label className="flex cursor-pointer gap-3 rounded-md border border-gray-200 p-3 text-sm has-[:checked]:border-indigo-400 has-[:checked]:bg-indigo-50">
                    <input type="radio" name="mode" checked={mode === "auto"} onChange={() => setMode("auto")} />
                    <span>
                      <span className="font-medium text-gray-900">Auto update</span>
                      <span className="block text-gray-600">
                        Online devices switch immediately. Offline devices switch when they reconnect. The old version
                        is revoked right away.
                      </span>
                    </span>
                  </label>
                  <label className="flex cursor-pointer gap-3 rounded-md border border-gray-200 p-3 text-sm has-[:checked]:border-indigo-400 has-[:checked]:bg-indigo-50">
                    <input type="radio" name="mode" checked={mode === "request"} onChange={() => setMode("request")} />
                    <span className="flex-1">
                      <span className="font-medium text-gray-900">Request, then update automatically after a deadline</span>
                      <span className="block text-gray-600">
                        Devices are asked to update and can accept any time before the deadline. Whoever has not
                        updated by then is updated automatically, and the old version is revoked.
                      </span>
                      {mode === "request" && (
                        <span className="mt-2 flex items-center gap-2">
                          <span className="text-gray-700">Deadline after</span>
                          <input
                            type="number"
                            min="1"
                            value={graceHours}
                            onChange={(e) => setGraceHours(e.target.value)}
                            className="w-24 rounded-md border border-gray-300 px-2 py-1 text-sm"
                            aria-label="Hours until the deadline"
                          />
                          <span className="text-gray-700">hours</span>
                        </span>
                      )}
                    </span>
                  </label>
                </fieldset>
                <input
                  type="text"
                  value={note}
                  maxLength={200}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Optional note shown with the release"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
                <div className="flex items-center gap-3">
                  <button
                    className={btnPrimary}
                    disabled={busy || Boolean(data.publish_blocker)}
                    onClick={() =>
                      act("/publish", "POST", {
                        mode,
                        grace_hours: mode === "request" ? Number(graceHours) : undefined,
                        note,
                      })
                    }
                  >
                    Publish unlearned model
                  </button>
                  {data.publish_blocker && <span className="text-xs text-amber-700">{data.publish_blocker}</span>}
                </div>
              </div>
            )}
          </Card>

          <Card title="2. Releases">
            {data.releases.length === 0 ? (
              <p className="text-sm text-gray-500">Nothing released yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-600">
                    <tr>
                      <th className="px-3 py-2">Version</th>
                      <th className="px-3 py-2">Model</th>
                      <th className="px-3 py-2">Policy</th>
                      <th className="px-3 py-2">Deadline</th>
                      <th className="px-3 py-2">Old copies</th>
                      <th className="px-3 py-2">SHA-256</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.releases.map((release) => (
                      <tr key={release.version}>
                        <td className="px-3 py-2 font-semibold">v{release.version}</td>
                        <td className="px-3 py-2">
                          {release.label}
                          {release.note && <span className="block text-xs text-gray-500">{release.note}</span>}
                        </td>
                        <td className="px-3 py-2">
                          {release.policy ? (release.policy.mode === "auto" ? "Auto update" : "Request, then force") : "—"}
                        </td>
                        <td className="px-3 py-2">{fmt(release.deadline)}</td>
                        <td className="px-3 py-2">
                          {release.allowed ? (
                            <span className="text-emerald-700">Allowed</span>
                          ) : (
                            <span className="text-rose-700">Revoked</span>
                          )}
                        </td>
                        <td className="px-3 py-2 font-mono text-xs text-gray-500" title={release.sha256}>
                          {release.sha256.slice(0, 12)}…
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {hasOriginal && (
            <Card
              title="3. Simulated devices"
              aside={<span className="text-xs text-gray-500">Simulated time: {fmt(data.now)}</span>}
            >
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <input
                  type="number"
                  min="1"
                  value={deviceCount}
                  onChange={(e) => setDeviceCount(e.target.value)}
                  className="w-20 rounded-md border border-gray-300 px-2 py-1 text-xs"
                  aria-label="Number of devices to add"
                />
                <button className={btn} disabled={busy} onClick={() => act("/devices", "POST", { count: Number(deviceCount) })}>
                  Add devices
                </button>
                <span className="mx-1 h-5 w-px bg-gray-200" />
                {[1, 24, 72].map((hours) => (
                  <button key={hours} className={btn} disabled={busy || !hasDevices} onClick={() => act("/advance-clock", "POST", { hours })}>
                    +{hours === 24 ? "1 day" : hours === 72 ? "3 days" : "1 hour"}
                  </button>
                ))}
                <button className={btn} disabled={busy || !hasDevices} onClick={() => act("/check-in", "POST", {})}>
                  All online devices check in
                </button>
                <button
                  className={`${btn} ml-auto text-rose-700`}
                  disabled={busy}
                  onClick={() => window.confirm("Clear all releases and devices for this experiment?") && act("", "DELETE")}
                >
                  Reset
                </button>
              </div>

              {latest?.policy?.mode === "request" && data.hours_to_deadline !== null && (
                <p className="mb-3 text-sm text-gray-700">
                  {data.hours_to_deadline > 0
                    ? `Deadline for v${latest.version}: ${data.hours_to_deadline} hour(s) left.`
                    : `Deadline for v${latest.version} has passed: older versions are revoked.`}
                </p>
              )}

              {!hasDevices ? (
                <p className="text-sm text-gray-500">Add some devices to see how the policy treats them.</p>
              ) : (
                <>
                  <p className="mb-2 text-xs text-gray-500">
                    {data.counts.current} up to date · {data.counts.update_requested} asked · {data.counts.blocked} revoked ·{" "}
                    {data.counts.offline} offline
                  </p>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-600">
                        <tr>
                          <th className="px-3 py-2">Device</th>
                          <th className="px-3 py-2">Version</th>
                          <th className="px-3 py-2">Status</th>
                          <th className="px-3 py-2">Connection</th>
                          <th className="px-3 py-2">Last check-in</th>
                          <th className="px-3 py-2" />
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {data.devices.map((device) => {
                          const status = STATUS[device.status];
                          return (
                            <tr key={device.device_id}>
                              <td className="px-3 py-2 font-mono text-xs">{device.device_id}</td>
                              <td className="px-3 py-2">v{device.version}</td>
                              <td className="px-3 py-2">
                                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${status.className}`}>{status.label}</span>
                              </td>
                              <td className="px-3 py-2">
                                <button
                                  className={btn}
                                  disabled={busy}
                                  onClick={() => act("/online", "POST", { device_id: device.device_id, online: !device.online })}
                                >
                                  {device.online ? "Online · go offline" : "Offline · reconnect"}
                                </button>
                              </td>
                              <td className="px-3 py-2 text-xs text-gray-500">{fmt(device.last_check_in)}</td>
                              <td className="px-3 py-2 text-right">
                                {device.status === "update_requested" && device.online && (
                                  <button className={btn} disabled={busy} onClick={() => act("/accept", "POST", { device_id: device.device_id })}>
                                    Accept update
                                  </button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </Card>
          )}

          {data.events.length > 0 && (
            <Card title="4. What happened">
              <ul className="divide-y divide-gray-100 text-sm">
                {data.events.map((event, index) => (
                  <li key={`${event.at}-${index}`} className="flex gap-3 py-1.5">
                    <span className="w-36 shrink-0 text-xs text-gray-500">{fmt(event.at)}</span>
                    <span className="w-28 shrink-0 text-xs font-semibold text-gray-700">{EVENT_LABELS[event.event] || event.event}</span>
                    <span className="text-gray-700">
                      {event.device_id && <span className="mr-1 font-mono text-xs text-gray-500">{event.device_id}</span>}
                      {event.detail}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </section>
  );
}
