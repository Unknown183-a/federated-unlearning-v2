# Phase 06 — Federated Learning Visualization & Metrics

> Status: **Complete**
> Implementation: `frontend/src/components/FedAvgDiagram.jsx` (server/client loop diagram), `RoundProgress.jsx` (round progress bar + live per-client checklist + aggregation/global-model status), `MetricLineChart.jsx` (generic round-vs-value SVG line chart, reused for accuracy and loss). Wired together in `frontend/src/pages/FederatedLearning.jsx`, which drives both against `POST /api/training` (fresh run) and `GET /api/training/:experimentId` (stored run) from Phase 05, replaying either round-by-round on the client since the backend always returns the complete history at once.

## Goal

Show the FedAvg loop live: server/client diagram, round progress, per-client update checklist, and accuracy/loss charts.

## In Scope

- Server/client loop diagram component
- Round progress bar + per-client checklist
- Global accuracy vs round chart
- Global loss vs round chart
- Page 4 (full)

## Out of Scope

- Training logic itself (Phase 05)

## Tasks

- [x] Build the server/client FedAvg diagram component
- [x] Build the round progress bar + live per-client checklist
- [x] Build the accuracy-vs-round and loss-vs-round charts
- [x] Wire live vs replay labeling (Measured vs Precomputed, per Ch.46)

## Deliverables

- Complete Page 4: Federated Learning

## Depends On

Phase 05 (FL engine)

## Acceptance Criteria

- A live training run animates round-by-round in the UI
- A precomputed run replays identically and is labeled 'Stored Experiment'

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | Page 4 built end to end: FedAvg diagram, round progress + per-client checklist, and accuracy/loss charts, wired to both `run_federated_training` (labeled "Measured" once the backend responds) and `load_existing` (labeled "Stored Experiment", loaded by experiment ID). Both modes replay the same round-by-round client-side animation, with a "Skip to final result" escape hatch; a warning links to Data Distribution when no partition exists yet for the current experiment. `frontend/npm run build` verified clean. |

---
Previous: [Phase 05 — Federated Learning Engine](../phase-05-federated-learning-engine/README.md)
Next: [Phase 07 — Global Model & Target Client Selection](../phase-07-global-model-target-selection/README.md)
