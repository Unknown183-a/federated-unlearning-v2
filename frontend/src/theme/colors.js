// Shared semantic color code (Dashboard Spec Ch.40, Phase 13 task
// "Apply a consistent color code for dataset/client/server/model
// across all pages").
//
// Before this phase, each component picked its own color per concept
// with no shared reference -- most consistently landed on indigo for
// "server / global model" and rose for "target client" already (see
// GradientAscentPanel.jsx, ClientInfluenceBars.jsx), but a few spots
// drifted (ClientCard.jsx's "Target" badge was indigo, the same color
// used for the server/model and for generic UI selection -- not
// visually distinct from either). This module is the single place
// that documents the intended mapping; components reference ROLE
// below instead of picking a color inline, and the one real
// inconsistency it fixes is ClientCard.jsx.
//
// This isn't a full re-skin of every existing chart (components that
// already use indigo/emerald/rose consistently for the right concept
// are left alone to avoid unrelated churn) -- it's the shared
// reference going forward, applied everywhere the client/server/
// target distinction is the point: ClientCard's target badge, and the
// new PipelineMiniMap / navigation stepper.

export const ROLE = {
  // The dataset itself, and the data-partitioning stage.
  dataset: {
    text: "text-slate-700",
    bg: "bg-slate-100",
    border: "border-slate-300",
    ring: "ring-slate-400",
    hex: "#475569",
  },
  // An individual federated client, in its ordinary (non-target) state.
  client: {
    text: "text-gray-700",
    bg: "bg-gray-100",
    border: "border-gray-300",
    ring: "ring-gray-400",
    hex: "#6b7280",
  },
  // The server / global model / FedAvg aggregation -- anything that
  // represents the shared, centrally-trained model rather than one
  // client's local data.
  server: {
    text: "text-indigo-700",
    bg: "bg-indigo-100",
    border: "border-indigo-600",
    ring: "ring-indigo-400",
    hex: "#4f46e5",
  },
  // The client selected for unlearning -- must be visually distinct
  // from both "server" and an ordinary client everywhere it appears
  // (Client Selection, Gradient Ascent, Client Influence bars,
  // Evaluation's forget-client metric, the Retraining Comparison
  // chart). Rose was already the de-facto choice in most of those
  // places; this makes it the documented, enforced one.
  target: {
    text: "text-rose-800",
    bg: "bg-rose-100",
    border: "border-rose-500",
    ring: "ring-rose-300",
    hex: "#e11d48",
  },
  // A result that is working as intended (retained-client accuracy
  // holding up, MIA back near chance, a stage completed successfully).
  success: {
    text: "text-emerald-700",
    bg: "bg-emerald-100",
    border: "border-emerald-500",
    hex: "#059669",
  },
  // A result moving the wrong way, or an error state.
  warning: {
    text: "text-rose-700",
    bg: "bg-rose-50",
    border: "border-rose-400",
    hex: "#e11d48",
  },
  // Not yet reached / not applicable.
  muted: {
    text: "text-gray-500",
    bg: "bg-gray-50",
    border: "border-gray-200",
    hex: "#9ca3af",
  },
};
