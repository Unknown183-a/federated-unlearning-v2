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

const NAV = [
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

export default function App() {
  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      <nav className="w-64 flex-shrink-0 border-r border-gray-200 bg-white">
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900">Federated Unlearning</h1>
        </div>
        <ul className="px-3 py-4 space-y-1">
          {NAV.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-5xl">
          <Routes>
            {NAV.map((item) => (
              <Route key={item.path} path={item.path} element={item.element} />
            ))}
          </Routes>
        </div>
      </main>
    </div>
  );
}
