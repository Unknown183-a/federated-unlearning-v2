import { Link, useLocation } from "react-router-dom";
import { useExperimentConfig } from "../state/ExperimentContext.jsx";

// Phase 15 -- the Professor Demo walkthrough strip (Dashboard Spec
// Ch.37). Shows where you are in the 6-step research story with a
// suggested time for each, plus Previous / Next. The times add up to
// the spec's ~10 minute demo; they are a speaking guide, not timers.
export const DEMO_STEPS = [
  { path: "/distribution", label: "Data Distribution", minutes: 1, say: "How the data is split across clients." },
  { path: "/training", label: "Federated Learning", minutes: 2, say: "The stored training run, round by round." },
  { path: "/client-selection", label: "Client Selection", minutes: 1, say: "The client whose data will be forgotten." },
  { path: "/unlearning", label: "Unlearning", minutes: 2, say: "Gradient Ascent, then Knowledge Distillation." },
  { path: "/evaluation", label: "Results", minutes: 2, say: "Before vs after: accuracy, forgetting, MIA." },
  { path: "/comparison", label: "Retraining Comparison", minutes: 2, say: "Unlearning vs full retraining, with measured runtimes." },
];

export default function DemoGuideBar() {
  const { appMode, setAppMode } = useExperimentConfig();
  const { pathname } = useLocation();
  if (appMode !== "demo") return null;

  const index = DEMO_STEPS.findIndex((s) => s.path === pathname);
  const step = index >= 0 ? DEMO_STEPS[index] : null;
  const prev = index > 0 ? DEMO_STEPS[index - 1] : null;
  const next = index >= 0 && index < DEMO_STEPS.length - 1 ? DEMO_STEPS[index + 1] : null;

  return (
    <div className="mb-6 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3" role="region" aria-label="Professor demo guide">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
            Professor Demo Mode · stored experiment · no training will run
          </p>
          {step ? (
            <p className="mt-0.5 text-sm text-indigo-900">
              <span className="font-semibold">
                Step {index + 1} of {DEMO_STEPS.length}: {step.label}
              </span>{" "}
              (~{step.minutes} min) — {step.say}
            </p>
          ) : (
            <p className="mt-0.5 text-sm text-indigo-900">Use the demo page to start the guided walkthrough.</p>
          )}
        </div>
        <div className="flex gap-2">
          {prev && (
            <Link to={prev.path} className="rounded-md border border-indigo-300 bg-white px-3 py-1.5 text-sm font-medium text-indigo-800 hover:bg-indigo-100">
              ← {prev.label}
            </Link>
          )}
          {next && (
            <Link to={next.path} className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700">
              {next.label} →
            </Link>
          )}
          <button
            type="button"
            onClick={() => setAppMode("research")}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Exit demo
          </button>
        </div>
      </div>
    </div>
  );
}
