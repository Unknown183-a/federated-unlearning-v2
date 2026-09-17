import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

torch = pytest.importorskip("torch")

from torch.utils.data import TensorDataset

from core.federated.client import local_train
from core.federated.model import build_model
from core.partitioning.engine import partition_dataset
from core.unlearning.gradient_ascent import run_gradient_ascent
from core.unlearning.knowledge_distillation import run_knowledge_distillation
from core.unlearning.storage import (
    load_final_checkpoint,
    load_ga_checkpoint,
    load_unlearning_status,
    save_final_checkpoint,
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


def test_run_knowledge_distillation_raises_on_empty_retained_clients():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        run_knowledge_distillation(
            teacher_state=model.state_dict(),
            student_state=model.state_dict(),
            model_id="cnn",
            channels=1,
            num_classes=3,
            dataset=dataset,
            retained_clients=[],
            epochs=3,
        )


def test_run_knowledge_distillation_rejects_zero_epochs():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        run_knowledge_distillation(
            teacher_state=model.state_dict(),
            student_state=model.state_dict(),
            model_id="cnn",
            channels=1,
            num_classes=3,
            dataset=dataset,
            retained_clients=[{"client_id": 1, "indices": [0, 1, 2]}],
            epochs=0,
        )


def test_run_knowledge_distillation_recovers_retained_accuracy():
    """The Phase 09 acceptance criterion, directly: retained-client
    accuracy must measurably recover after distillation.

    Builds a teacher that has actually fit this (small, memorizable)
    dataset, damages a copy of it with Gradient Ascent the same way
    Phase 08 would, then checks that distilling the teacher's
    knowledge back in recovers the damage on the retained clients.
    """
    torch.manual_seed(0)
    dataset = _synthetic_dataset(num_samples=80, channels=1, size=8, num_classes=3, seed=0)
    base_model = build_model("cnn", channels=1, num_classes=3)

    # Full-batch, enough epochs to actually memorize this tiny dataset --
    # otherwise there's nothing for the teacher to know that the
    # damaged student doesn't, and "recovery" wouldn't mean anything.
    teacher_result = local_train(
        global_state=base_model.state_dict(),
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        indices=list(range(len(dataset))),
        epochs=60,
        lr=0.02,
        batch_size=80,
    )
    teacher_state = teacher_result["state_dict"]

    target_indices = list(range(0, 20))
    retained_indices = list(range(20, 80))

    # A handful of ascent steps -- enough to measurably hurt retained
    # accuracy without diverging into a fully collapsed model that no
    # amount of distillation could recover (gradient ascent has no
    # natural stopping point, so a few too many steps overshoots fast).
    ga_result = run_gradient_ascent(
        global_state=teacher_state,
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        target_indices=target_indices,
        steps=8,
        lr=0.01,
        batch_size=20,
    )
    damaged_state = ga_result["final_state_dict"]

    retained_clients = [{"client_id": 1, "indices": retained_indices}]

    result = run_knowledge_distillation(
        teacher_state=teacher_state,
        student_state=damaged_state,
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        retained_clients=retained_clients,
        epochs=10,
        lr=0.02,
        batch_size=60,
    )

    assert result["final_retained_accuracy"] > result["initial_retained_accuracy"]
    assert len(result["epoch_history"]) == 10
    assert set(result["per_client_accuracy_before"].keys()) == {1}
    assert set(result["per_client_accuracy_after"].keys()) == {1}


def test_run_knowledge_distillation_tracks_per_client_accuracy():
    torch.manual_seed(2)
    dataset = _synthetic_dataset(num_samples=60, channels=1, size=8, num_classes=3, seed=2)
    model = build_model("cnn", channels=1, num_classes=3)

    retained_clients = [
        {"client_id": 0, "indices": list(range(0, 20))},
        {"client_id": 2, "indices": list(range(20, 40))},
        {"client_id": 3, "indices": list(range(40, 60))},
    ]

    result = run_knowledge_distillation(
        teacher_state=model.state_dict(),
        student_state=model.state_dict(),
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        retained_clients=retained_clients,
        epochs=2,
        batch_size=16,
    )

    assert set(result["per_client_accuracy_before"].keys()) == {0, 2, 3}
    assert set(result["per_client_accuracy_after"].keys()) == {0, 2, 3}
    for epoch_entry in result["epoch_history"]:
        assert {"epoch", "kd_loss", "retained_accuracy"} <= epoch_entry.keys()


def test_final_checkpoint_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.unlearning.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    model = build_model("cnn", channels=1, num_classes=3)
    save_final_checkpoint("test-exp", model.state_dict(), model_id="cnn", channels=1, num_classes=3)
    loaded = load_final_checkpoint("test-exp")
    assert loaded["model_id"] == "cnn"
    assert loaded["channels"] == 1
    assert loaded["num_classes"] == 3
    assert loaded["state_dict"].keys() == model.state_dict().keys()


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
    real Gradient Ascent + Knowledge Distillation pipeline against the
    saved checkpoint -- mirrors the Phase 08 + Phase 09 acceptance
    criteria end to end.
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
        kd_epochs=2,
        kd_batch_size=64,
    )

    assert status["status"] == "complete"
    assert status["target_client_id"] == 2
    assert status["gradient_ascent"]["final_loss"] > status["gradient_ascent"]["initial_loss"]
    assert (tmp_path / "mnist-unlearn-smoke" / "unlearning_ga_model.pt").exists()

    kd = status["knowledge_distillation"]
    assert kd["final_retained_accuracy"] >= 0
    assert len(kd["epoch_history"]) == 2
    assert (tmp_path / "mnist-unlearn-smoke" / "unlearning_final_model.pt").exists()

    reloaded = get_unlearning_status("mnist-unlearn-smoke")
    assert reloaded == status


def test_start_unlearning_full_pipeline_synthetic(tmp_path, monkeypatch):
    """Same pipeline as the MNIST integration test above, but against an
    in-memory synthetic dataset (no torchvision download needed) so
    this runs everywhere the fast unit tests do.
    """
    import core.federated.server as fl_server
    import core.federated.storage as fl_storage
    import core.partitioning.storage as partition_storage
    import core.unlearning.storage as unlearning_storage
    import core.unlearning.unlearning_engine as unlearning_engine

    monkeypatch.setattr(fl_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(partition_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)

    torch.manual_seed(3)
    # mnist's manifest entry pins channels=1, num_classes=10 -- match
    # that here so run_federated_training's real load_manifest() call
    # stays consistent with the fake dataset's shape.
    train_set = _synthetic_dataset(num_samples=120, channels=1, size=8, num_classes=10, seed=3)
    test_set = _synthetic_dataset(num_samples=40, channels=1, size=8, num_classes=10, seed=4)

    class _FakeDataset:
        def get_train(self_inner):
            return train_set

        def get_test(self_inner):
            return test_set

    fake_dataset = _FakeDataset()
    monkeypatch.setattr(fl_server, "get_dataset", lambda dataset_id: fake_dataset)
    monkeypatch.setattr(unlearning_engine, "get_dataset", lambda dataset_id: fake_dataset)

    partition = {
        "dataset": "mnist",
        "num_clients": 4,
        "strategy": "iid",
        "seed": 3,
        "clients": [
            {"client_id": i, "indices": list(range(i * 30, (i + 1) * 30))} for i in range(4)
        ],
    }
    partition_storage.save_partition("synthetic-unlearn", partition)
    fl_server.run_federated_training(
        experiment_id="synthetic-unlearn",
        partition=partition,
        model_id="cnn",
        rounds=1,
        local_epochs=1,
        seed=3,
        lr=0.1,
        batch_size=16,
    )

    status = unlearning_engine.start_unlearning(
        experiment_id="synthetic-unlearn",
        client_id=1,
        steps=8,
        lr=0.5,
        batch_size=8,
        kd_epochs=3,
        kd_lr=0.05,
        kd_batch_size=16,
    )

    assert status["status"] == "complete"
    assert status["stage"] == "knowledge_distillation"
    assert status["target_client_id"] == 1

    ga = status["gradient_ascent"]
    assert ga["status"] == "complete"
    assert ga["final_loss"] > ga["initial_loss"]

    kd = status["knowledge_distillation"]
    assert kd["status"] == "complete"
    assert set(kd["per_client_accuracy_before"].keys()) == {0, 2, 3}
    assert len(kd["epoch_history"]) == 3

    assert (tmp_path / "synthetic-unlearn" / "unlearning_ga_model.pt").exists()
    assert (tmp_path / "synthetic-unlearn" / "unlearning_final_model.pt").exists()


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
