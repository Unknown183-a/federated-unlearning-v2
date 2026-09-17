# Phase 03 — Data Partitioning Engine

> Status: **Complete**
> Implementation: IID/Non-IID partitioning engine, persistence, and the partitioning summary screen are live on main.

## Goal

Split a dataset into N client-owned shards according to the chosen strategy, with a fixed random seed for reproducibility.

## In Scope

- Partitioning engine (IID and Non-IID strategies)
- Per-client sample/class bookkeeping
- Partitioning summary API + screen (page 3, part 1)

## Out of Scope

- Client distribution heatmap/cards (Phase 04)
- Training

## Tasks

- [x] Implement IID partitioning strategy
- [x] Implement Non-IID partitioning strategy (e.g. Dirichlet or shard-based)
- [x] Persist partition metadata: samples/client, classes/client, seed, method
- [x] Expose get_client_distribution() from the backend
- [x] Build the partitioning summary screen

## Deliverables

- Working partitioner for both strategies
- Partition summary screen

## Depends On

Phase 02 (experiment configuration)

## Acceptance Criteria

- Same seed + same config reproduces an identical partition
- Partition works correctly for 5, 10, and 20 clients

## Progress Log

| Date | Update |
|------|--------|
| 2026-09-15 | Added `core/partitioning` (IID uniform-random + Non-IID Dirichlet-skewed engine, `get_client_distribution()`, JSON persistence to `experiments/<id>/partition.json`, CLI entrypoint), `pytest` coverage for reproducibility/5-10-20-client acceptance criteria, `POST /api/partition` + `GET /api/partition/:experimentId` on the backend, and the Partition Summary screen on the Data Distribution page. |

---
Previous: [Phase 02 — Experiment Configuration](../phase-02-experiment-configuration/README.md)
Next: [Phase 04 — Client Data Distribution View](../phase-04-client-distribution-view/README.md)
