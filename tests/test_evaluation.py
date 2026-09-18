import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

torch = pytest.importorskip("torch")

from torch.utils.data import TensorDataset

from core.federated.client import local_train
from core.federated.model import build_model
from core.evaluation.accuracy import (
    compute_accuracy,
    evaluate_client_accuracy,
    evaluate_global_accuracy,
    evaluate_retained_accuracy,
)
from core.evaluation.mia import run_membership_inference
from core.evaluation.storage import load_evaluation_results, save_evaluation_results


def _synthetic_dataset(num_samples=40, channels=1, size=8, num_classes=3, seed=0):
    """A small in-memory dataset shaped like the real ones, without any
    download -- keeps the accuracy/MIA unit tests fast and offline.
    """
    generator = torch.Generator().manual_seed(seed)
    images = torch.randn(num_samples, channels, size, size, generator=generator)
    labels = torch.randint(0, num_classes, (num_samples,), generator=generator)
    return TensorDataset(images, labels)


# -- accuracy.py -------------------------------------------------------


def test_evaluate_global_accuracy_matches_compute_accuracy():
    from torch.utils.data import DataLoader

    torch.manual_seed(0)
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()

    direct = compute_accuracy(model, DataLoader(dataset, batch_size=16, shuffle=False), "cpu")
    via_helper = evaluate_global_accuracy(
        model.state_dict(), "cnn", channels=1, num_classes=3, test_dataset=dataset, device="cpu"
    )
    assert via_helper == pytest.approx(direct)


def test_evaluate_client_accuracy_raises_on_empty_indices():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        evaluate_client_accuracy(
            model.state_dict(), "cnn", channels=1, num_classes=3, train_dataset=dataset, indices=[]
        )


def test_evaluate_client_accuracy_recovers_high_accuracy_after_memorizing():
    """A model trained to memorize one client's data should score highly
    on that same client's accuracy metric -- a basic sanity check that
    the metric measures what it says it does.
    """
    torch.manual_seed(0)
    dataset = _synthetic_dataset(num_samples=30, channels=1, size=8, num_classes=3, seed=0)
    base_model = build_model("cnn", channels=1, num_classes=3)
    indices = list(range(len(dataset)))

    trained = local_train(
        global_state=base_model.state_dict(),
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=dataset,
        indices=indices,
        epochs=40,
        lr=0.05,
        batch_size=30,
    )

    accuracy = evaluate_client_accuracy(
        trained["state_dict"], "cnn", channels=1, num_classes=3, train_dataset=dataset, indices=indices
    )
    assert accuracy > 0.8


def test_evaluate_retained_accuracy_raises_on_empty_clients():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        evaluate_retained_accuracy(
            model.state_dict(),
            "cnn",
            channels=1,
            num_classes=3,
            train_dataset=dataset,
            retained_clients=[],
        )


def test_evaluate_retained_accuracy_tracks_per_client_and_mean():
    torch.manual_seed(1)
    dataset = _synthetic_dataset(num_samples=60, channels=1, size=8, num_classes=3, seed=1)
    model = build_model("cnn", channels=1, num_classes=3)

    retained_clients = [
        {"client_id": 0, "indices": list(range(0, 20))},
        {"client_id": 2, "indices": list(range(20, 40))},
        {"client_id": 3, "indices": list(range(40, 60))},
    ]

    result = evaluate_retained_accuracy(
        model.state_dict(),
        "cnn",
        channels=1,
        num_classes=3,
        train_dataset=dataset,
        retained_clients=retained_clients,
    )
    # Keys are strings, not ints -- see the comment in
    # evaluate_retained_accuracy: this dict round-trips through JSON.
    assert set(result["per_client"].keys()) == {"0", "2", "3"}
    expected_mean = sum(result["per_client"].values()) / 3
    assert result["mean"] == pytest.approx(expected_mean)


# -- mia.py --------------------------------------------------------------


def test_run_membership_inference_raises_on_empty_member_indices():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        run_membership_inference(
            model.state_dict(),
            "cnn",
            channels=1,
            num_classes=3,
            train_dataset=dataset,
            member_indices=[],
            non_member_dataset=dataset,
            non_member_indices=[0, 1, 2],
        )


def test_run_membership_inference_raises_on_empty_non_member_indices():
    model = build_model("cnn", channels=1, num_classes=3)
    dataset = _synthetic_dataset()
    with pytest.raises(ValueError):
        run_membership_inference(
            model.state_dict(),
            "cnn",
            channels=1,
            num_classes=3,
            train_dataset=dataset,
            member_indices=[0, 1, 2],
            non_member_dataset=dataset,
            non_member_indices=[],
        )


def test_run_membership_inference_near_chance_on_untrained_model():
    """An untrained (randomly initialized) model has no memorized
    training set, so it shouldn't leak membership -- attack accuracy
    should sit close to the 0.5 chance baseline.
    """
    torch.manual_seed(0)
    model = build_model("cnn", channels=1, num_classes=3)
    train_dataset = _synthetic_dataset(num_samples=60, channels=1, size=8, num_classes=3, seed=0)
    test_dataset = _synthetic_dataset(num_samples=60, channels=1, size=8, num_classes=3, seed=1)

    result = run_membership_inference(
        model.state_dict(),
        "cnn",
        channels=1,
        num_classes=3,
        train_dataset=train_dataset,
        member_indices=list(range(30)),
        non_member_dataset=test_dataset,
        non_member_indices=list(range(30)),
    )
    # Threshold sweep always finds *some* separating value on finite
    # noisy data, so this isn't pinned to exactly 0.5 -- just checks it
    # isn't dramatically better than chance the way a memorizing model
    # would be (see the "memorized" test below).
    assert result["attack_accuracy"] < 0.8
    assert result["member_count"] == 30
    assert result["non_member_count"] == 30


def test_run_membership_inference_detects_memorized_training_set():
    """A model trained to convergence on one specific set of samples
    should have measurably lower loss on those samples than on unseen
    ones -- the MIA should catch that as high attack accuracy.
    """
    torch.manual_seed(2)
    train_dataset = _synthetic_dataset(num_samples=20, channels=1, size=8, num_classes=3, seed=2)
    held_out_dataset = _synthetic_dataset(num_samples=20, channels=1, size=8, num_classes=3, seed=3)
    base_model = build_model("cnn", channels=1, num_classes=3)
    member_indices = list(range(len(train_dataset)))

    trained = local_train(
        global_state=base_model.state_dict(),
        model_id="cnn",
        channels=1,
        num_classes=3,
        dataset=train_dataset,
        indices=member_indices,
        epochs=60,
        lr=0.05,
        batch_size=20,
    )

    result = run_membership_inference(
        trained["state_dict"],
        "cnn",
        channels=1,
        num_classes=3,
        train_dataset=train_dataset,
        member_indices=member_indices,
        non_member_dataset=held_out_dataset,
        non_member_indices=list(range(len(held_out_dataset))),
    )
    assert result["attack_accuracy"] > 0.7
    assert result["mean_member_loss"] < result["mean_non_member_loss"]


# -- storage.py ------------------------------------------------------------


def test_evaluation_results_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.evaluation.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    results = {"experiment_id": "test-exp", "status": "complete", "before": {}, "after": {}}
    save_evaluation_results("test-exp", results)
    loaded = load_evaluation_results("test-exp")
    assert loaded == results
    assert (tmp_path / "test-exp" / "evaluation_results.json").exists()


def test_load_evaluation_results_missing_raises(tmp_path, monkeypatch):
    import core.evaluation.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_evaluation_results("does-not-exist")


# -- evaluation_engine.py: full pipeline ------------------------------------


def test_evaluate_experiment_full_pipeline_synthetic(tmp_path, monkeypatch):
    """Partition -> FedAvg -> unlearn -> evaluate, end to end, against an
    in-memory synthetic dataset (mirrors
    test_unlearning.test_start_unlearning_full_pipeline_synthetic).
    """
    import core.evaluation.evaluation_engine as evaluation_engine
    import core.evaluation.storage as evaluation_storage
    import core.federated.server as fl_server
    import core.federated.storage as fl_storage
    import core.partitioning.storage as partition_storage
    import core.unlearning.storage as unlearning_storage
    import core.unlearning.unlearning_engine as unlearning_engine

    monkeypatch.setattr(fl_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(partition_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)
    monkeypatch.setattr(evaluation_storage, "EXPERIMENTS_DIR", tmp_path)

    torch.manual_seed(4)
    # mnist's manifest entry pins channels=1, num_classes=10 -- match
    # that here so the real load_manifest() calls stay consistent with
    # this fake dataset's shape.
    train_set = _synthetic_dataset(num_samples=120, channels=1, size=8, num_classes=10, seed=4)
    test_set = _synthetic_dataset(num_samples=50, channels=1, size=8, num_classes=10, seed=5)

    class _FakeDataset:
        def get_train(self_inner):
            return train_set

        def get_test(self_inner):
            return test_set

    fake_dataset = _FakeDataset()
    monkeypatch.setattr(fl_server, "get_dataset", lambda dataset_id: fake_dataset)
    monkeypatch.setattr(unlearning_engine, "get_dataset", lambda dataset_id: fake_dataset)
    monkeypatch.setattr(evaluation_engine, "get_dataset", lambda dataset_id: fake_dataset)

    partition = {
        "dataset": "mnist",
        "num_clients": 4,
        "strategy": "iid",
        "seed": 4,
        "clients": [
            {"client_id": i, "indices": list(range(i * 30, (i + 1) * 30))} for i in range(4)
        ],
    }
    partition_storage.save_partition("eval-synthetic", partition)
    fl_server.run_federated_training(
        experiment_id="eval-synthetic",
        partition=partition,
        model_id="cnn",
        rounds=1,
        local_epochs=1,
        seed=4,
        lr=0.1,
        batch_size=16,
    )

    unlearning_engine.start_unlearning(
        experiment_id="eval-synthetic",
        client_id=1,
        steps=8,
        lr=0.5,
        batch_size=8,
        kd_epochs=2,
        kd_lr=0.05,
        kd_batch_size=16,
    )

    results = evaluation_engine.evaluate_experiment(
        "eval-synthetic", non_member_sample_size=50, device="cpu"
    )

    assert results["status"] == "complete"
    assert results["target_client_id"] == 1
    for label in ("before", "after"):
        metrics = results[label]
        assert 0.0 <= metrics["global_accuracy"] <= 1.0
        assert 0.0 <= metrics["forget_client_accuracy"] <= 1.0
        assert 0.0 <= metrics["retained_client_accuracy"] <= 1.0
        assert set(metrics["retained_client_accuracy_per_client"].keys()) == {"0", "2", "3"}
        assert 0.0 <= metrics["mia_success"] <= 1.0

    assert results["runtime"]["total_unlearning_seconds"] is not None
    assert results["runtime"]["gradient_ascent_seconds"] is not None
    assert results["runtime"]["knowledge_distillation_seconds"] is not None
    assert results["runtime"]["evaluation_seconds"] > 0

    reloaded = evaluation_storage.load_evaluation_results("eval-synthetic")
    assert reloaded == results


def test_evaluate_experiment_raises_if_unlearning_not_complete(tmp_path, monkeypatch):
    import core.unlearning.storage as unlearning_storage
    from core.evaluation.evaluation_engine import evaluate_experiment

    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)
    unlearning_storage.save_unlearning_status(
        "in-progress-exp", {"experiment_id": "in-progress-exp", "status": "running"}
    )
    with pytest.raises(ValueError):
        evaluate_experiment("in-progress-exp")


def test_evaluate_experiment_raises_if_never_unlearned(tmp_path, monkeypatch):
    import core.unlearning.storage as unlearning_storage
    from core.evaluation.evaluation_engine import evaluate_experiment

    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        evaluate_experiment("never-unlearned-exp")
