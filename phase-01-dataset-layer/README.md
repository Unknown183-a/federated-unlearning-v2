# Phase 01 — Dataset Layer

> Status: **Complete**
> Implementation: dataset manifest, loaders, /api/datasets, and the dataset picker screen are live on main.

## Goal

Load and describe MNIST, CIFAR-10, and CIFAR-100 in a way that is extensible to future datasets without touching downstream code.

## In Scope

- Dataset loader interface (get_metadata, get_train, get_test)
- MNIST, CIFAR-10, CIFAR-100 implementations
- Dataset card UI component (name, dims, channels, class count)
- Dataset selection screen (page 2, part 1)

## Out of Scope

- Partitioning
- Training
- Any UI beyond the dataset picker

## Tasks

- [x] Define a Dataset interface all datasets implement
- [x] Implement MNIST loader + metadata
- [x] Implement CIFAR-10 loader + metadata
- [x] Implement CIFAR-100 loader + metadata
- [x] Build the Dataset Card component and the dataset picker screen
- [x] Wire get_status()/dataset metadata into the backend API

## Deliverables

- 3 working dataset loaders
- Dataset picker screen showing all 3 cards

## Depends On

Phase 00 (project skeleton)

## Acceptance Criteria

- Selecting a dataset in the UI returns correct metadata from the backend
- Adding a 4th dataset later requires no changes outside the dataset layer (documented + spot-checked)

## Progress Log

| Date | Update |
|------|--------|
| 2026-09-15 | Added manifest.json, Dataset interface + MNIST/CIFAR-10/CIFAR-100 loaders, /api/datasets route, DatasetCard + picker screen |

---
Previous: [Phase 00 — Project Setup & Architecture Foundation](../phase-00-project-setup/README.md)
Next: [Phase 02 — Experiment Configuration](../phase-02-experiment-configuration/README.md)
