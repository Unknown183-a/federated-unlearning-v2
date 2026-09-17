import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from core.partitioning.engine import (
    get_client_distribution,
    partition_dataset,
    summarize_partition,
)
from core.partitioning.storage import load_partition, save_partition


@pytest.mark.parametrize("strategy", ["iid", "non_iid"])
@pytest.mark.parametrize("num_clients", [5, 10, 20])
def test_partition_covers_every_sample_exactly_once(strategy, num_clients):
    partition = partition_dataset("cifar10", num_clients, strategy, seed=42)
    all_indices = sorted(i for c in partition["clients"] for i in c["indices"])
    assert all_indices == list(range(partition["total_samples"]))
    assert len(partition["clients"]) == num_clients


def test_same_seed_and_config_reproduces_identical_partition():
    a = partition_dataset("cifar100", 10, "non_iid", seed=7)
    b = partition_dataset("cifar100", 10, "non_iid", seed=7)
    assert [c["indices"] for c in a["clients"]] == [c["indices"] for c in b["clients"]]


def test_different_seed_changes_the_partition():
    a = partition_dataset("cifar100", 10, "non_iid", seed=1)
    b = partition_dataset("cifar100", 10, "non_iid", seed=2)
    assert [c["indices"] for c in a["clients"]] != [c["indices"] for c in b["clients"]]


def test_non_iid_is_more_class_skewed_than_iid():
    iid = partition_dataset("cifar10", 10, "iid", seed=42)
    non_iid = partition_dataset("cifar10", 10, "non_iid", seed=42)

    def total_classes_touched(partition):
        return sum(len(c["class_counts"]) for c in partition["clients"])

    # IID clients should each see close to all 10 classes; Non-IID
    # (alpha=0.5) clients should see noticeably fewer classes each.
    assert total_classes_touched(non_iid) < total_classes_touched(iid)


def test_get_client_distribution():
    partition = partition_dataset("mnist", 5, "non_iid", seed=3)
    dist = get_client_distribution(partition, 0)
    assert dist["client_id"] == 0
    assert dist["num_samples"] == partition["clients"][0]["num_samples"]
    assert "dominant_classes" in dist
    assert len(dist["dominant_classes"]) <= 3


def test_get_client_distribution_rejects_out_of_range_client():
    partition = partition_dataset("mnist", 5, "iid", seed=3)
    with pytest.raises(KeyError):
        get_client_distribution(partition, 5)


def test_summarize_strips_indices_but_keeps_counts():
    partition = partition_dataset("mnist", 5, "iid", seed=1)
    summary = summarize_partition(partition)
    assert "indices" not in summary["clients"][0]
    assert summary["average_samples_per_client"] == pytest.approx(12000)
    assert summary["most_imbalanced_client"] is not None


def test_rejects_bad_inputs():
    with pytest.raises(ValueError):
        partition_dataset("mnist", 1, "iid", seed=1)
    with pytest.raises(ValueError):
        partition_dataset("mnist", 5, "bogus_strategy", seed=1)
    with pytest.raises(KeyError):
        partition_dataset("not-a-real-dataset", 5, "iid", seed=1)


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.partitioning.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    partition = partition_dataset("mnist", 5, "iid", seed=1)
    save_partition("test-exp", partition)
    loaded = load_partition("test-exp")
    # JSON round-trips dict keys as strings, so class_counts keys change
    # type (0 -> "0") -- indices, sample counts, and everything else
    # should still match exactly.
    assert [c["indices"] for c in loaded["clients"]] == [c["indices"] for c in partition["clients"]]
    assert [c["num_samples"] for c in loaded["clients"]] == [c["num_samples"] for c in partition["clients"]]
    assert (tmp_path / "test-exp" / "partition.json").exists()
