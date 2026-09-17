# Federated Unlearning Lab — Complete Interactive Dashboard Specification

## 0. Purpose

This document is the complete product, UI, visualization, workflow, and backend specification for an interactive **Federated Learning + Machine Unlearning Dashboard**.

The goal is to turn the existing federated-unlearning research pipeline into a professor-friendly visual demonstration.

The dashboard must make the complete research story visible:

**Dataset → Data Partitioning → Client Data Distribution → Federated Learning → Global Model → Target Client Selection → Gradient Ascent → Knowledge Distillation → Unlearned Model → Evaluation → Comparison with Retraining**

The dashboard must support two modes:

1. **Complete FL + Unlearning Experiment**
2. **Quick Unlearning Demo using already-trained/pretrained federated models**

The application should not require full model training during every professor demonstration. Training can be performed offline and the resulting global model/checkpoints can be loaded. Unlearning should be executable live when possible.

---

# 1. Product Vision

The dashboard should look like a **Federated Unlearning Laboratory**, not merely a collection of accuracy tables.

A professor should be able to understand the system visually without opening source code.

The central question demonstrated by the dashboard is:

> "Can we remove the influence of one federated client from an already-trained global model without retraining the entire federated system from scratch?"

The dashboard should clearly show:

- What dataset is being used
- How the dataset is divided among clients
- What each client owns
- How local client training happens
- How the server aggregates models using FedAvg
- How the global model is obtained
- Which client is selected for forgetting
- How Gradient Ascent removes the target client's influence
- How Knowledge Distillation preserves useful knowledge
- How the final unlearned model performs
- Whether the target client's information has actually been forgotten
- How the result compares with the original model
- How the result compares with full retraining
- How long unlearning takes

---

# 2. Main Dashboard Modes

The landing page must provide two large choices.

```text
FEDERATED UNLEARNING LAB

Choose Experiment Mode

┌─────────────────────────────────────────┐
│ COMPLETE FL + UNLEARNING                │
│                                         │
│ Dataset → Partition → FL → Unlearning  │
│ → Evaluation                            │
│                                         │
│ [ Start Complete Experiment ]           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ QUICK UNLEARNING DEMO                   │
│                                         │
│ Pretrained Model → Client → Unlearn    │
│ → Evaluation                            │
│                                         │
│ [ Start Quick Demo ]                    │
└─────────────────────────────────────────┘
```

## 2.1 Complete FL + Unlearning

This mode demonstrates the complete pipeline.

Flow:

```text
Dataset Selection
        ↓
Experiment Configuration
        ↓
Dataset Partitioning
        ↓
Client Data Distribution
        ↓
Federated Learning
        ↓
Trained Global Model
        ↓
Target Client Selection
        ↓
Unlearning
        ↓
Evaluation
        ↓
Comparison
```

Training may be loaded from a precomputed experiment if live training would take too long.

## 2.2 Quick Unlearning Demo

This mode is optimized for a 5–15 minute professor demonstration.

Flow:

```text
Select Existing Model
        ↓
View Model Metadata
        ↓
Select Target Client
        ↓
Remove Influence
        ↓
Gradient Ascent
        ↓
Knowledge Distillation
        ↓
Evaluation
        ↓
Before vs After vs Retraining
```

The model is already trained.

Only the unlearning pipeline needs to execute live.

---

# 3. Supported Datasets

Initial dashboard dataset choices:

- MNIST
- CIFAR-10
- CIFAR-100

Dataset cards should show:

```text
MNIST
28 × 28
Grayscale
10 Classes

CIFAR-10
32 × 32
RGB
10 Classes

CIFAR-100
32 × 32
RGB
100 Classes
```

The architecture should be extensible so additional datasets can be added later.

Do not hard-code the dashboard around only one dataset.

---

# 4. Experiment Configuration

After selecting a dataset, show:

```text
Dataset
[ CIFAR-100 ▼ ]

Number of Clients
[ 10 ]

Partition Strategy
[ Non-IID ▼ ]

Federated Rounds
[ 20 ]

Local Epochs
[ 1 ]

Model
[ ResNet / CNN ▼ ]

Random Seed
[ 42 ]

Training Mode
○ Load Existing Experiment
○ Run Federated Training
```

Important:

The number of clients must be dynamic.

Examples:

- 5 clients
- 10 clients
- 20 clients

The dashboard must not assume that the system always has exactly five clients.

---

# 5. Dataset Preparation

The dataset stage must be visible.

```text
SELECTED DATASET
        ↓
Download / Load Dataset
        ↓
Preprocessing
        ↓
Train / Test Split
        ↓
Partitioning Engine
        ↓
Client Datasets
```

Show dataset metadata:

- Number of training samples
- Number of test samples
- Number of classes
- Image dimensions
- Dataset type
- Partition strategy
- Number of clients

Example:

```text
Dataset: CIFAR-10

Training Samples: 50,000
Test Samples: 10,000
Classes: 10
Clients: 10
Partition: Non-IID
```

---

# 6. Data Partitioning

This is a mandatory visible stage.

The dashboard must clearly explain that the central dataset is divided into client-specific datasets before federated training.

Visual structure:

```text
                     DATASET
                        │
                        ▼
               PARTITIONING ENGINE
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
     CLIENT 1        CLIENT 2        CLIENT 3
        │               │               │
       ...             ...             ...
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                   CLIENT N
```

The dashboard must show:

- Samples per client
- Classes per client
- Class distribution
- IID vs Non-IID status
- Partition method
- Random seed

---

# 7. Client Data Distribution View

Create a dedicated **Client Distribution** section/page.

## 7.1 Client Cards

For every client:

```text
CLIENT 1

Samples
5,000

Classes
10

Dominant Classes
Cat
Dog
Bird

Distribution
Non-IID
```

## 7.2 Class Distribution Heatmap

Show:

```text
                 Classes
Client     0  1  2  3  4  5  6  7  8  9

Client 1   █  ███ █  ░  ░  ██ ░  ░  ███ ░
Client 2   ░  █  ███ ██ ░  ░  ███ ░  ░  ██
Client 3   ██ ░  ░  ███ █  ██ ░  █  ░  ░
...
```

For CIFAR-100, the heatmap must be scrollable or grouped because there are 100 classes.

## 7.3 Distribution Summary

Show:

```text
Total Samples
50,000

Clients
10

Average Samples / Client
5,000

Most Imbalanced Client
Client X

Partition
Non-IID
```

---

# 8. Federated Learning Visualization

Federated Learning must be clearly visible as a separate stage.

The dashboard should show the server and clients.

```text
                         SERVER
                    ┌─────────────┐
                    │ Global Model│
                    └──────┬──────┘
                           │
                  Broadcast Global Model
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CLIENT 1   │     │  CLIENT 2   │     │  CLIENT 3   │
│             │     │             │     │             │
│ Local Data  │     │ Local Data  │     │ Local Data  │
│ Local Train │     │ Local Train │     │ Local Train │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    Model Updates
                           │
                           ▼
                    ┌─────────────┐
                    │   FedAvg    │
                    └──────┬──────┘
                           │
                           ▼
                    Updated Global
                       Model
                           │
                        Round 2
                           │
                          ...
```

This diagram must be visible in the dashboard.

---

# 9. Federated Learning Round Visualization

The training page should have a round selector/progress bar.

```text
Federated Training

Round 1 / 20
████░░░░░░░░░░░░░░░░

Client Updates
✓ Client 1
✓ Client 2
✓ Client 3
...
✓ Client 10

Aggregation
✓ FedAvg

Global Model
✓ Updated
```

If precomputed training is being used, the dashboard should replay the training progression from stored metrics.

Do not pretend that training is live if it was precomputed.

Use labels such as:

> "Replay from stored experiment"

---

# 10. Federated Learning Metrics

Show:

- Global accuracy
- Global loss
- Round number
- Client participation
- Local training loss
- Aggregation status
- Total training time

Main charts:

### Global Accuracy vs Round

```text
Accuracy
  │
  │              ______
  │          ___/
  │      ___/
  │   __/
  │__/
  └──────────────────────
       Federated Round
```

### Global Loss vs Round

```text
Loss
 │\
 │ \
 │  \
 │   \____
 │        \____
 └────────────────
       Round
```

All displayed values must come from actual experiment artifacts.

---

# 11. Trained Global Model

After FL:

```text
FEDERATED TRAINING COMPLETE

Dataset: CIFAR-100
Clients: 10
Rounds: 20

Global Accuracy
61.20%

Global Loss
1.42

Checkpoint
✓ Available

Training Source
Precomputed / Live
```

The global model becomes the input to the unlearning stage.

---

# 12. Target Client Selection

This is the transition from Federated Learning to Machine Unlearning.

Show all clients as selectable cards.

```text
SELECT CLIENT TO FORGET

┌────────┐ ┌────────┐ ┌────────┐
│Client 1│ │Client 2│ │Client 3│
│ 5,000  │ │ 5,000  │ │ 5,000  │
└────────┘ └────────┘ └────────┘

┌────────┐ ┌────────┐ ┌────────┐
│Client 4│ │Client 5│ │Client 6│
└────────┘ └────────┘ └────────┘

...

Selected Client:
CLIENT 3

[ REMOVE INFLUENCE ]
```

When Client 3 is selected, visually highlight:

```text
Global Model
     │
     ├── Client 1
     ├── Client 2
     ├── Client 3  ← TARGET
     ├── Client 4
     └── ...
```

---

# 13. Unlearning Overview

Once the user clicks:

**REMOVE INFLUENCE**

start the unlearning visualization.

Main flow:

```text
TRAINED GLOBAL MODEL
        │
        ▼
 TARGET CLIENT
        │
        ▼
 GRADIENT ASCENT
        │
        ▼
 REMOVE CLIENT INFLUENCE
        │
        ▼
 KNOWLEDGE DISTILLATION
        │
        ▼
 UNLEARNED MODEL
        │
        ▼
 EVALUATION
```

The UI should show a live progress indicator.

---

# 14. Unlearning Status Timeline

Use a stepper:

```text
① Model Loaded        ✓
        ↓
② Target Client       ✓
        ↓
③ Gradient Ascent     ● RUNNING
        ↓
④ Knowledge Distill.  ○ WAITING
        ↓
⑤ Evaluation          ○ WAITING
        ↓
⑥ Final Results       ○ WAITING
```

When a stage completes, change it to completed.

---

# 15. Gradient Ascent Visualization

Gradient Ascent must have its own panel.

Show:

```text
GRADIENT ASCENT

Target Client: Client 3

Purpose:
Reduce the model's ability to reproduce the target client's learned
information.

Iteration
0 ─────────────────────────── 100%

Current Iteration: 24 / 50

Target Client Loss
████████████████░░░░

Target Client Accuracy
████████░░░░░░░░░░░░

Status:
Removing client influence...
```

Also show a live chart:

- Iteration on X-axis
- Target-client loss
- Target-client accuracy
- Optional gradient magnitude

Important:

The dashboard must use the actual values produced by the unlearning implementation.

Do not use hard-coded illustrative values in the real dashboard.

---

# 16. Gradient Ascent Interpretation

Include a small explanation box:

```text
WHAT IS HAPPENING?

The unlearning procedure updates the model in a direction that
reduces its dependence on the selected client's learned information.

Target:
Client 3

The dashboard tracks the optimization process so the user can
visually observe the effect of the unlearning stage.
```

The wording should match the actual implementation and research method.

---

# 17. Knowledge Distillation Visualization

After Gradient Ascent:

```text
GRADIENT ASCENT COMPLETE ✓
              │
              ▼
      KNOWLEDGE DISTILLATION
```

Visualize:

```text
                 ORIGINAL MODEL
                    TEACHER
                       │
                       │ Soft Predictions
                       ▼
                ┌─────────────┐
                │     KD      │
                │             │
                │ KD Loss     │
                │ Temperature │
                └──────┬──────┘
                       │
                       ▼
                UNLEARNED MODEL
                   STUDENT
```

The panel should display:

- Teacher model
- Student model
- Temperature, if used
- KD loss
- Iterations/epochs
- Current progress
- Final KD loss

---

# 18. Knowledge Distillation Graph

Show:

```text
KD Loss
  │\
  │ \
  │  \
  │   \____
  │        \____
  └────────────────
       Iteration
```

Again, values must be actual experimental values.

---

# 19. Live Unlearning Animation

The dashboard should make it visually obvious that the target client's influence is being removed.

Example visual state:

```text
CLIENT INFLUENCE

Client 1  ████████████████
Client 2  ██████████████
Client 3  ████████████████  ← BEFORE

             ↓
        UNLEARNING
             ↓

Client 1  ████████████████
Client 2  ██████████████
Client 3  ████             ← AFTER
```

Important:

If the project does not calculate a formal influence score, do not invent one.

Instead, use a visual representation based on actual measurable metrics, such as target-client accuracy, loss, membership inference performance, or another implemented influence proxy.

---

# 20. Unlearned Model

After GA + KD:

```text
UNLEARNING COMPLETE ✓

Original Model
      ↓
Gradient Ascent
      ↓
Knowledge Distillation
      ↓
Unlearned Model

Checkpoint:
✓ Saved
```

Show model metadata.

---

# 21. Final Evaluation

The final evaluation page is one of the most important screens.

Show four major metric cards.

```text
┌────────────────────┐
│ GLOBAL ACCURACY    │
│                    │
│ Before: 60.02%     │
│ After:  57.78%     │
└────────────────────┘

┌────────────────────┐
│ FORGET CLIENT ACC. │
│                    │
│ Before: XX.XX%     │
│ After:  XX.XX%     │
└────────────────────┘

┌────────────────────┐
│ MIA SUCCESS        │
│                    │
│ Before: XX.XX%     │
│ After:  XX.XX%     │
└────────────────────┘

┌────────────────────┐
│ UNLEARNING TIME    │
│                    │
│ XX seconds         │
└────────────────────┘
```

The values above are examples except where they are explicitly sourced from existing project results.

---

# 22. Metrics to Evaluate

At minimum:

## Global Model Accuracy

How much overall performance remains after unlearning.

## Forget-Client Accuracy

Performance on the selected client's data.

This helps demonstrate whether the selected client's information has been removed.

## Retained-Client Performance

Performance on data belonging to clients that should remain.

This helps demonstrate whether useful knowledge was preserved.

## Membership Inference Attack (MIA)

Show the MIA result before and after unlearning.

Goal:

```text
MIA Success
      ↓
Should decrease after effective forgetting
```

The exact interpretation must follow the project's implemented MIA methodology.

## Runtime

Measure:

- Gradient Ascent time
- Knowledge Distillation time
- Total unlearning time

---

# 23. Before vs After Visualization

Create a dedicated comparison area.

```text
                BEFORE          AFTER

Global Acc.      XX%             XX%
Forget Acc.      XX%             XX%
Retained Acc.    XX%             XX%
MIA              XX%             XX%
```

Use:

- grouped bars
- metric cards
- arrows
- percentage change

Do not exaggerate improvements.

If a metric gets worse, show that honestly.

---

# 24. Full Retraining Baseline

A major research comparison should be:

```text
                    ORIGINAL
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
      UNLEARNING             FULL RETRAINING
       GA + KD                     │
             │                     │
             ▼                     ▼
      UNLEARNED MODEL        RETRAINED MODEL
             │                     │
             └──────────┬──────────┘
                        ▼
                    COMPARISON
```

Compare:

- Global accuracy
- Forget-client accuracy
- Retained-client accuracy
- MIA
- Runtime

The important research point is to show whether unlearning can approach the retraining outcome without paying the cost of complete retraining.

---

# 25. Runtime Comparison

Show:

```text
METHOD

Full Retraining     ████████████████████████
GA + KD             █████

Time Saved
XX%
```

Use actual measured times.

Do not claim a speedup unless measured.

---

# 26. Complete Research Story

The professor should be able to follow this story:

```text
1. Choose Dataset
       ↓
2. Choose Number of Clients
       ↓
3. Partition Dataset
       ↓
4. Inspect Client Distributions
       ↓
5. Federated Training
       ↓
6. Global Model Created
       ↓
7. Select Client to Forget
       ↓
8. Gradient Ascent
       ↓
9. Knowledge Distillation
       ↓
10. Unlearned Model
       ↓
11. Accuracy Evaluation
       ↓
12. MIA Evaluation
       ↓
13. Compare with Original
       ↓
14. Compare with Full Retraining
```

This must be the primary narrative of the application.

---

# 27. Quick Unlearning Demo

The Quick Demo must start from a library of trained models.

Example:

```text
AVAILABLE FEDERATED MODELS

┌─────────────────────────────┐
│ MNIST                       │
│ Clients: 10                 │
│ Rounds: 20                  │
│ Accuracy: XX%               │
│ Status: READY               │
│ [ SELECT ]                  │
└─────────────────────────────┘

┌─────────────────────────────┐
│ CIFAR-10                    │
│ Clients: 10                 │
│ Rounds: 20                  │
│ Accuracy: XX%               │
│ Status: READY               │
│ [ SELECT ]                  │
└─────────────────────────────┘

┌─────────────────────────────┐
│ CIFAR-100                   │
│ Clients: 10                 │
│ Rounds: 20                  │
│ Accuracy: XX%               │
│ Status: READY               │
│ [ SELECT ]                  │
└─────────────────────────────┘
```

Selecting CIFAR-100 should automatically load:

- Dataset metadata
- Client partition metadata
- Global model checkpoint
- Client datasets/indexes
- Baseline metrics
- Unlearning configuration

---

# 28. Quick Demo Flow

```text
SELECT MODEL
     │
     ▼
MODEL INFORMATION
     │
     ▼
SELECT CLIENT
     │
     ▼
REMOVE INFLUENCE
     │
     ▼
GRADIENT ASCENT
     │
     ▼
KNOWLEDGE DISTILLATION
     │
     ▼
EVALUATION
     │
     ▼
FINAL RESULT
```

This mode should avoid full FL training.

---

# 29. Model Library

The backend should maintain a model registry.

Conceptually:

```text
models/
├── mnist/
│   ├── global_model.pt
│   ├── metadata.json
│   └── metrics.json
│
├── cifar10/
│   ├── global_model.pt
│   ├── metadata.json
│   └── metrics.json
│
└── cifar100/
    ├── global_model.pt
    ├── metadata.json
    └── metrics.json
```

For multiple configurations:

```text
models/
├── cifar100/
│   ├── clients_5/
│   ├── clients_10/
│   └── clients_20/
```

The exact storage system can be local files, object storage, database records, or another backend.

---

# 30. Experiment Artifact Structure

Each experiment should have a machine-readable manifest.

Example:

```json
{
  "experiment_id": "cifar100_10clients_seed42",
  "dataset": "cifar100",
  "num_clients": 10,
  "partition_strategy": "non_iid",
  "seed": 42,
  "model": "resnet",
  "federated_rounds": 20,
  "local_epochs": 1,
  "checkpoint": "global_model.pt"
}
```

The manifest should be treated as the source of truth for loading an experiment.

---

# 31. Unlearning Artifact

Each unlearning run should save a result record.

Example:

```json
{
  "experiment_id": "cifar100_10clients_seed42",
  "target_client": 3,
  "method": "GA+KD",
  "baseline": {
    "global_accuracy": 0.0,
    "forget_client_accuracy": 0.0,
    "mia": 0.0
  },
  "unlearning": {
    "gradient_ascent": [],
    "knowledge_distillation": []
  },
  "final": {
    "global_accuracy": 0.0,
    "forget_client_accuracy": 0.0,
    "retained_client_accuracy": 0.0,
    "mia": 0.0
  },
  "runtime_seconds": 0
}
```

The zeros above are placeholders for schema definition only.

The real application must populate them from experiment results.

---

# 32. Dashboard Page Structure

Recommended pages:

## Page 1 — Overview

Purpose:

Explain the project.

Show:

- Project title
- Research objective
- Two experiment modes
- High-level pipeline
- Current experiment status

---

## Page 2 — Experiment Setup

Controls:

- Dataset
- Number of clients
- Partition strategy
- Model
- Federated rounds
- Local epochs
- Seed
- Training source

---

## Page 3 — Data Distribution

Show:

- Dataset statistics
- Partitioning
- Client cards
- Samples/client
- Class distribution
- Heatmap
- IID/Non-IID information

---

## Page 4 — Federated Learning

Show:

- Server
- Clients
- Local training
- FedAvg
- Round progress
- Accuracy curve
- Loss curve
- Global model status

---

## Page 5 — Client Selection

Show:

- Global model
- All clients
- Client data information
- Target client selection
- Remove influence button

---

## Page 6 — Unlearning

Show:

- Original model
- Target client
- Gradient Ascent
- GA progress
- GA loss
- Client accuracy
- Knowledge Distillation
- KD loss
- Final unlearned model

---

## Page 7 — Evaluation

Show:

- Global accuracy
- Forget-client accuracy
- Retained-client accuracy
- MIA
- Runtime
- Before/after comparison

---

## Page 8 — Retraining Comparison

Show:

```text
GA + KD
vs
Full Retraining
```

Compare:

- Accuracy
- Forgetting
- MIA
- Runtime

---

## Page 9 — Experiment History

Show previous experiments:

```text
Experiment              Dataset     Clients    Target    Status

cifar100_exp_01         CIFAR-100   10         C3        ✓
cifar10_exp_02          CIFAR-10    10         C7        ✓
mnist_exp_03            MNIST       5          C2        ✓
```

Allow the user to reopen a result.

---

# 33. Global Navigation

Sidebar:

```text
FEDERATED UNLEARNING LAB

Mode
○ Complete Experiment
○ Quick Unlearning

──────────────────

Experiment
Overview
Setup
Data Distribution
Federated Learning

Unlearning
Client Selection
Unlearning Process

Evaluation
Results
Retraining Comparison
History
```

A progress indicator should show the current stage.

---

# 34. State Management

The dashboard must maintain an experiment state.

Conceptually:

```text
state = {
    dataset,
    num_clients,
    partition_strategy,
    experiment_id,
    selected_model,
    selected_client,
    training_status,
    training_checkpoint,
    unlearning_status,
    unlearning_method,
    evaluation_results
}
```

Changing the dataset should reset incompatible experiment state.

Changing the number of clients should load/create the correct experiment configuration.

Selecting a client should not change the trained model.

---

# 35. Backend Service Boundaries

Recommended backend modules:

```text
Dataset Manager
        │
        ▼
Partition Manager
        │
        ▼
Federated Trainer
        │
        ▼
Model Registry
        │
        ▼
Unlearning Engine
        │
        ├── Gradient Ascent
        │
        └── Knowledge Distillation
        │
        ▼
Evaluation Engine
        │
        ├── Accuracy
        ├── Forget Accuracy
        ├── Retained Accuracy
        ├── MIA
        └── Runtime
```

The UI should not contain the ML algorithms themselves.

The UI should call backend functions/services.

---

# 36. Suggested Backend Functions

Conceptual interface:

```python
load_dataset(name)

partition_dataset(
    dataset,
    num_clients,
    strategy,
    seed
)

load_experiment(experiment_id)

run_federated_training(config)

load_global_model(experiment_id)

get_client_distribution(experiment_id, client_id)

get_training_metrics(experiment_id)

run_gradient_ascent(
    model,
    target_client,
    config
)

run_knowledge_distillation(
    teacher_model,
    student_model,
    config
)

run_unlearning(
    experiment_id,
    target_client
)

evaluate_model(
    model,
    experiment_id,
    target_client
)

compare_with_retraining(
    unlearned_results,
    retraining_results
)
```

These are architectural interfaces. They should be mapped to the actual existing repository functions rather than blindly duplicated.

---

# 37. Live vs Precomputed Strategy

This is critical for the professor demonstration.

## Federated Training

Prefer:

**Precomputed / checkpoint loading**

because full training can take too long.

The dashboard can replay:

- rounds
- accuracy
- loss
- client participation

from stored metrics.

## Unlearning

Prefer:

**Live execution**

if the actual GA + KD process consistently completes within an acceptable demo window.

Before making live unlearning the default, benchmark it.

Target:

```text
Preferred:
1–5 minutes

Maximum practical demo:
~10 minutes
```

If live execution is unreliable, use precomputed unlearning results while clearly labeling them as precomputed.

---

# 38. Demo Mode for Professors

Add a dedicated toggle:

```text
DEMO MODE

○ Research Mode
○ Professor Demo Mode
```

Professor Demo Mode should:

- Use cached datasets
- Use existing model checkpoints
- Skip downloads
- Skip long training
- Show important visualizations
- Run unlearning live if possible
- Keep the interface simple

Optional:

```text
Demo Dataset
[ CIFAR-10 ▼ ]

Demo Clients
[ 10 ]

Target Client
[ Client 3 ▼ ]

[ START DEMO ]
```

---

# 39. What Must NOT Happen

The dashboard must not:

1. Train a huge model from scratch automatically when the professor clicks the demo.
2. Pretend precomputed results are live.
3. Display fabricated metric values.
4. Hard-code Client 0 as the only supported client.
5. Hide data partitioning.
6. Hide federated aggregation.
7. Show only final accuracy.
8. Claim forgetting based only on global accuracy.
9. Claim MIA improvement without actually running/evaluating MIA.
10. Claim faster-than-retraining performance without measuring runtime.

---

# 40. Visual Design

The interface should be:

- Scientific
- Clean
- Modern
- Professional
- Easy to understand
- Suitable for an academic presentation

Avoid excessive:

- Neon colors
- Futuristic animations
- Gaming-style effects
- Unnecessary 3D graphics

Use:

- Cards
- Progress indicators
- Flow diagrams
- Network diagrams
- Heatmaps
- Line charts
- Before/after comparison
- Status indicators
- Clear labels

The important visual hierarchy is:

```text
DATA
  ↓
CLIENTS
  ↓
FEDERATED LEARNING
  ↓
GLOBAL MODEL
  ↓
TARGET CLIENT
  ↓
UNLEARNING
  ↓
EVALUATION
```

---

# 41. Main Visual Dashboard

The main overview should contain a persistent pipeline:

```text
[DATASET]
    ↓
[PARTITION]
    ↓
[CLIENTS]
    ↓
[FEDERATED LEARNING]
    ↓
[GLOBAL MODEL]
    ↓
[SELECT CLIENT]
    ↓
[GRADIENT ASCENT]
    ↓
[KNOWLEDGE DISTILLATION]
    ↓
[UNLEARNED MODEL]
    ↓
[EVALUATION]
```

The current stage should be highlighted.

Completed stages should show a checkmark.

Running stage should show progress.

Upcoming stages should be muted.

---

# 42. Client Influence Story

The UI should communicate:

```text
Before Unlearning

Global Model
     │
     ├── Client 1 influence
     ├── Client 2 influence
     ├── Client 3 influence  ← TARGET
     ├── Client 4 influence
     └── Client N influence

                 ↓

          UNLEARNING

                 ↓

After Unlearning

Global Model
     │
     ├── Client 1 retained
     ├── Client 2 retained
     ├── Client 3 influence reduced
     ├── Client 4 retained
     └── Client N retained
```

Use measurable metrics to support this visual story.

---

# 43. Error Handling

The dashboard must handle:

### Dataset unavailable

```text
Dataset could not be loaded.

[ Retry ]
```

### Model unavailable

```text
No trained checkpoint exists for this configuration.

Choose:
[ Run Training ]
or
[ Select Another Experiment ]
```

### Client unavailable

```text
Selected client is not available in this experiment.
```

### Unlearning failure

```text
Unlearning failed.

Stage:
Gradient Ascent

Error:
<technical error>

[ Retry ]
[ Return to Experiment ]
```

### Evaluation failure

Do not show incomplete metrics as valid final results.

---

# 44. Experiment Reproducibility

Every experiment should store:

- Dataset
- Dataset version/configuration
- Number of clients
- Partition strategy
- Random seed
- Model architecture
- Federated rounds
- Local epochs
- Unlearning method
- Unlearning hyperparameters
- Target client
- Software/config version
- Result metrics

This allows the professor to reproduce a result.

---

# 45. Configuration Display

Provide a collapsible "Experiment Configuration" panel.

Example:

```text
EXPERIMENT CONFIGURATION

Dataset             CIFAR-100
Clients             10
Partition           Non-IID
Seed                42
Model               ResNet
FL Rounds           20
Local Epochs        1
Unlearning          GA + KD
Target Client       Client 3
```

---

# 46. Research Transparency

The dashboard should distinguish:

### Measured

Actual experiment result.

### Precomputed

Result loaded from stored experiment.

### Live

Currently being calculated.

### Illustrative

Only allowed in documentation/mockups, never presented as an actual experiment result.

This distinction is important for an academic demonstration.

---

# 47. Example Professor Demonstration

A 10-minute demonstration can follow:

## Minute 0–1

Open dashboard.

Select:

```text
Quick Unlearning Demo
CIFAR-100
10 clients
```

## Minute 1–2

Show:

- Dataset
- Client distribution
- Existing federated global model

## Minute 2–3

Select:

```text
Client 3
```

Explain:

> "This is the client whose influence we want to remove."

## Minute 3–6

Click:

**REMOVE INFLUENCE**

Show live:

```text
Gradient Ascent
      ↓
Loss / Accuracy
      ↓
Knowledge Distillation
      ↓
KD Loss
```

## Minute 6–8

Show:

```text
Before vs After
```

Metrics:

- Global accuracy
- Forget accuracy
- Retained accuracy
- MIA

## Minute 8–10

Show:

```text
GA + KD
vs
Full Retraining
```

Explain the runtime difference.

---

# 48. Complete Experiment Demonstration

If the professor wants to see the entire FL process:

```text
Complete Experiment

CIFAR-10
↓
10 Clients
↓
Non-IID Partition
↓
Show Data Distribution
↓
Federated Training
↓
Show FedAvg Rounds
↓
Global Model
↓
Select Client 3
↓
Unlearning
↓
Evaluation
```

Training can use stored checkpoints/replayed metrics if live training is too slow.

---

# 49. Recommended Project Structure

The existing research repository should remain the source of ML logic.

Add dashboard-specific code around it.

Conceptual structure:

```text
federated-unlearning/
│
├── src/
│   ├── federated/
│   │   ├── client.py
│   │   ├── server.py
│   │   └── fedavg.py
│   │
│   ├── unlearning/
│   │   ├── gradient_ascent.py
│   │   ├── knowledge_distillation.py
│   │   └── unlearning_engine.py
│   │
│   ├── evaluation/
│   │   ├── accuracy.py
│   │   ├── mia.py
│   │   └── comparison.py
│   │
│   └── datasets/
│       ├── mnist.py
│       ├── cifar10.py
│       └── cifar100.py
│
├── dashboard/
│   ├── app.py
│   ├── pages/
│   │   ├── overview.py
│   │   ├── setup.py
│   │   ├── distribution.py
│   │   ├── training.py
│   │   ├── client_selection.py
│   │   ├── unlearning.py
│   │   ├── evaluation.py
│   │   ├── comparison.py
│   │   └── history.py
│   │
│   └── components/
│       ├── pipeline.py
│       ├── client_cards.py
│       ├── network.py
│       ├── charts.py
│       ├── metrics.py
│       └── progress.py
│
├── models/
│   ├── mnist/
│   ├── cifar10/
│   └── cifar100/
│
├── artifacts/
│   ├── experiments/
│   ├── training/
│   ├── unlearning/
│   └── evaluation/
│
└── docs/
```

This is a target architecture; adapt names to the existing repository instead of unnecessarily rewriting working research code.

---

# 50. Dashboard-to-Backend Data Flow

The UI should request information rather than directly manipulating model internals.

```text
USER
 │
 ▼
DASHBOARD UI
 │
 ├── Dataset Manager
 │
 ├── Experiment Manager
 │
 ├── Training Manager
 │
 ├── Unlearning Manager
 │
 └── Evaluation Manager
 │
 ▼
EXPERIMENT ARTIFACTS / ML ENGINE
```

---

# 51. Backend Execution Flow

Complete flow:

```text
load_dataset()
      ↓
partition_dataset()
      ↓
create_clients()
      ↓
run/load federated training
      ↓
save global checkpoint
      ↓
select target client
      ↓
load target client data
      ↓
run Gradient Ascent
      ↓
record GA metrics
      ↓
run Knowledge Distillation
      ↓
record KD metrics
      ↓
save unlearned checkpoint
      ↓
evaluate original
      ↓
evaluate unlearned
      ↓
evaluate retrained baseline
      ↓
calculate comparison
      ↓
return results to dashboard
```

---

# 52. Data Required for Visualizations

To make the dashboard truly interactive, the backend should save traces rather than only final values.

For FL:

```json
{
  "round": 1,
  "global_accuracy": 0.42,
  "global_loss": 1.8
}
```

For Gradient Ascent:

```json
{
  "iteration": 1,
  "target_client_loss": 0.42,
  "target_client_accuracy": 0.78
}
```

For KD:

```json
{
  "iteration": 1,
  "kd_loss": 1.24
}
```

For evaluation:

```json
{
  "global_accuracy": 0.57,
  "forget_client_accuracy": 0.31,
  "retained_client_accuracy": 0.59,
  "mia_success": 0.21,
  "runtime_seconds": 84
}
```

These values are schema examples, not actual results.

---

# 53. API-Level Concept

If the dashboard is later separated into frontend/backend:

```text
GET /datasets
GET /experiments
GET /experiments/{id}
GET /experiments/{id}/clients
GET /experiments/{id}/distribution
GET /experiments/{id}/training-metrics
GET /experiments/{id}/models

POST /experiments
POST /experiments/{id}/train
POST /experiments/{id}/unlearn

GET /unlearning/{run_id}/status
GET /unlearning/{run_id}/metrics
GET /unlearning/{run_id}/results

GET /experiments/{id}/comparison
```

If Streamlit is used, equivalent Python function calls are sufficient; a REST API is optional.

---

# 54. Important Research Comparison

The dashboard should visually distinguish three model states:

```text
MODEL A
Original Federated Global Model

MODEL B
Unlearned Model
(GA + KD)

MODEL C
Retrained Model
(Train without target client)
```

Then:

```text
               Original      Unlearned      Retrained

Accuracy          XX%           XX%             XX%
Forget Acc.       XX%           XX%             XX%
Retained Acc.     XX%           XX%             XX%
MIA               XX%           XX%             XX%
Runtime            --           XX sec          XX min
```

This is a strong research result screen.

---

# 55. Unlearning Success Interpretation

Do not define success using one metric alone.

The dashboard should present a balanced interpretation:

```text
FORGETTING
Target-client performance / MIA

UTILITY
Global accuracy / retained-client performance

EFFICIENCY
Unlearning runtime vs retraining
```

The ideal result is:

```text
Target client influence ↓
MIA ↓
Useful global performance ≈ retained
Runtime << full retraining
```

The actual result should determine whether these conditions are achieved.

---

# 56. Dataset-Specific Behavior

The architecture should support dataset-specific:

- Input dimensions
- Number of classes
- Model architecture
- Preprocessing
- Evaluation
- Visualization

For example:

```text
MNIST
→ grayscale image examples

CIFAR-10
→ RGB image examples

CIFAR-100
→ 100-class distribution visualization
```

The dashboard should automatically adapt labels and statistics to the selected dataset.

---

# 57. Optional Client Data Preview

When a client is selected, optionally show sample images:

```text
CLIENT 3 DATA

Sample 1   Sample 2   Sample 3
[ image ]  [ image ]  [ image ]

Classes represented:
...
```

This is especially useful for demonstrating what exactly belongs to the client being forgotten.

---

# 58. Optional Animation

Animations should communicate real system state.

Examples:

### During partitioning

Dataset blocks move into client containers.

### During FL

Global model is broadcast to clients.

Client updates return to server.

FedAvg animation runs.

### During unlearning

Target client is highlighted.

Gradient Ascent progress updates.

KD transitions teacher → student.

### During evaluation

Metrics update after computation.

Animations should not be decorative if they do not represent actual system events.

---

# 59. Accessibility and Readability

The HTML implementation should:

- Work on laptop screens
- Work on projector displays
- Use readable font sizes
- Maintain high contrast
- Avoid tiny charts
- Avoid excessive text
- Use clear labels
- Provide tooltips for technical concepts

A professor should understand the main pipeline from several feet away.

---

# 60. HTML Implementation Requirements

Any cloud/AI coding agent receiving this Markdown should convert the specification into an interactive HTML dashboard.

The resulting HTML should not merely reproduce the Markdown text.

It should create:

- Interactive navigation
- Dataset selector
- Client selector
- Experiment selector
- Pipeline visualization
- Client distribution visualization
- Federated network visualization
- Training charts
- Unlearning progress
- Gradient Ascent chart
- Knowledge Distillation chart
- Evaluation cards
- Before/after comparison
- Retraining comparison

If the actual backend is not connected yet, use a clearly labeled **Demo Data / Simulation Mode**.

Never represent simulated numbers as real research measurements.

---

# 61. Recommended Frontend Sections

The main HTML page should contain:

```text
HEADER
│
├── Project Title
├── Experiment Mode
└── Experiment Status

PIPELINE
│
├── Dataset
├── Partition
├── Clients
├── Federated Learning
├── Global Model
├── Client Selection
├── Unlearning
└── Evaluation

MAIN CONTENT
│
├── Dataset / Experiment Setup
├── Client Distribution
├── FL Visualization
├── Unlearning Visualization
└── Results

FOOTER / STATUS
└── Experiment ID / Model / Runtime / Status
```

---

# 62. Landing Page Copy

Suggested title:

> Federated Unlearning Laboratory

Suggested subtitle:

> Interactive visualization of federated learning, client-level data distribution, and machine unlearning.

Suggested description:

> Train or load a federated global model, select a target client, remove its influence using the unlearning pipeline, and evaluate the resulting model against the original and retrained baselines.

---

# 63. Main Pipeline Labels

Use these exact conceptual labels:

1. Dataset Selection
2. Data Partitioning
3. Client Data Distribution
4. Federated Learning
5. Global Model
6. Target Client
7. Gradient Ascent
8. Knowledge Distillation
9. Unlearned Model
10. Evaluation
11. Retraining Comparison

---

# 64. Minimum Viable Dashboard

If development time is limited, implement in this order:

### Priority 1

```text
Dataset
↓
Model
↓
Client Selection
↓
Remove Influence
↓
GA + KD
↓
Before/After Results
```

### Priority 2

```text
Data Distribution
↓
Federated Learning Visualization
```

### Priority 3

```text
MIA
↓
Retraining Comparison
↓
History
```

But the final architecture should support all stages from the beginning.

---

# 65. Final Desired User Experience

A user should be able to open the dashboard and do this:

```text
1. Select CIFAR-100

2. Select 10 clients

3. See:
   "Dataset → 10 Clients"

4. Open Data Distribution

5. See how CIFAR-100 is distributed

6. Open Federated Learning

7. See:
   Client 1 ─┐
   Client 2 ─┤
   Client 3 ─┤ → FedAvg → Global Model
   ...       │
   Client 10─┘

8. See global accuracy/loss

9. Select Client 3

10. Click:
    REMOVE INFLUENCE

11. See:
    Gradient Ascent running

12. See:
    Target client metrics changing

13. See:
    Knowledge Distillation running

14. See:
    KD loss changing

15. See:
    Unlearned model created

16. See:
    Accuracy comparison

17. See:
    Forget-client comparison

18. See:
    MIA comparison

19. See:
    Runtime comparison

20. Compare:
    GA + KD vs Full Retraining
```

---

# 66. Final Architecture Summary

The entire system is:

```text
                         ┌──────────────────────┐
                         │    DATASET LIBRARY   │
                         │                      │
                         │ MNIST                │
                         │ CIFAR-10             │
                         │ CIFAR-100            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ DATA PARTITIONING    │
                         │                      │
                         │ 5 / 10 / 20 clients  │
                         │ IID / Non-IID        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       CLIENT DATASETS        │
                    │                              │
                    │ C1  C2  C3 ... C10           │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     FEDERATED LEARNING       │
                    │                              │
                    │ Local Training               │
                    │       ↓                      │
                    │ Client Updates               │
                    │       ↓                      │
                    │ FedAvg                       │
                    │       ↓                      │
                    │ Global Model                 │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       GLOBAL MODEL           │
                    │                              │
                    │ Accuracy                     │
                    │ Loss                         │
                    │ Checkpoint                   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      TARGET CLIENT           │
                    │                              │
                    │ Select C1 / C2 / ... / C10  │
                    └──────────────┬───────────────┘
                                   │
                         REMOVE INFLUENCE
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       UNLEARNING             │
                    │                              │
                    │ Gradient Ascent              │
                    │       ↓                      │
                    │ Knowledge Distillation       │
                    │       ↓                      │
                    │ Unlearned Model              │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │         EVALUATION           │
                    │                              │
                    │ Global Accuracy              │
                    │ Forget Accuracy              │
                    │ Retained Accuracy             │
                    │ MIA                          │
                    │ Runtime                      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       COMPARISON             │
                    │                              │
                    │ Original Model               │
                    │ Unlearned Model              │
                    │ Retrained Model              │
                    └──────────────────────────────┘
```

---

# 67. Two Complete Entry Points

The final dashboard must support both:

```text
                    FEDERATED UNLEARNING LAB
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
        COMPLETE EXPERIMENT          QUICK DEMO
                 │                         │
                 ▼                         ▼
             Dataset                 Model Library
                 │                         │
                 ▼                         ▼
            Partition                 Select Model
                 │                         │
                 ▼                         ▼
        Data Distribution            Select Client
                 │                         │
                 ▼                         ▼
        Federated Learning          Gradient Ascent
                 │                         │
                 ▼                         ▼
          Global Model             Knowledge Distillation
                 │                         │
                 ▼                         ▼
        Select Client                  Evaluation
                 │                         │
                 ▼                         ▼
             Unlearn                  Final Result
                 │
                 ▼
            Evaluation
```

This dual-flow architecture is the central design decision.

---

# 68. Final Implementation Principle

The dashboard is not intended to replace the federated-learning/unlearning research code.

It is a **visual control and demonstration layer over the existing research pipeline**.

The existing ML implementation remains responsible for:

- Dataset loading
- Client creation
- Federated training
- FedAvg
- Gradient Ascent
- Knowledge Distillation
- Evaluation
- MIA
- Retraining baseline

The dashboard is responsible for:

- Configuration
- Experiment selection
- Visualization
- Execution control
- Progress display
- Metric display
- Model selection
- Client selection
- Result comparison
- Research storytelling

The final system should make the following sentence visually obvious:

> **A dataset is distributed among multiple federated clients, a global model is learned without centralizing client data, a specific client's influence can then be targeted for removal, Gradient Ascent and Knowledge Distillation produce an unlearned model, and the resulting forgetting, retained utility, privacy behavior, and computational cost are evaluated against the original and retrained models.**

---

# 69. Important Source-of-Truth Rule

All implementation details must ultimately be connected to the actual `federated-unlearning` repository.

If an existing function already performs:

- FedAvg
- Gradient Ascent
- Knowledge Distillation
- MIA
- Evaluation

the dashboard should call or wrap that implementation instead of creating a second independent implementation.

The dashboard specification defines the **desired user experience and architecture**.

It does not authorize replacing existing research algorithms with fake/demo implementations.

---

# 70. Final Acceptance Checklist

The HTML/dashboard implementation is considered complete only when:

## Dataset

- [ ] MNIST selectable
- [ ] CIFAR-10 selectable
- [ ] CIFAR-100 selectable

## Experiment Setup

- [ ] Number of clients selectable
- [ ] Partition strategy selectable
- [ ] Model selectable
- [ ] Federated rounds configurable
- [ ] Existing experiments loadable

## Data Distribution

- [ ] Dataset partitioning visible
- [ ] Client list visible
- [ ] Samples/client visible
- [ ] Class distribution visible
- [ ] IID/Non-IID visible
- [ ] Heatmap available

## Federated Learning

- [ ] Server visible
- [ ] Clients visible
- [ ] Local training visible
- [ ] Model updates visible
- [ ] FedAvg visible
- [ ] Round progression visible
- [ ] Accuracy chart visible
- [ ] Loss chart visible
- [ ] Global checkpoint visible

## Client Selection

- [ ] All clients selectable
- [ ] Target client highlighted
- [ ] Client data information shown
- [ ] Remove Influence button available

## Unlearning

- [ ] Original model shown
- [ ] Gradient Ascent shown
- [ ] GA progress shown
- [ ] GA metrics shown
- [ ] Knowledge Distillation shown
- [ ] KD progress shown
- [ ] KD loss shown
- [ ] Unlearned model shown

## Evaluation

- [ ] Global accuracy
- [ ] Forget-client accuracy
- [ ] Retained-client accuracy
- [ ] MIA
- [ ] Runtime
- [ ] Before/after comparison

## Research Comparison

- [ ] Original model
- [ ] Unlearned model
- [ ] Retrained model
- [ ] Accuracy comparison
- [ ] Forgetting comparison
- [ ] MIA comparison
- [ ] Runtime comparison

## Demo

- [ ] Quick Unlearning mode
- [ ] Complete Experiment mode
- [ ] Precomputed model support
- [ ] Precomputed training replay
- [ ] Live unlearning support where practical
- [ ] No fabricated results
- [ ] Clear live/precomputed labels

## Presentation

- [ ] Clean academic design
- [ ] Clear pipeline
- [ ] Readable charts
- [ ] Projector-friendly
- [ ] Interactive
- [ ] Easy to understand without source code

# 71. COMPUTE BACKEND AND FALLBACK ARCHITECTURE

## 71.1 Purpose

The dashboard must not depend on a single GPU machine. The same federated-learning and unlearning pipeline should be executable through multiple compute backends.

The dashboard must support:

1. **College GPU — Primary live backend**
2. **Google Colab GPU — Backup live/temporary backend**
3. **Local Mac — CPU/MPS fallback for small experiments**
4. **Precomputed Demo — Guaranteed presentation fallback**

The frontend must present these as compute options while keeping the ML implementation itself shared.

## 71.2 Compute Backend Selector

Add a visible control to the dashboard:

```text
COMPUTE BACKEND

● Auto
○ College GPU
○ Google Colab
○ Local Mac
○ Demo / Precomputed
```

The selected backend must be shown clearly throughout an experiment.

Example:

```text
Backend: College GPU
Status: Connected
Accelerator: NVIDIA CUDA
```

or:

```text
Backend: Demo / Precomputed
Status: Using stored experiment artifacts
```

Never present precomputed or simulated results as live GPU computation.

## 71.3 Auto Backend Selection

`Auto` is the recommended default.

The backend-selection logic should follow:

```text
                  AUTO
                    │
                    ▼
          Is College GPU reachable?
              │              │
             YES             NO
              │              │
              ▼              ▼
        College GPU     Is Colab available?
                             │          │
                            YES         NO
                             │          │
                             ▼          ▼
                       Google Colab   Local Mac
                                      MPS/CPU
                                         │
                                         ▼
                                  Precomputed Demo
```

The exact implementation may differ depending on the deployment environment, but the user experience must follow this principle.

## 71.4 College GPU Backend

The college GPU is the preferred backend for genuine live computation.

Expected architecture:

```text
Dashboard
    │
    │ REST/WebSocket API
    ▼
College GPU Server
    │
    ├── FastAPI / Backend
    ├── Python
    ├── PyTorch
    ├── CUDA
    └── NVIDIA GPU
            │
            ▼
    Federated Unlearning Engine
```

SSH access may be used for administration/deployment. SSH credentials must never be embedded in frontend code.

The dashboard should expose a health/status endpoint conceptually equivalent to:

```text
GET /health
```

and a compute capability/status response containing information such as:

```json
{
  "backend": "college_gpu",
  "status": "connected",
  "accelerator": "cuda",
  "gpu_name": "...",
  "cuda_available": true
}
```

Do not hard-code a specific GPU model unless it is actually detected.

## 71.5 Google Colab Backend

Google Colab is a backup GPU environment, not a guaranteed permanent production server.

The architecture should allow the same backend code to run in a Colab GPU runtime:

```text
Google Colab
    │
    ├── Repository checkout
    ├── Python environment
    ├── PyTorch
    └── CUDA GPU
            │
            ▼
    Federated Unlearning Engine
```

The implementation must account for the fact that Colab runtimes can disconnect, reset, or become unavailable.

Therefore:

- Do not make the dashboard permanently dependent on a Colab session.
- Do not assume a stable public URL.
- Do not store critical experiment artifacts only inside an ephemeral Colab runtime.
- Provide a clear `Colab Connected` / `Colab Unavailable` state.
- Use Colab primarily for temporary live computation, testing, or backup demonstration.
- Store important trained models and experiment artifacts outside the temporary runtime when possible.

If a Colab API/tunnel approach is used, the dashboard must treat the connection as temporary and recoverable.

## 71.6 Local Mac Backend

The local Mac backend is the fallback when remote GPU access is unavailable.

The implementation should detect the available PyTorch device:

```python
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
```

The local backend must not assume NVIDIA CUDA on a Mac.

For demonstration purposes, local execution should favor small or lightweight configurations such as:

```text
Dataset: MNIST
Clients: 3–5
Training: pretrained/checkpointed
Unlearning: lightweight live run
```

The dashboard must clearly display:

```text
Backend: Local Mac
Accelerator: MPS
```

or:

```text
Backend: Local Mac
Accelerator: CPU
```

when applicable.

## 71.7 Demo / Precomputed Backend

This is the guaranteed presentation fallback.

It must load previously generated artifacts rather than requiring live training.

Example:

```text
experiments/
├── mnist/
├── cifar10/
└── cifar100/
```

Each experiment may contain:

```text
global_model
partition information
FL round metrics
client metrics
unlearning metrics
Gradient Ascent history
Knowledge Distillation history
MIA results
runtime measurements
comparison with retraining
```

The dashboard should display:

```text
Backend: Demo / Precomputed
Mode: Stored Experiment
```

This mode must preserve the complete research story:

```text
Dataset
   ↓
Partitioning
   ↓
Client Distribution
   ↓
Federated Learning
   ↓
Trained Global Model
   ↓
Target Client
   ↓
Gradient Ascent
   ↓
Knowledge Distillation
   ↓
Unlearned Model
   ↓
Evaluation
   ↓
MIA
   ↓
Retraining Comparison
```

If the numbers are from stored experiments, label them as stored/precomputed results.

## 71.8 Backend Abstraction

The frontend must not contain backend-specific ML logic.

Use a common conceptual interface:

```text
ComputeBackend
├── CollegeGPUBackend
├── ColabBackend
├── LocalBackend
└── DemoBackend
```

Each backend should expose equivalent high-level operations, for example:

```text
get_status()
load_experiment()
get_client_distribution()
get_fl_history()
start_unlearning(client_id)
get_unlearning_status()
get_results()
```

The actual function names may be adapted to the existing repository.

The critical requirement is that the dashboard can switch compute backends without changing the visualization layer.

## 71.9 Live Unlearning Request

A user action such as:

```text
Client 3
[ Remove Influence ]
```

must be translated into a backend-neutral request:

```json
{
  "experiment": "cifar10_10clients",
  "client_id": 3
}
```

The Compute Manager routes the request to the selected backend.

Example:

```text
Dashboard
    │
    ▼
Compute Manager
    │
    ▼
Selected Backend
    │
    ▼
Federated Unlearning Engine
    │
    ├── Gradient Ascent
    ├── Knowledge Distillation
    └── Evaluation
    │
    ▼
Structured Results
    │
    ▼
Dashboard
```

## 71.10 Backend Status Panel

Add a compact status panel:

```text
COMPUTE STATUS

College GPU     ● Connected
Google Colab    ○ Disconnected
Local Mac       ● Available
Demo Data       ● Available
```

The status must be factual and dynamically determined.

Possible states:

```text
● Connected
● Available
○ Disconnected
⚠ Busy
⚠ Starting
✕ Unavailable
```

## 71.11 Failure and Automatic Fallback

If a live backend fails during an experiment:

```text
College GPU
     ↓
Connection failed
     ↓
Show clear error
     ↓
Offer fallback
     ↓
Colab / Local / Demo
```

Do not silently switch to fake data.

If automatic fallback is enabled, display:

```text
College GPU unavailable.
Switched to Demo / Precomputed mode.
```

The user must always know which backend produced the displayed results.

## 71.12 Presentation-Safe Design

The dashboard is intended for a short professor demonstration of approximately 10–15 minutes.

Therefore the system must optimize for reliability rather than requiring every computation to happen live.

Recommended presentation sequence:

```text
1. Select Dataset
2. Select Number of Clients
3. Show Client Data Distribution
4. Show Federated Learning / trained model
5. Select Target Client
6. Click Remove Influence
7. Run live unlearning on College GPU if available
8. Show Gradient Ascent
9. Show Knowledge Distillation
10. Show final evaluation + MIA
11. Compare Original vs Unlearned vs Retrained
```

If the GPU is unavailable:

```text
Use Colab
      ↓
If unavailable:
Use Local Mac for a small experiment
      ↓
If unsuitable:
Use Demo / Precomputed artifacts
```

The presentation must remain functional even when no remote GPU is reachable.

## 71.13 No Fake Live Indicators

Never show:

```text
GPU Running...
Gradient Ascent: 72%
```

unless an actual computation or explicitly labeled visualization is running.

For precomputed data, use:

```text
Stored Experiment
Replay Mode
Precomputed Result
```

For a visual replay of an already completed experiment, use:

```text
Experiment Replay
```

rather than claiming the computation is currently executing.

## 71.14 Environment Information

The dashboard should optionally show:

```text
Dataset
Clients
Model
Backend
Device
GPU
CUDA/MPS
Experiment ID
```

Example:

```text
Experiment
CIFAR-10 / 10 Clients

Backend
College GPU

Device
CUDA

Model
Federated Global Model

Mode
Live Unlearning
```

For a stored run:

```text
Backend
Demo / Precomputed

Mode
Stored Experiment Replay
```

## 71.15 Shared Artifact Strategy

The compute backend should save experiment outputs in a backend-independent format.

Prefer structured files such as:

```text
JSON
CSV
PyTorch checkpoints
NumPy arrays
```

where appropriate.

The dashboard should consume the same result schema regardless of whether the experiment was generated by:

```text
College GPU
Google Colab
Local Mac
```

This makes experiments reproducible and prevents the frontend from becoming coupled to one machine.

## 71.16 Recommended Backend Priority

Final priority:

```text
PRIMARY
College GPU
     │
     ▼
BACKUP
Google Colab GPU
     │
     ▼
LOCAL FALLBACK
Mac MPS / CPU
     │
     ▼
GUARANTEED PRESENTATION FALLBACK
Demo / Precomputed
```

This priority must be reflected in `Auto` mode.

## 71.17 Security Requirements

Never place any of the following in frontend HTML/JavaScript:

```text
SSH password
SSH private key
College GPU credentials
API secrets
Cloud credentials
```

All credentials must remain server-side or in secure environment configuration.

The dashboard should communicate with a controlled backend API rather than directly exposing the college server's SSH credentials.

## 71.18 Acceptance Criteria for Compute Architecture

The implementation is complete when:

- [ ] Dashboard has a Compute Backend selector.
- [ ] `Auto` is available.
- [ ] College GPU can be configured as the primary live backend.
- [ ] Google Colab can be used as a temporary GPU backend.
- [ ] Local Mac MPS/CPU execution is supported for lightweight experiments.
- [ ] Demo/Precomputed mode is always available.
- [ ] Backend status is visible.
- [ ] The active backend is visible during unlearning.
- [ ] Backend failures produce clear messages.
- [ ] Fallback does not silently fabricate results.
- [ ] Stored experiments are clearly labeled.
- [ ] The same dashboard visualization works with all backend types.
- [ ] Credentials are never exposed to the frontend.
- [ ] The professor demonstration can continue even when the college GPU is unavailable.
