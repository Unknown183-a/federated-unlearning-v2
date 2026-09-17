# Phase 05 — Federated Learning Engine

> Status: **Complete**
> Implementation: `core/federated/model.py` (dataset-agnostic small CNN), `client.py` (local training step), `fedavg.py` (sample-weighted aggregation), `server.py` (round loop + evaluation + `get_fl_history()`), `storage.py` and `cli.py` (mirroring Phase 03's pattern). Exposed via `POST/GET /api/training` in the Express backend.

## Goal

Implement the actual client/server FedAvg loop: local training per client, aggregation on the server, repeated over rounds.

## In Scope

- Local training step (per client, per round)
- FedAvg aggregation
- Round loop with configurable round count and local epochs
- Persisted per-round metrics (accuracy, loss) and per-client update logs

## Out of Scope

- Any UI (Phase 06)
- Unlearning

## Tasks

- [x] Implement local client training step
- [x] Implement FedAvg aggregation
- [x] Implement the round loop, driven by experiment config
- [x] Persist round-by-round global accuracy/loss and per-client completion
- [x] Expose get_fl_history() from the backend

## Deliverables

- Working FedAvg training loop, runnable end to end on MNIST

## Depends On

Phase 04 (client distribution)

## Acceptance Criteria

- A full training run on MNIST with 5 clients converges to a reasonable accuracy
- get_fl_history() returns a complete, well-formed round-by-round history

## Progress Log

| Date | Update |
|------|--------|
| — | Phase not started |
| — | FedAvg engine implemented; verified end to end on real MNIST -- 5 IID clients went from 53% to 98.9% accuracy over 6 rounds, and Non-IID (Dirichlet) clients converged to 98.7% over 3 rounds without errors. `/api/training` route tested live against a real partition. |

---
Previous: [Phase 04 — Client Data Distribution View](../phase-04-client-distribution-view/README.md)
Next: [Phase 06 — Federated Learning Visualization & Metrics](../phase-06-fl-visualization/README.md)
