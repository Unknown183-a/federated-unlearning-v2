"""FedAvg aggregation algorithm (Phase 05).

Combines each client's updated model weights into one new global
model, weighted by how many samples each client trained on -- the
standard FedAvg rule (McMahan et al., 2017):

    w_global = sum_k (n_k / n_total) * w_k

Kept independent of `client.py`/`server.py` so it can be unit tested
against plain state dicts without spinning up any real training.
"""
from __future__ import annotations

import copy

import torch


def federated_average(state_dicts: list[dict], num_samples: list[int]) -> dict:
    """Weighted-average a list of model state dicts.

    `state_dicts[i]` was trained on `num_samples[i]` samples. Every
    state dict must have the same keys/shapes (they're all copies of
    the same architecture).
    """
    if not state_dicts:
        raise ValueError("federated_average requires at least one state dict")
    if len(state_dicts) != len(num_samples):
        raise ValueError("state_dicts and num_samples must be the same length")

    total_samples = sum(num_samples)
    if total_samples <= 0:
        raise ValueError("num_samples must sum to a positive number")

    keys = state_dicts[0].keys()
    averaged = copy.deepcopy(state_dicts[0])
    for key in keys:
        weighted_sum = torch.zeros_like(state_dicts[0][key], dtype=torch.float32)
        for state, n in zip(state_dicts, num_samples):
            weighted_sum += state[key].to(torch.float32) * (n / total_samples)
        averaged[key] = weighted_sum.to(state_dicts[0][key].dtype)

    return averaged
