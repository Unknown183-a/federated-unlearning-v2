import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api.js";

// Phase 15 -- the collapsible "Experiment Configuration" panel that
// every result screen carries (Dashboard Spec Ch.44 / Ch.45), so any
// number on screen can be traced back to the exact dataset, partition,
// seed, model and unlearning settings that produced it.
//
// It reads GET /api/experiments/:id/reproducibility, which only reports
// what the stored artifacts actually contain. A missing value is shown
// as "not recorded" -- never as a guessed default.

function Row({ label, value }) {
  const recorded = value !== null && value !== undefined && value !== "";
  return (
    <div className="flex justify-between gap-4 py-1 text-sm">
      <dt className="text-gray-500">{label}</dt>
      <dd className={recorded ? "font-medium text-gray-900" : "italic text-gray-400"}>
        {recorded ? String(value) : "not recorded"}
      </dd>
    </div>
  );
}

const STRATEGY_LABELS = { iid: "IID", non_iid: "Non-IID" };

export default function ExperimentConfigPanel({ experimentId }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState(null);
  const [problem, setProblem] = useState(null);

  useEffect(() => {
    if (!open || !experimentId) return undefined;
    let cancelled = false;
    setProblem(null);
    apiFetch(`/api/experiments/${encodeURIComponent(experimentId)}/reproducibility`)
      .then((body) => !cancelled && setData(body.reproducibility))
      .catch((err) => !cancelled && setProblem(err.message));
    return () => {
      cancelled = true;
    };
  }, [open, experimentId]);

  const ga = data?.unlearning?.hyperparameters?.gradient_ascent;
  const kd = data?.unlearning?.hyperparameters?.knowledge_distillation;

  return (
    <section className="rounded-lg border border-gray-200 bg-white" aria-label="Experiment configuration">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
      >
        <span>Experiment Configuration &amp; Seed</span>
        <span aria-hidden="true" className="text-gray-400">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="border-t border-gray-100 px-4 py-3">
          {problem && <p className="text-sm text-red-700">Could not load the configuration: {problem}</p>}
          {!problem && !data && <p className="text-sm text-gray-500">Loading…</p>}
          {data && (
            <dl className="divide-y divide-gray-100">
              <Row label="Experiment ID" value={data.experiment_id} />
              <Row label="Dataset" value={data.dataset_config?.name || data.dataset} />
              <Row label="Clients" value={data.num_clients} />
              <Row label="Partition" value={STRATEGY_LABELS[data.partition_strategy] || data.partition_strategy} />
              {data.partition_strategy === "non_iid" && <Row label="Dirichlet alpha" value={data.partition_alpha} />}
              <Row label="Random seed" value={data.seed} />
              <Row label="Model" value={data.model} />
              <Row label="Federated rounds" value={data.federated_rounds} />
              <Row label="Local epochs" value={data.local_epochs} />
              <Row label="Learning rate" value={data.learning_rate} />
              <Row label="Batch size" value={data.batch_size} />
              <Row label="Unlearning method" value={data.unlearning?.method_label} />
              <Row label="Target client" value={data.unlearning?.target_client_id} />
              <Row label="Gradient Ascent" value={ga && `${ga.steps} steps · lr ${ga.lr} · batch ${ga.batch_size}`} />
              <Row
                label="Knowledge Distillation"
                value={kd && `${kd.epochs} epochs · lr ${kd.lr} · T ${kd.temperature} · α ${kd.alpha} · batch ${kd.batch_size}`}
              />
              <Row
                label="Software"
                value={data.software && `v${data.software.project_version} · commit ${data.software.git_commit || "unknown"}`}
              />
            </dl>
          )}
          {data && data.unlearning && !data.unlearning.hyperparameters && (
            <p className="mt-2 text-xs text-gray-500">
              Unlearning settings were not recorded for this run (it was made before they were saved). Re-run unlearning to record them.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
