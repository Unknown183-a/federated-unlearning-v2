# Phase 02 — Experiment Configuration

> Status: **Complete**
> Implementation: shared experiment state, config form, and wired dataset picker are live on main.

## Goal

Let a user configure a full experiment — client count, partition strategy, rounds, model, seed — with no assumption ever fixed at a specific client count.

## In Scope

- Configuration form UI (page 2, part 2)
- Config validation (client count, rounds, epochs, seed)
- Config persisted into the central experiment state (Ch.15's state model)

## Out of Scope

- Partitioning logic itself
- Training logic itself

## Tasks

- [x] Build the Experiment Configuration form (dataset, clients, partition strategy, rounds, local epochs, model, seed, training mode)
- [x] Add client-count as a free numeric input, not a fixed set of options
- [x] Add form validation and sane defaults
- [x] Wire config into the global experiment state store

## Deliverables

- Working configuration screen
- Config object available to all later phases via shared state

## Depends On

Phase 01 (dataset layer)

## Acceptance Criteria

- 5, 10, and 20 clients can all be configured without code changes
- Config is retained when navigating between pages

## Progress Log

| Date | Update |
|------|--------|
| 2026-09-15 | Added ExperimentContext (shared state), ExperimentConfigForm, wired dataset picker into shared config |

---
Previous: [Phase 01 — Dataset Layer](../phase-01-dataset-layer/README.md)
Next: [Phase 03 — Data Partitioning Engine](../phase-03-data-partitioning/README.md)
