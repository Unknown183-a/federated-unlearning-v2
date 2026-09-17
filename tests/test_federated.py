import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

torch = pytest.importorskip("torch")

from core.federated.fedavg import federated_average
from core.federated.model import build_model
from core.federated.storage import load_fl_history, save_fl_history
from core.partitioning.engine import partition_dataset


def test_federated_average_is_sample_weighted_mean():
    state_a = {"w": torch.tensor([0.0, 0.0])}
    state_b = {"w": torch.tensor([10.0, 10.0])}
    # 1 sample for a, 3 samples for b -> b should dominate the average.
    averaged = federated_average([state_a, state_b], [1, 3])
    assert torch.allclose(averaged["w"], torch.tensor([7.5, 7.5]))


def test_federated_average_equal_weights_is_plain_mean():
    state_a = {"w": torch.tensor([1.0, 2.0])}
    state_b = {"w": torch.tensor([3.0, 4.0])}
    averaged = federated_average([state_a, state_b], [10, 10])
    assert torch.allclose(averaged["w"], torch.tensor([2.0, 3.0]))


def test_federated_average_rejects_mismatched_lengths():
    state_a = {"w": torch.tensor([1.0])}
    with pytest.raises(ValueError):
        federated_average([state_a], [1, 2])


def test_federated_average_rejects_empty_input():
    with pytest.raises(ValueError):
        federated_average([], [])


@pytest.mark.parametrize("model_id", ["cnn", "resnet"])
def test_build_model_output_shape(model_id):
    model = build_model(model_id, channels=1, num_classes=10)
    x = torch.randn(4, 1, 28, 28)
    out = model(x)
    assert out.shape == (4, 10)


def test_build_model_rejects_unknown_id():
    with pytest.raises(ValueError):
        build_model("bogus", channels=1, num_classes=10)


def test_fl_history_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.federated.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    history = {"experiment_id": "test-exp", "round_history": [{"round": 1, "accuracy": 0.9}]}
    save_fl_history("test-exp", history)
    loaded = load_fl_history("test-exp")
    assert loaded == history
    assert (tmp_path / "test-exp" / "fl_history.json").exists()


def test_load_fl_history_missing_raises(tmp_path, monkeypatch):
    import core.federated.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_fl_history("does-not-exist")


@pytest.mark.slow
def test_run_federated_training_converges_on_mnist(tmp_path, monkeypatch):
    """Integration test: real FedAvg loop, real MNIST, real convergence.

    Mirrors the Phase 05 acceptance criterion directly -- a full run on
    MNIST with 5 clients should converge to a reasonable accuracy within
    a couple of rounds, and get_fl_history() should return the same
    well-formed, round-by-round history that was persisted.
    """
    import core.federated.storage as storage
    from core.federated.server import get_fl_history, run_federated_training

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)

    partition = partition_dataset("mnist", num_clients=5, strategy="iid", seed=42)
    history = run_federated_training(
        experiment_id="mnist-smoke",
        partition=partition,
        model_id="cnn",
        rounds=2,
        local_epochs=1,
        seed=42,
        lr=0.1,
        batch_size=64,
    )

    assert history["num_clients"] == 5
    assert len(history["round_history"]) == 2
    for i, round_entry in enumerate(history["round_history"], start=1):
        assert round_entry["round"] == i
        assert 0.0 <= round_entry["accuracy"] <= 1.0
        assert round_entry["loss"] >= 0.0
        assert len(round_entry["clients"]) == 5
        assert all(c["completed"] for c in round_entry["clients"])

    # "Converges to a reasonable accuracy" -- MNIST with 5 IID clients
    # should comfortably clear random-guess (10%) well before round 2.
    assert history["final_accuracy"] > 0.7

    reloaded = get_fl_history("mnist-smoke")
    assert reloaded == history
