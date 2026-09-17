// Unlearning status timeline (Dashboard Spec Ch.14). `stageStatus` maps
// each stage key to "done" | "running" | "waiting" so the caller drives
// this purely off real backend/animation state -- no stage is ever
// marked done or running except because the data says so.
const STAGES = [
  { key: "model_loaded", label: "Model Loaded" },
  { key: "target_client", label: "Target Client" },
  { key: "gradient_ascent", label: "Gradient Ascent" },
  { key: "knowledge_distillation", label: "Knowledge Distill." },
  { key: "final_results", label: "Final Results" },
];

const ICON = {
  done: "✓",
  running: "●",
  waiting: "○",
};

const COLOR = {
  done: "border-green-300 bg-green-50 text-green-700",
  running: "border-indigo-400 bg-indigo-50 text-indigo-700 animate-pulse",
  waiting: "border-gray-200 bg-gray-50 text-gray-400",
};

export default function UnlearningStepper({ stageStatus }) {
  return (
    <section aria-labelledby="unlearning-stepper-heading" className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 id="unlearning-stepper-heading" className="text-base font-semibold text-gray-900">
        Unlearning Pipeline
      </h2>
      <ol className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-0">
        {STAGES.map((stage, i) => {
          const state = stageStatus[stage.key] || "waiting";
          return (
            <li key={stage.key} className="flex items-center sm:flex-1">
              <div
                className={`flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors ${COLOR[state]}`}
              >
                <span aria-hidden="true">{ICON[state]}</span>
                {stage.label}
              </div>
              {i < STAGES.length - 1 && (
                <span className="mx-2 hidden text-gray-300 sm:inline" aria-hidden="true">
                  ──▶
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
