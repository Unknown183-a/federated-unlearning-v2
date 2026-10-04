# Phase 13 — Dashboard UX — Navigation, State & Visual Design System

> Status: **Complete**
> Implementation: the grouped navigation stepper, central stage store, persistent pipeline mini-map, shared color code, and the accessibility pass are live on main.

## Goal

Tie all 9 pages together into one coherent app with a persistent stepper, shared state, and the full visual design system.

## In Scope

- Global navigation stepper across all 9 pages
- Central experiment state management
- Visual design system: pipeline mini-map, consistent color code, target-client highlighting
- Accessibility pass (text-equivalents for charts, keyboard navigation, color contrast)

## Out of Scope

- Backend/compute architecture (Phase 14)

## Tasks

- [x] Build the persistent navigation stepper reflecting the 9-page order
- [x] Consolidate all page state into one central store
- [x] Build the persistent pipeline mini-map component
- [x] Apply a consistent color code for dataset/client/server/model across all pages
- [x] Accessibility pass: alt text/summaries for every chart, keyboard nav, contrast check

## Deliverables

- Fully navigable 9-page app with one shared state model

## Depends On

Phase 12 (quick demo + model library)

## Acceptance Criteria

- Navigating back and forth between pages never loses or recomputes state
- Every chart has a text-equivalent summary

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | `ExperimentContext.jsx` gained the central piece this phase needed: `stages` (the five `partitioned/trained/unlearned/evaluated/compared` flags from the Phase 12 registry) plus `refreshStages()`, read by both the sidebar and the new mini-map so they can never disagree about progress. All five pages that run an expensive stage (`DataDistribution`, `FederatedLearning`, `Unlearning`, `Evaluation`, `RetrainingComparison`) now call `refreshStages()` right after their own POST succeeds, so the stepper/mini-map update immediately rather than waiting for a route change. Caught and fixed a stale-closure bug in the first draft of the guard that discards out-of-order responses: comparing against `config.experiment_id` captured inside the same `useCallback` the comparison lives in is always trivially true (it can never detect that the experiment changed since the call was made) -- replaced with a ref that always holds the latest experiment_id, independent of which render's closure is running. `App.jsx`: the flat 9-link sidebar became three headed sections matching Ch.33's wireframe (Experiment / Unlearning / Evaluation), each item showing a ✓ once its stage is done -- this *is* the "persistent navigation stepper," reusing the same `stages` rather than a separate progress calculation. `PipelineMiniMap.jsx` (new, Ch.41): an 11-chip horizontal strip -- Dataset → Partition → Clients → Federated Learning → Global Model → Select Client → Gradient Ascent → Knowledge Distillation → Unlearned Model → Evaluation → Retraining Comparison -- rendered above every page in `App.jsx`, not just Overview, with complete/current/upcoming derived the same way the sidebar is, each chip a real link, and a `sr-only` sentence-per-chip summary so the same progress is available as text, not just icon+color. `theme/colors.js` (new): documents the color code this project had mostly already converged on by accident (indigo = server/global model, rose = target client, emerald = success) and fixes the one real inconsistency -- `ClientCard.jsx`'s "Target" badge and selection ring were indigo, the same color already used for the server/model and for nothing-in-particular UI selection, so a selected (target) client card looked like neither a clear match nor a clear mismatch next to the rest of the app; it's rose now, matching `ClientInfluenceBars.jsx` and `GradientAscentPanel.jsx`, so the target client reads the same way on Client Selection, Unlearning, and everywhere else it's called out. `ClientCard.jsx` also picked up real keyboard support in selectable mode (`role="button"`, `tabIndex`, Enter/Space via `onKeyDown`) -- it was previously only `onClick` on an `<article>`, unreachable by keyboard despite already carrying `aria-pressed`. Accessibility pass: every chart that previously had only a generic or title-only `aria-label` now carries a real, data-derived `sr-only` text-equivalent referenced via `aria-labelledby`/`aria-describedby` -- `MetricLineChart` (trend direction, start/end/min/max with their rounds), `DistributionHeatmap` (per-cell sample count as hidden text inside each `<td>`, since the heatmap previously encoded count as color alone, plus a one-line most-imbalanced-client summary), and `RetrainingComparisonChart` (per-metric original/unlearned/retrained values, replacing a static "Comparison chart" label). Three more spots relied on color alone to carry meaning with no textual fallback -- `ClientInfluenceBars` now appends "(target)" in text next to the highlighted row, `EvaluationMetrics` now appends "(improved)"/"(regressed)" next to each colored delta, and `FedAvgDiagram`'s per-client chips now carry a hidden "finished local training / training locally / waiting" status word alongside their color. Contrast: sampled every `text-gray-400` (`#9ca3af` on white is roughly 2.8:1, below WCAG AA's 4.5:1 for normal text) used for actual content rather than a purely decorative glyph and bumped it to `text-gray-500` (`#6b7280`, roughly 4.6:1) across 13 files. Verified: `npm run build` clean before and after every batch of changes; the full Python suite unaffected since this phase touched no `core/` or `backend/` code beyond the already-shipped Phase 12 registry -- `pytest tests/ -m "not slow"` still 67 passed; and the registry's single-experiment response shape was curled live against a real (then removed, not committed) `experiments/` fixture directory to confirm it matches exactly what `ExperimentContext.refreshStages()` expects (`{ experiment: { stages: {...}, ... } }`). |

---
Previous: [Phase 12 — Quick Unlearning Demo & Model Library](../phase-12-quick-demo-model-library/README.md)
Next: [Phase 14 — Backend Service Layer & Compute Backend Architecture](../phase-14-compute-backend-architecture/README.md)
