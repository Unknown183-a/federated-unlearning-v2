"""Data partitioning engine (Dashboard Spec Ch.6, Phase 03).

Splits a dataset's training samples across N simulated federated
clients, either IID (uniform random) or Non-IID (label-skewed via a
Dirichlet distribution over each class), with a fixed seed for
reproducibility.

Real per-sample labels aren't loaded here -- that needs torch/
torchvision plus a download, the same heavy-dependency tradeoff
Phase 01 avoided for get_metadata(). Instead each dataset's labels
are treated as a deterministic, perfectly balanced round-robin over
its class count from manifest.json, which is a close approximation
for MNIST/CIFAR-10/CIFAR-100 (all near-perfectly balanced). Only the
*assignment* of samples to clients is randomized and seeded -- that
assignment is what the partitioning stage and its acceptance criteria
actually care about.
"""
from __future__ import annotations

import numpy as np

from core.datasets.base import load_manifest

#: Dirichlet concentration for Non-IID partitioning. Lower = more skewed
#: per-client label distribution; 0.5 gives a clearly visible skew while
#: still leaving every client with samples from most classes.
DEFAULT_DIRICHLET_ALPHA = 0.5


def _class_labels(num_train: int, num_classes: int) -> np.ndarray:
    """A deterministic, balanced label array standing in for the real one."""
    return np.arange(num_train) % num_classes


def _partition_iid(labels: np.ndarray, num_clients: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(labels))
    return list(np.array_split(indices, num_clients))


def _partition_non_iid(
    labels: np.ndarray,
    num_clients: int,
    seed: int,
    alpha: float = DEFAULT_DIRICHLET_ALPHA,
) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    num_classes = int(labels.max()) + 1
    client_indices: list[list[int]] = [[] for _ in range(num_clients)]

    for c in range(num_classes):
        class_idx = np.where(labels == c)[0]
        rng.shuffle(class_idx)
        proportions = rng.dirichlet(alpha * np.ones(num_clients))
        # Proportions -> integer cut points over this class's samples.
        cuts = (np.cumsum(proportions) * len(class_idx)).astype(int)[:-1]
        for client_id, shard in enumerate(np.split(class_idx, cuts)):
            client_indices[client_id].extend(shard.tolist())

    return [np.array(sorted(idx)) for idx in client_indices]


def partition_dataset(
    dataset: str,
    num_clients: int,
    strategy: str,
    seed: int,
    alpha: float = DEFAULT_DIRICHLET_ALPHA,
) -> dict:
    """Partition `dataset`'s training samples across `num_clients` clients.

    Mirrors the conceptual ``partition_dataset(dataset, num_clients,
    strategy, seed)`` interface from the Dashboard Spec, Ch.36.

    Returns a dict with per-client sample indices and class counts.
    Every sample is assigned to exactly one client.
    """
    if not isinstance(num_clients, int) or num_clients < 2:
        raise ValueError("num_clients must be an integer >= 2")
    if strategy not in ("iid", "non_iid"):
        raise ValueError(f"Unknown partition strategy '{strategy}' (expected 'iid' or 'non_iid')")

    manifest = load_manifest()
    if dataset not in manifest:
        raise KeyError(f"Unknown dataset id '{dataset}'")
    meta = manifest[dataset]
    num_train = meta["num_train"]
    num_classes = meta["num_classes"]

    labels = _class_labels(num_train, num_classes)
    if strategy == "iid":
        shards = _partition_iid(labels, num_clients, seed)
    else:
        shards = _partition_non_iid(labels, num_clients, seed, alpha)

    clients = []
    for client_id, indices in enumerate(shards):
        class_counts: dict[int, int] = {}
        if len(indices):
            classes, counts = np.unique(labels[indices], return_counts=True)
            class_counts = {int(c): int(n) for c, n in zip(classes, counts)}
        clients.append(
            {
                "client_id": client_id,
                "indices": indices.tolist(),
                "num_samples": int(len(indices)),
                "class_counts": class_counts,
            }
        )

    return {
        "dataset": dataset,
        "num_clients": num_clients,
        "strategy": strategy,
        "seed": seed,
        "alpha": alpha if strategy == "non_iid" else None,
        "num_classes": num_classes,
        "total_samples": num_train,
        "clients": clients,
    }


def get_client_distribution(partition: dict, client_id: int) -> dict:
    """Look up one client's distribution from an already-computed partition.

    Mirrors ``get_client_distribution(experiment_id, client_id)`` from
    Ch.36 -- callers that only have an experiment_id should load the
    partition via ``core.partitioning.storage.load_partition()`` first
    and pass the result in here.
    """
    clients = partition["clients"]
    if not (0 <= client_id < len(clients)):
        raise KeyError(f"No client {client_id} in this partition (num_clients={partition['num_clients']})")
    client = clients[client_id]

    dominant = sorted(client["class_counts"].items(), key=lambda kv: -kv[1])[:3]
    return {
        "client_id": client["client_id"],
        "num_samples": client["num_samples"],
        "num_classes_present": len(client["class_counts"]),
        "dominant_classes": [c for c, _ in dominant],
        "class_counts": client["class_counts"],
    }


def summarize_partition(partition: dict) -> dict:
    """Strip per-sample indices for a lightweight API/UI payload."""
    samples = [c["num_samples"] for c in partition["clients"]]
    avg = sum(samples) / len(samples) if samples else 0
    most_imbalanced = max(
        partition["clients"],
        key=lambda c: abs(c["num_samples"] - avg),
        default=None,
    )
    return {
        "dataset": partition["dataset"],
        "num_clients": partition["num_clients"],
        "strategy": partition["strategy"],
        "seed": partition["seed"],
        "alpha": partition["alpha"],
        "num_classes": partition["num_classes"],
        "total_samples": partition["total_samples"],
        "average_samples_per_client": avg,
        "most_imbalanced_client": most_imbalanced["client_id"] if most_imbalanced else None,
        "clients": [
            {
                "client_id": c["client_id"],
                "num_samples": c["num_samples"],
                "num_classes_present": len(c["class_counts"]),
                "class_counts": c["class_counts"],
            }
            for c in partition["clients"]
        ],
    }
