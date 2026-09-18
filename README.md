# Federated Unlearning Lab — Implementation Plan

This repository tracks the phased implementation of the **Federated Unlearning Lab** interactive dashboard, following the architecture and product specification in `FEDERATED_UNLEARNING_DASHBOARD_SPEC_V2.md`.

Implementation is in progress. See the Phase Index below for what's done and what's still planning-only.

## How to use this repo

1. Work through phases **in order**, Phase 00 through Phase 15.
2. Before starting a phase, read its `README.md` in full — especially "Depends On" and "Out of Scope".
3. As work happens, update that phase's **Status** line and **Progress Log** table.
4. Do not start a phase whose dependencies are not yet marked complete.

## Phase Index

| Phase | Folder | Title | Status |
|-------|--------|-------|--------|
| 00 | [`phase-00-project-setup/`](./phase-00-project-setup/README.md) | Project Setup & Architecture Foundation | Complete |
| 01 | [`phase-01-dataset-layer/`](./phase-01-dataset-layer/README.md) | Dataset Layer | Complete |
| 02 | [`phase-02-experiment-configuration/`](./phase-02-experiment-configuration/README.md) | Experiment Configuration | Complete |
| 03 | [`phase-03-data-partitioning/`](./phase-03-data-partitioning/README.md) | Data Partitioning Engine | Complete |
| 04 | [`phase-04-client-distribution-view/`](./phase-04-client-distribution-view/README.md) | Client Data Distribution View | Complete |
| 05 | [`phase-05-federated-learning-engine/`](./phase-05-federated-learning-engine/README.md) | Federated Learning Engine | Complete |
| 06 | [`phase-06-fl-visualization/`](./phase-06-fl-visualization/README.md) | Federated Learning Visualization & Metrics | Complete |
| 07 | [`phase-07-global-model-target-selection/`](./phase-07-global-model-target-selection/README.md) | Global Model & Target Client Selection | Complete |
| 08 | [`phase-08-gradient-ascent/`](./phase-08-gradient-ascent/README.md) | Unlearning Engine — Gradient Ascent | Complete |
| 09 | [`phase-09-knowledge-distillation/`](./phase-09-knowledge-distillation/README.md) | Knowledge Distillation & Live Unlearning Animation | Complete |
| 10 | [`phase-10-evaluation-mia/`](./phase-10-evaluation-mia/README.md) | Evaluation & Membership Inference Attack | Complete |
| 11 | [`phase-11-comparison-retraining/`](./phase-11-comparison-retraining/README.md) | Before/After, Full Retraining Baseline & Runtime Comparison | Not Started |
| 12 | [`phase-12-quick-demo-model-library/`](./phase-12-quick-demo-model-library/README.md) | Quick Unlearning Demo & Model Library | Not Started |
| 13 | [`phase-13-dashboard-ux/`](./phase-13-dashboard-ux/README.md) | Dashboard UX — Navigation, State & Visual Design System | Not Started |
| 14 | [`phase-14-compute-backend-architecture/`](./phase-14-compute-backend-architecture/README.md) | Backend Service Layer & Compute Backend Architecture | Not Started |
| 15 | [`phase-15-polish-launch/`](./phase-15-polish-launch/README.md) | Error Handling, Reproducibility, Professor Demo Mode & Launch | Not Started |

## Overall Progress

- [x] Phase 00 — Project Setup & Architecture Foundation
- [x] Phase 01 — Dataset Layer
- [x] Phase 02 — Experiment Configuration
- [x] Phase 03 — Data Partitioning Engine
- [x] Phase 04 — Client Data Distribution View
- [x] Phase 05 — Federated Learning Engine
- [x] Phase 06 — Federated Learning Visualization & Metrics
- [x] Phase 07 — Global Model & Target Client Selection
- [x] Phase 08 — Unlearning Engine: Gradient Ascent
- [x] Phase 09 — Knowledge Distillation & Live Animation
- [x] Phase 10 — Evaluation & Membership Inference Attack
- [ ] Phase 11 — Before/After, Retraining Baseline & Runtime Comparison
- [ ] Phase 12 — Quick Unlearning Demo & Model Library
- [ ] Phase 13 — Dashboard UX: Navigation, State & Visual Design
- [ ] Phase 14 — Backend Service Layer & Compute Backend Architecture
- [ ] Phase 15 — Error Handling, Reproducibility, Demo Mode & Launch

## Read the Architecture Document

The full system design lives in a **26-chapter Dashboard Specification Document** — not a wiki page, an actual reference covering the two experiment modes, dataset partitioning, client data distribution, the FedAvg training loop, the Gradient Ascent + Knowledge Distillation unlearning engine, evaluation and MIA, retraining comparisons, dashboard UX, and the full compute backend architecture:

→ [Open the Architecture Document](https://unknown183-a.github.io/federated-unlearning-v2/Federated-Unlearning-Lab-Architecture.html)

The complete underlying product spec is also included in full:

→ [Open the Dashboard Specification (Markdown)](./docs/FEDERATED_UNLEARNING_DASHBOARD_SPEC_V2.md)
