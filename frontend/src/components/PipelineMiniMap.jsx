import { Link, useLocation } from "react-router-dom";

// Persistent pipeline mini-map (Dashboard Spec Ch.41, Phase 13).
//
// "The main overview should contain a persistent pipeline... The
// current stage should be highlighted. Completed stages should show a
// checkmark. Running stage should show progress. Upcoming stages
// should be muted." -- shown in App.jsx above every page, not just
// Overview, so it's always visible regardless of which of the 9 pages
// someone is on.
//
// Completion comes from ExperimentContext's `stages` (Phase 13's
// single central source, read from the Phase 12 registry) plus
// `config.target_client_id` for the one stage that isn't a stored
// artifact. "Current" comes from the active route. Each chip is a
// real link, so this doubles as quick navigation, not just a status
// display.

const STAGES = [
  { key: "dataset", label: "Dataset", path: "/setup", isComplete: (config, stages) => Boolean(config.dataset) },
  { key: "partition", label: "Partition", path: "/distribution", isComplete: (config, stages) => stages.partitioned },
  { key: "clients", label: "Clients", path: "/distribution", isComplete: (config, stages) => stages.partitioned },
  { key: "fl", label: "Federated Learning", path: "/training", isComplete: (config, stages) => stages.trained },
  { key: "global_model", label: "Global Model", path: "/training", isComplete: (config, stages) => stages.trained },
  {
    key: "select_client",
    label: "Select Client",
    path: "/client-selection",
    isComplete: (config) => config.target_client_id !== null && config.target_client_id !== undefined,
  },
  { key: "gradient_ascent", label: "Gradient Ascent", path: "/unlearning", isComplete: (config, stages) => stages.unlearned },
  {
    key: "knowledge_distillation",
    label: "Knowledge Distillation",
    path: "/unlearning",
    isComplete: (config, stages) => stages.unlearned,
  },
  { key: "unlearned_model", label: "Unlearned Model", path: "/unlearning", isComplete: (config, stages) => stages.unlearned },
  { key: "evaluation", label: "Evaluation", path: "/evaluation", isComplete: (config, stages) => stages.evaluated },
  {
    key: "retraining_comparison",
    label: "Retraining Comparison",
    path: "/comparison",
    isComplete: (config, stages) => stages.compared,
  },
];

function chipStatus(stage, config, stages, currentPath) {
  if (stage.isComplete(config, stages)) return "complete";
  if (stage.path === currentPath) return "current";
  return "upcoming";
}

const STATUS_STYLES = {
  complete: "border-emerald-500 bg-emerald-50 text-emerald-800",
  current: "border-indigo-600 bg-indigo-50 text-indigo-800 ring-2 ring-indigo-200",
  upcoming: "border-gray-200 bg-gray-50 text-gray-500",
};

const STATUS_ICON = { complete: "✓", current: "●", upcoming: "○" };
const STATUS_WORD = { complete: "done", current: "current stage", upcoming: "upcoming" };

export default function PipelineMiniMap({ config, stages }) {
  const location = useLocation();

  const summary = STAGES.map((stage) => {
    const status = chipStatus(stage, config, stages, location.pathname);
    return `${stage.label}: ${STATUS_WORD[status]}`;
  }).join(". ");

  return (
    <nav aria-label="Pipeline progress" className="border-b border-gray-200 bg-white px-6 py-2">
      <p className="sr-only">Pipeline progress. {summary}.</p>
      <ol
        aria-hidden="true"
        className="flex items-center gap-1 overflow-x-auto text-xs"
      >
        {STAGES.map((stage, i) => {
          const status = chipStatus(stage, config, stages, location.pathname);
          return (
            <li key={stage.key} className="flex shrink-0 items-center gap-1">
              <Link
                to={stage.path}
                className={`flex items-center gap-1 rounded-full border px-2.5 py-1 font-medium whitespace-nowrap transition-colors ${STATUS_STYLES[status]}`}
              >
                <span aria-hidden="true">{STATUS_ICON[status]}</span>
                {stage.label}
              </Link>
              {i < STAGES.length - 1 && <span className="text-gray-300">→</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
