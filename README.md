# Federated Unlearning Lab — Implementation Plan

This repository tracks the phased implementation of the **Federated Unlearning Lab** interactive dashboard, following the architecture and product specification in `FEDERATED_UNLEARNING_DASHBOARD_SPEC_V2.md`.

Implementation of Phases 00–14 and Phase 16 is complete, and Phase 15 (hardening and launch) is code-complete with its 3-dataset acceptance run pending. See the Phase Index below.

## How to use this repo

1. Work through phases **in order**, Phase 00 through Phase 15.
2. Before starting a phase, read its `README.md` in full — especially "Depends On" and "Out of Scope".
3. As work happens, update that phase's **Status** line and **Progress Log** table.
4. Do not start a phase whose dependencies are not yet marked complete.

## Quick start

You need Python 3.10+ with the packages in `core/requirements.txt` (this includes PyTorch), and Node.js 18+.

1. Install Python packages: `pip install -r core/requirements.txt`
2. Install the backend: `cd backend && npm install`
3. Install the frontend: `cd frontend && npm install`
4. Start the backend (port 4000): `cd backend && npm start`
5. Start the frontend: `cd frontend && npm run dev`, then open the address it prints.
6. Run the tests: `python -m pytest tests -q`

Optional: copy `.env.example` to `.env` to configure remote GPU backends (see [`docs/COMPUTE_BACKENDS.md`](./docs/COMPUTE_BACKENDS.md)). Without it, the app runs on your own machine.

## Make a demo experiment

In Research Mode, work down the left menu once: **Setup**, **Data Distribution**, **Federated Learning**, **Client Selection**, **Unlearning**, **Evaluation**, **Retraining Comparison**. Everything is saved in `experiments/<id>/`. When all stages are finished, the experiment shows as *Replayable* in Experiment History and appears on the Professor Demo page.

## Professor Demo Mode

Switch to **Professor Demo** (top of the left menu), choose a stored experiment and press **START DEMO**. It replays the whole story (data split, training, client selection, unlearning, results, retraining comparison) in about 10 minutes, with a speaking guide on every page. It **never trains or re-runs anything**, so it works with no GPU and no live backend. The talk track is in [`docs/DEMO_SCRIPT.md`](./docs/DEMO_SCRIPT.md).

## Model updates

After unlearning, publish the unlearned model as a new version for devices that already installed the old one: **Auto update**, or **Request, then update automatically after a deadline**. See [`docs/MODEL_UPDATES.md`](./docs/MODEL_UPDATES.md). Devices are simulated.

## How results are labelled

Every result screen shows one label, so you always know where a number came from.

| Label | Meaning |
|-------|---------|
| Measured | Computed by a real run in this session |
| Precomputed · Stored Experiment | Replayed from an earlier real run |
| Live | A run in progress right now |
| Illustrative | A diagram only, never a result |

Nothing is invented: an unfinished or unreadable stored result is refused with a clear message instead of being drawn as if it were final.

## Reproducibility

Every result screen has a collapsible **Experiment Configuration & Seed** panel: dataset, clients, partition, seed, model, rounds, local epochs, unlearning method and hyperparameters, target client, and the software version (git commit). Values the stored files do not contain are shown as "not recorded", never guessed. Runs made before Phase 15 do not have unlearning hyperparameters saved; re-run unlearning to record them.

## Checking an experiment

`python -m core.acceptance.cli --all` checks every stored experiment against the machine-checkable parts of the spec's acceptance checklist (complete files, consistent numbers, measured runtimes, retraining really excluded the target). It needs no GPU or torch. The full checklist, including the parts you check by eye, is in [`docs/ACCEPTANCE_CHECKLIST.md`](./docs/ACCEPTANCE_CHECKLIST.md).

## When something fails

Failures show what failed, which stage, and what to do next (Retry, Run Training, Select Another Experiment, and so on). The technical error is under "Technical details". A stage that runs longer than 15 minutes is stopped and reported; change the limit with `ENGINE_TIMEOUT_MS` (milliseconds). Set `PYTHON_BIN` if your Python is not called `python3`.

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
| 11 | [`phase-11-comparison-retraining/`](./phase-11-comparison-retraining/README.md) | Before/After, Full Retraining Baseline & Runtime Comparison | Complete |
| 12 | [`phase-12-quick-demo-model-library/`](./phase-12-quick-demo-model-library/README.md) | Quick Unlearning Demo & Model Library | Complete |
| 13 | [`phase-13-dashboard-ux/`](./phase-13-dashboard-ux/README.md) | Dashboard UX — Navigation, State & Visual Design System | Complete |
| 14 | [`phase-14-compute-backend-architecture/`](./phase-14-compute-backend-architecture/README.md) | Backend Service Layer & Compute Backend Architecture | Complete |
| 15 | [`phase-15-polish-launch/`](./phase-15-polish-launch/README.md) | Error Handling, Reproducibility, Professor Demo Mode & Launch | In Progress (code done; 3-dataset acceptance run pending) |
| 16 | [`phase-16-model-updates/`](./phase-16-model-updates/README.md) | Model Releases & Update Policy | Complete |

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
- [x] Phase 11 — Before/After, Retraining Baseline & Runtime Comparison
- [x] Phase 12 — Quick Unlearning Demo & Model Library
- [x] Phase 13 — Dashboard UX: Navigation, State & Visual Design
- [x] Phase 14 — Backend Service Layer & Compute Backend Architecture
- [ ] Phase 15 — Error Handling, Reproducibility, Demo Mode & Launch (code complete; run the acceptance checklist on all 3 datasets to close it)
- [x] Phase 16 — Model Releases & Update Policy

## Read the Architecture Document

The full system design lives in a **26-chapter Dashboard Specification Document** — not a wiki page, an actual reference covering the two experiment modes, dataset partitioning, client data distribution, the FedAvg training loop, the Gradient Ascent + Knowledge Distillation unlearning engine, evaluation and MIA, retraining comparisons, dashboard UX, and the full compute backend architecture:

→ [Open the Architecture Document](https://unknown183-a.github.io/federated-unlearning-v2/Federated-Unlearning-Lab-Architecture.html)

The complete underlying product spec is also included in full:

→ [Open the Dashboard Specification (Markdown)](./docs/FEDERATED_UNLEARNING_DASHBOARD_SPEC_V2.md)


# README Update: Research Extension Proposal for Federated Unlearning

> **Status: Proposed research extension --- not yet implemented or
> experimentally validated.**
>
> This file is an additive README update. Append the section below to
> the existing `README.md`; do not replace or delete existing project
> documentation. Keep all claims about implementation and results
> aligned with the current code and experiments.

------------------------------------------------------------------------

## Proposed Research Extension: Heterogeneity-Aware Adaptive Federated Unlearning (HAFU)

### Motivation

The current project studies client-level federated unlearning using
Gradient Ascent (GA) and Knowledge Distillation (KD), with full
retraining as a reference baseline. A potential extension is to
investigate whether the forgetting strength and knowledge-recovery
strategy should adapt to client-data heterogeneity rather than use fixed
settings.

We use **HAFU (Heterogeneity-Aware Adaptive Federated Unlearning)** as a
working name for this research proposal. The name does not imply that
the method is novel, implemented, or proven superior. A focused
literature review and experiments are required before making a novelty
claim.

### Research Question

Can an adaptive unlearning controller that accounts for client
heterogeneity improve the trade-off between forgetting the target
client's influence and preserving the utility of retained clients,
compared with fixed-strength GA+KD?

### Proposed Method

The proposed pipeline is:

``` text
Federated Training (e.g., FedAvg)
              |
              v
Select Target / Forget Client
              |
              v
Measure Client Heterogeneity
              |
              v
Adaptive Gradient-Ascent Forgetting
              |
              v
Class-Aware Knowledge Recovery
              |
              v
Evaluate Forgetting, Utility, Privacy Risk, and Cost
              |
              v
Compare Against GA+KD and Full Retraining
```

#### 1. Client-heterogeneity analysis

Estimate how the target client's data distribution differs from the
retained-client distributions. In simulated experiments, this can use
known partition statistics; in a privacy-conscious deployment, the
method should specify what statistics can be computed without exposing
raw client data.

Possible measurements include label-distribution divergence and class
coverage. The exact metric must be selected and justified during
implementation.

#### 2. Adaptive forgetting strength

Instead of fixing the Gradient Ascent strength for every unlearning
request, adapt it according to measured forgetting and retained-client
utility. For example, the controller may increase forgetting strength
when the forgetting target is not met, and reduce it or trigger recovery
when retained-client utility degrades beyond a predefined tolerance.

A basic gradient-ascent update can be written as:

$$\theta' = \theta + \eta \lambda_f \nabla_\theta \mathcal{L}_f(\theta)$$

where $\theta$ denotes model parameters, $\eta$ is the
learning rate, $\lambda_f$ is the forgetting-strength
coefficient, and $\mathcal{L}_f$ is the loss on the target
client's forget data. The adaptive rule for $\lambda_f$ is a
research component to be defined and evaluated; this equation alone is
not a novel contribution.

#### 3. Class-aware knowledge recovery

Investigate whether the distillation objective can weight classes
according to evidence that they remain represented in retained clients.
The aim is to recover useful retained knowledge without indiscriminately
restoring behavior associated with the forgotten client.

A candidate objective is:

$$\mathcal{L}_{KD} = \sum_{c} w_c \, D_{KL}\left(p_T^c \,\|\, p_S^c\right)$$

where $p_T^c$ and $p_S^c$ are teacher and student predictive
distributions for class $c$, and $w_c$ is a class-retention weight
derived from retained-client information. This is a design hypothesis,
not a guarantee of client-level forgetting: when classes overlap across
clients, class-level weights may not distinguish which client
contributed the knowledge.

#### 4. Joint control objective

Explore a controller that balances forgetting, retained-client utility,
and privacy-risk measurements:

$$J = \alpha F + \beta U - \gamma R$$

Here, (F) represents a defined forgetting score, (U) retained-client
utility, and (R) a privacy-risk measure such as membership-inference
attack performance. The exact definitions, optimization direction,
constraints, and coefficients must be specified before experiments.
Attack metrics are empirical evidence and do not constitute a formal
guarantee that information has been erased.

### Evaluation Plan

Compare the proposed method against:

-   The original federated model before unlearning.
-   Full retraining without the target client, as a reference baseline.
-   The existing GA+KD implementation.
-   Adaptive GA without class-aware KD (ablation).
-   GA with class-aware KD but without adaptive control (ablation).
-   The complete proposed method.
-   Relevant published federated-unlearning baselines, where
    implementations and experimental conditions permit a fair
    comparison.

Evaluate under both IID and multiple non-IID client partitions. Vary the
target client and random seed, and report mean and standard deviation.

Recommended metrics:

-   Retained-client test accuracy and macro-F1.
-   Forget-client behavior and forgetting effectiveness, with clearly
    defined metrics.
-   Membership-inference attack performance, where implemented.
-   Similarity to the full-retraining reference.
-   Unlearning runtime and computational overhead.
-   Communication cost, if communication is measured by the
    implementation.
-   Performance under repeated deletion requests, if supported.

Do not infer successful unlearning from low forget-client accuracy
alone. Report the trade-off between forgetting, retained utility,
privacy-risk measurements, and efficiency.

### Research Novelty and Limitations

GA, KD, client-heterogeneity analysis, and adaptive optimization are
established research ideas. Combining them does not by itself establish
novelty. Before presenting HAFU as a novel method, review closely
related work and determine whether the specific controller, objective,
and class-aware recovery mechanism already exist.

A defensible contribution would require:

1.  A precisely specified mechanism that differs from relevant prior
    methods.
2.  A reproducible implementation and controlled experiments.
3.  Ablation studies showing which components provide benefit.
4.  Consistent improvements over appropriate baselines, including GA+KD
    and full retraining as a reference.
5.  A careful discussion of limitations and any privacy or deletion
    guarantees that are---and are not---provided.

This proposal does not claim certified or exact machine unlearning. Full
retraining without the target client's data is a useful reference, but
its guarantee depends on the training procedure and the scope of the
deletion request.

### Implementation Status

-   **Existing project:** Federated-learning and unlearning components
    should be described as implemented only when confirmed in the
    current repository.
-   **HAFU proposal:** Not implemented or experimentally validated
    unless subsequent code and results establish otherwise.
-   **Results:** No accuracy, forgetting, privacy, runtime, or
    communication results are claimed in this proposal.
-   **Next step:** Review related literature, define the adaptive
    controller mathematically, implement it as a separate experimental
    method, and compare it against the existing GA+KD baseline using
    reproducible configurations.

### Suggested Repository Organization (after implementation)

Add files only when the corresponding functionality is implemented.
Adapt names to the repository's actual structure.

``` text
configs/
  hafu.yaml

src/
  unlearning/
    adaptive_controller.py
    heterogeneity.py
    class_aware_distillation.py
    hafu.py

scripts/
  run_hafu.py

tests/
  test_adaptive_controller.py
  test_class_aware_distillation.py

artifacts/
  hafu/
```

Do not add placeholder paths to the main README as if they already
exist. Update the main README's commands, architecture, and status only
after the code is present and tested.
