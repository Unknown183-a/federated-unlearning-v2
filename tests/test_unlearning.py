import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

torch = pytest.importorskip("torch")

from torch.utils.data import TensorDataset

from core.federated.model import build_model
from core.partitioning.engine import partition_dataset
from core.unlearning.gradient_ascent import run_gradient_ascent
from core.unlearning.storage import (
    load_ga_checkpoint,
    load_unlearning_status,
    save_ga_checkpoint,
    save_unlearning_status,
)


def _synthetic_dataset(num_samples=40, channels=1, size=8, num_classes=3, seed=0):
    """A small in-memory dataset shaped like the real ones, without any
    download -- keeps the ascent-direction unit tests fast and offline.
    """
    generator = torch.Generator().manual_seed(seed)
    images = torch.randn(num_samples, channels, size, size, generator=generator)
    labels = torch.randint(0, num_classes, (num_samples,), generator=generator)
    return TensorDataset(images, labels)


def test_run_gradient_ascent_raises_on_empty_target_indices():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        run_gradient_ascent(
            global_state=model.state_dict(),
            model_id="cnn",
            channels=1,
            num_classes=3,
            dataset=dataset,
            target_indices=[],
            steps=5,
        )


def test_run_gradient_ascent_rejects_zero_steps():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        run_gradient_ascent(
            global_state=model.state_dict(),
            model_id="cnn",
            channels=1,
            num_classes=3,
            dataset=dataset,
            target_indices=[0, 1, 2],
            steps=0,
        )


def test_run_gradient_ascent_raises_target_client_loss():
    """The Phase 08 acceptance criterion, directly: target-client loss
    must measurably rise over the ascent steps.
    """
    torch.manual_seed(0)
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset(num_samples=40, channels=1, size=8, num_classes=3)
    target_indices = list(range(len(dataset)))

    result = run_gradient_ascent(
        global_state=model.state_dict(),
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        target_indices=target_indices,
        steps=15,
        lr=0.5,
        batch_size=8,
        plateau_patience=15,  # disable early stopping for this check
    )

    assert result["final_loss"] > result["initial_loss"]
    assert len(result["step_history"]) == result["steps_completed"]
    # Loss should be non-decreasing step over step on the way up, since
    # we're deliberately ascending it (a little noise is fine given
    # mini-batch sampling, but the overall trend must be upward).
    assert result["step_history"][-1]["loss"] > result["step_history"][0]["loss"]


def test_run_gradient_ascent_never_exceeds_requested_steps():
    torch.manual_seed(1)
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    result = run_gradient_ascent(
        global_state=model.state_dict(),
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        target_indices=list(range(len(dataset))),
        steps=10,
        batch_size=8,
    )
    assert result["steps_completed"] <= 10
    assert result["steps_requested"] == 10


def test_unlearning_status_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.unlearning.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    status = {"experiment_id": "test-exp", "stage": "gradient_ascent", "status": "complete"}
    save_unlearning_status("test-exp", status)
    loaded = load_unlearning_status("test-exp")
    assert loaded == status
    assert (tmp_path / "test-exp" / "unlearning_status.json").exists()


def test_load_unlearning_status_missing_raises(tmp_path, monkeypatch):
    import core.unlearning.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_unlearning_status("does-not-exist")


def test_ga_checkpoint_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.unlearning.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    model = build_model("cnn", channels=1, num_classes=3)
    save_ga_checkpoint("test-exp", model.state_dict(), model_id="cnn", channels=1, num_classes=3)
    loaded = load_ga_checkpoint("test-exp")
    assert loaded["model_id"] == "cnn"
    assert loaded["channels"] == 1
    assert loaded["num_classes"] == 3
    assert loaded["state_dict"].keys() == model.state_dict().keys()


@pytest.mark.slow
def test_start_unlearning_end_to_end_on_mnist(tmp_path, monkeypatch):
    """Integration test: real partition + real (tiny) FedAvg run, then a
    real Gradient Ascent stage against the saved checkpoint -- mirrors
    the Phase 08 acceptance criteria end to end.
    """
    import core.federated.storage as fl_storage
    import core.partitioning.storage as partition_storage
    import core.unlearning.storage as unlearning_storage
    from core.federated.server import run_federated_training
    from core.unlearning.unlearning_engine import get_unlearning_status, start_unlearning

    monkeypatch.setattr(fl_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(partition_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)

    partition = partition_dataset("mnist", num_clients=5, strategy="iid", seed=42)
    partition_storage.save_partition("mnist-unlearn-smoke", partition)
    run_federated_training(
        experiment_id="mnist-unlearn-smoke",
        partition=partition,
        model_id="cnn",
        rounds=1,
        local_epochs=1,
        seed=42,
        lr=0.1,
        batch_size=64,
    )

    status = start_unlearning(
        experiment_id="mnist-unlearn-smoke",
        client_id=2,
        steps=10,
        lr=0.5,
        batch_size=32,
    )

    assert status["status"] == "complete"
    assert status["target_client_id"] == 2
    assert status["final_loss"] > status["initial_loss"]
    assert (tmp_path / "mnist-unlearn-smoke" / "unlearning_ga_model.pt").exists()

    reloaded = get_unlearning_status("mnist-unlearn-smoke")
    assert reloaded == status


def test_start_unlearning_rejects_unknown_client(tmp_path, monkeypatch):
    import core.federated.storage as fl_storage
    import core.partitioning.storage as partition_storage
    import core.unlearning.storage as unlearning_storage
    from core.unlearning.unlearning_engine import start_unlearning

    monkeypatch.setattr(fl_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(partition_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)

    partition = partition_dataset("mnist", num_clients=3, strategy="iid", seed=1)
    partition_storage.save_partition("bad-client-exp", partition)
    fl_storage.save_fl_history(
        "bad-client-exp",
        {"experiment_id": "bad-client-exp", "model": "cnn", "dataset": "mnist", "round_history": []},
    )
    model = build_model("cnn", channels=1, num_classes=10)
    fl_storage.save_model_checkpoint(
        "bad-client-exp", model.state_dict(), model_id="cnn", channels=1, num_classes=10
    )

    with pytest.raises(ValueError):
        start_unlearning("bad-client-exp", client_id=99)
