# Final Acceptance Checklist (Spec Chapter 70) — how to verify each item

The spec says the dashboard is complete only when every item in Chapter 70 is
true. This file says **how to check each one** and which parts a program can
check for you.

- **Auto** = `python -m core.acceptance.cli --experiment-id <id>` (or `--all`)
  checks the stored files behind that screen. The check name is in brackets.
  It reads JSON only, so it needs no GPU, no torch and no network.
- **Look** = you open the page and look. A program cannot judge it.
- The last column is for **you**. Nothing is pre-ticked: tick an item only
  after you have checked it on your own machine.

## How to run the acceptance pass

1. Run the full pipeline once per dataset (MNIST, CIFAR-10, CIFAR-100): Setup,
   Data Distribution, Federated Learning, Client Selection, Unlearning,
   Evaluation, Retraining Comparison.
2. Run `python -m core.acceptance.cli --all`. Every experiment must show `0 failed`.
3. Work down the tables below in Research Mode, then repeat the Demo section in
   Professor Demo Mode with the network off.
4. Record the results in the table at the bottom.

## Dataset

| Item | How | Done |
|------|-----|------|
| MNIST selectable | Look: Setup page | [ ] |
| CIFAR-10 selectable | Look: Setup page | [ ] |
| CIFAR-100 selectable | Look: Setup page | [ ] |

## Experiment Setup

| Item | How | Done |
|------|-----|------|
| Number of clients selectable | Look: Setup page (free numeric input) | [ ] |
| Partition strategy selectable | Look: IID / Non-IID | [ ] |
| Model selectable | Look: CNN / ResNet | [ ] |
| Federated rounds configurable | Look | [ ] |
| Existing experiments loadable | Look: Overview "Quick Demo" and Experiment History "Open" | [ ] |

## Data Distribution

| Item | How | Done |
|------|-----|------|
| Dataset partitioning visible | Auto [`partition_covers_dataset`] + Look | [ ] |
| Client list visible | Auto [`client_list`] + Look | [ ] |
| Samples/client visible | Auto [`samples_per_client`] + Look | [ ] |
| Class distribution visible | Auto [`samples_per_client`] + Look | [ ] |
| IID/Non-IID visible | Auto [`iid_flag`] + Look | [ ] |
| Heatmap available | Look | [ ] |

## Federated Learning

| Item | How | Done |
|------|-----|------|
| Server, clients, local training, model updates, FedAvg visible | Look: the animated diagram | [ ] |
| Round progression visible | Auto [`round_count`] + Look | [ ] |
| Accuracy chart and loss chart visible | Auto [`charts_data`] + Look | [ ] |
| Global checkpoint visible | Auto [`global_checkpoint`] + Look | [ ] |

## Client Selection

| Item | How | Done |
|------|-----|------|
| All clients selectable | Look | [ ] |
| Target client highlighted | Auto [`target_valid`] + Look | [ ] |
| Client data information shown | Look | [ ] |
| Remove Influence button available | Look: appears after you pick a client | [ ] |

## Unlearning

| Item | How | Done |
|------|-----|------|
| Original model shown | Look | [ ] |
| Gradient Ascent + progress + metrics shown | Auto [`ga_progress`] + Look | [ ] |
| Knowledge Distillation + progress + loss shown | Auto [`kd_progress`] + Look | [ ] |
| Unlearned model shown | Auto [`unlearned_model`] + Look | [ ] |

## Evaluation

| Item | How | Done |
|------|-----|------|
| Global, forget-client, retained-client accuracy and MIA | Auto [`before_metrics`, `after_metrics`] + Look | [ ] |
| Runtime | Auto [`runtime_measured`] + Look | [ ] |
| Before/after comparison | Auto [`results_complete`] + Look | [ ] |

## Research Comparison

| Item | How | Done |
|------|-----|------|
| Original, unlearned and retrained models | Auto [`baseline_complete`] + Look | [ ] |
| Accuracy, forgetting and MIA comparison | Auto [`retrained_metrics`] + Look | [ ] |
| Runtime comparison | Auto [`retraining_runtime`] + Look | [ ] |
| Retrained model really excluded the target, same protocol | Auto [`target_excluded`, `same_protocol`, `baseline_matches_target`] | [ ] |

## Demo

| Item | How | Done |
|------|-----|------|
| Quick Unlearning mode, Complete Experiment mode | Look: Overview | [ ] |
| Precomputed model support, precomputed training replay | Look: Federated Learning page in Demo Mode replays a stored run | [ ] |
| Live unlearning support where practical | Look: Research Mode with Local or GPU backend | [ ] |
| No fabricated results | Auto [every check above]; unfinished results are refused by the API (409) and the page | [ ] |
| Clear live/precomputed labels | Look: every result page has a badge; Overview has a legend | [ ] |
| Whole story replays with no live backend | Stop remote backends, set `PYTHON_BIN` to a missing path, open Professor Demo. Pages still load. | [ ] |
| Reproducibility: seed + config on every result screen | Auto [`core_config`, `unlearning_hyperparameters`] + Look: "Experiment Configuration & Seed" panel | [ ] |

## Presentation

All six items are **Look** items (clean design, clear pipeline, readable charts,
projector-friendly, interactive, understandable without source code). Check
them on the projector you will actually use.

| Item | Done |
|------|------|
| Clean academic design | [ ] |
| Clear pipeline | [ ] |
| Readable charts | [ ] |
| Projector-friendly | [ ] |
| Interactive | [ ] |
| Easy to understand without source code | [ ] |

## Result record (fill in)

| Dataset | Experiment id | `core.acceptance.cli` result | Demo Mode replay with network off | Date |
|---------|---------------|------------------------------|-----------------------------------|------|
| MNIST | | | | |
| CIFAR-10 | | | | |
| CIFAR-100 | | | | |

A warning from the checker (for example "unlearning hyperparameters not
recorded") is not a failure. It means the run was made before Phase 15 saved
those settings. Re-run unlearning to record them.
