import { Routes, Route, NavLink } from "react-router-dom";
import Overview from "./pages/Overview.jsx";
import ExperimentSetup from "./pages/ExperimentSetup.jsx";
import DataDistribution from "./pages/DataDistribution.jsx";
import FederatedLearning from "./pages/FederatedLearning.jsx";
import ClientSelection from "./pages/ClientSelection.jsx";
import Unlearning from "./pages/Unlearning.jsx";
import Evaluation from "./pages/Evaluation.jsx";
import RetrainingComparison from "./pages/RetrainingComparison.jsx";
import ExperimentHistory from "./pages/ExperimentHistory.jsx";
import PipelineMiniMap from "./components/PipelineMiniMap.jsx";
import { useExperimentConfig } from "./state/ExperimentContext.jsx";

const ROUTES = [
  { path: "/", label: "Overview", element: <Overview /> },
  { path: "/setup", label: "Experiment Setup", element: <ExperimentSetup /> },
  { path: "/distribution", label: "Data Distribution", element: <DataDistribution /> },
  { path: "/training", label: "Federated Learning", element: <FederatedLearning /> },
  { path: "/client-selection", label: "Client Selection", element: <ClientSelection /> },
  { path: "/unlearning", label: "Unlearning", element: <Unlearning /> },
  { path: "/evaluation", label: "Evaluation", element: <Evaluation /> },
  { path: "/comparison", label: "Retraining Comparison", element: <RetrainingComparison /> },
  { path: "/history", label: "Experiment History", element: <ExperimentHistory /> },
];

// Grouped nav sections (Dashboard Spec Ch.33's sidebar wireframe:
// Experiment / Unlearning / Evaluation), each item carrying an
// optional `done` check against ExperimentContext's central `stages`
// -- the same single source of truth PipelineMiniMap reads, so the
// sidebar and the mini-map can never disagree about what's finished.
// This *is* "the persistent navigation stepper reflecting the 9-page
// order" (Phase 13): grouped, in spec order, with per-page progress.
function navSections(stages, config) {
  return [
    {
      heading: "Experiment",
      items: [
        { path: "/", label: "Overview" },
        { path: "/setup", label: "Setup" },
        { path: "/distribution", label: "Data Distribution", done: stages.partitioned },
        { path: "/training", label: "Federated Learning", done: stages.trained },
      ],
    },
    {
      heading: "Unlearning",
      items: [
        {
          path: "/client-selection",
          label: "Client Selection",
          done: config.target_client_id !== null && config.target_client_id !== undefined,
        },
        { path: "/unlearning", label: "Unlearning Process", done: stages.unlearned },
      ],
    },
    {
      heading: "Evaluation",
      items: [
        { path: "/evaluation", label: "Results", done: stages.evaluated },
        { path: "/comparison", label: "Retraining Comparison", done: stages.compared },
        { path: "/history", label: "Experiment History" },
      ],
    },
  ];
}

export default function App() {
  const { config, stages } = useExperimentConfig();
  const sections = navSections(stages, config);

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 text-gray-900">
      <PipelineMiniMap config={config} stages={stages} />
      <div className="flex flex-1">
        <nav aria-label="Experiment pages" className="w-64 flex-shrink-0 border-r border-gray-200 bg-white">
          <div className="border-b border-gray-200 px-6 py-5">
            <h1 className="text-lg font-semibold text-gray-900">Federated Unlearning Lab</h1>
          </div>
          {sections.map((section) => (
            <div key={section.heading} className="px-3 py-4">
              <h2 className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                {section.heading}
              </h2>
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      end={item.path === "/"}
                      className={({ isActive }) =>
                        `flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                          isActive
                            ? "bg-indigo-50 text-indigo-700"
                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                        }`
                      }
                    >
                      <span>{item.label}</span>
                      {item.done && (
                        <span aria-label="Complete" className="text-xs font-semibold text-emerald-600">
                          ✓
                        </span>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        <main className="flex-1 overflow-y-auto px-8 py-8">
          <div className="mx-auto max-w-5xl">
            <Routes>
              {ROUTES.map((item) => (
                <Route key={item.path} path={item.path} element={item.element} />
              ))}
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
}
