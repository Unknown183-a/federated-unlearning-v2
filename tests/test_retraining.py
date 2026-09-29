"""Phase 11 tests: full-retraining baseline + comparison.

The comparison-math tests are pure data and run without torch. The
pipeline tests need torch and run against an in-memory synthetic
dataset (same approach as tests/test_evaluation.py) -- no downloads.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from core.evaluation.comparison import build_comparison
from core.evaluation.storage import (
    load_retraining_results,
    save_retraining_results,
)


# -- comparison.py (pure data, no torch) -------------------------------------


def _metrics(g, f, r, m):
    return {
        "global_accuracy": g,
        "forget_client_accuracy": f,
        "retained_client_accuracy": r,
        "mia_success": m,
    }


def _evaluation(target=2, unlearning_seconds=5.0):
    return {
        "experiment_id": "x",
        "target_client_id": target,
        "model": "cnn",
        "dataset": "mnist",
        "before": _metrics(0.90, 0.92, 0.91, 0.80),
        "after": _metrics(0.85, 0.40, 0.86, 0.55),
        "runtime": {"total_unlearning_seconds": unlearning_seconds},
    }


def _retraining(target=2, retraining_seconds=50.0):
    return {
        "experiment_id": "x",
        "run_kind": "separate_retraining_baseline",
        "target_client_id": target,
        "excluded_client_ids": [target],
        "num_clients_trained": 4,
        "protocol": {"rounds": 3},
        "metrics": _metrics(0.86, 0.30, 0.87, 0.50),
        "runtime": {"retraining_seconds": retraining_seconds, "original_training_seconds": 60.0},
    }


def test_build_comparison_lines_up_three_models():
    comparison = build_comparison(_evaluation(), _retraining())
    by_key = {m["key"]: m for m in comparison["metrics"]}

    forget = by_key["forget_client_accuracy"]
    assert (forget["original"], forget["unlearned"], forget["retrained"]) == (0.92, 0.40, 0.30)
    assert forget["unlearned_minus_retrained"] == pytest.approx(0.10)
    assert forget["original_minus_retrained"] == pytest.approx(0.62)
    assert forget["unlearned_closer_to_retrained"] is True
    assert [m["key"] for m in comparison["metrics"]] == [
        "global_accuracy",
        "forget_client_accuracy",
        "retained_client_accuracy",
        "mia_success",
    ]
    assert comparison["retraining_run"]["run_kind"] == "separate_retraining_baseline"


def test_build_comparison_reports_measured_speedup():
    runtime = build_comparison(_evaluation(unlearning_seconds=5.0), _retraining(retraining_seconds=50.0))[
        "runtime"
    ]
    assert runtime["time_saved_seconds"] == pytest.approx(45.0)
    assert runtime["time_saved_fraction"] == pytest.approx(0.9)
    assert runtime["speedup_factor"] == pytest.approx(10.0)
    assert runtime["unlearning_faster"] is True


def test_build_comparison_is_honest_when_unlearning_is_not_faster():
    """No clamping: a slower unlearning run yields negative time saved."""
    runtime = build_comparison(_evaluation(unlearning_seconds=80.0), _retraining(retraining_seconds=50.0))[
        "runtime"
    ]
    assert runtime["unlearning_faster"] is False
    assert runtime["time_saved_seconds"] == pytest.approx(-30.0)
    assert runtime["time_saved_fraction"] < 0


def test_build_comparison_makes_no_speedup_claim_without_both_times():
    evaluation = _evaluation()
    evaluation["runtime"] = {"total_unlearning_seconds": None}
    runtime = build_comparison(evaluation, _retraining())["runtime"]
    assert runtime["unlearning_faster"] is None
    assert runtime["time_saved_fraction"] is None
    assert runtime["speedup_factor"] is None


def test_build_comparison_flags_metric_that_moved_away_from_retrained():
    evaluation = _evaluation()
    evaluation["after"]["mia_success"] = 0.95  # worse than original 0.80; retrained is 0.50
    mia = {m["key"]: m for m in build_comparison(evaluation, _retraining())["metrics"]}["mia_success"]
    assert mia["unlearned_closer_to_retrained"] is False


def test_build_comparison_rejects_mismatched_target():
    with pytest.raises(ValueError, match="re-run"):
        build_comparison(_evaluation(target=2), _retraining(target=3))


def test_retraining_results_save_and_load_round_trip(tmp_path, monkeypatch):
    import core.evaluation.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    results = _retraining()
    save_retraining_results("test-exp", results)
    assert load_retraining_results("test-exp") == results
    assert (tmp_path / "test-exp" / "retraining_results.json").exists()


def test_load_retraining_results_missing_raises(tmp_path, monkeypatch):
    import core.evaluation.storage as storage

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_retraining_results("nope")


def test_compare_only_cli_needs_no_torch_and_reports_missing(tmp_path, monkeypatch, capsys):
    import core.evaluation.storage as storage
    from core.evaluation.retraining_cli import main

    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    assert main(["--experiment-id", "nope", "--compare-only"]) == 1
    assert "No evaluation results" in capsys.readouterr().err

    storage.save_evaluation_results("x", _evaluation())
    storage.save_retraining_results("x", _retraining())
    assert main(["--experiment-id", "x", "--compare-only"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["comparison"]["status"] == "complete"
    assert "retraining" not in out


# -- retraining.py: full pipeline (needs torch) --------------------------------

torch = pytest.importorskip("torch")

from torch.utils.data import TensorDataset


def _synthetic_dataset(num_samples, seed, num_classes=10):
    generator = torch.Generator().manual_seed(seed)
    images = torch.randn(num_samples, 1, 8, 8, generator=generator)
    labels = torch.randint(0, num_classes, (num_samples,), generator=generator)
    return TensorDataset(images, labels)


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """Partition -> FedAvg -> unlearn -> evaluate on a synthetic dataset,
    with every storage module and get_dataset redirected to tmp_path /
    the in-memory data. Returns the modules the tests need.
    """
    import core.evaluation.evaluation_engine as evaluation_engine
    import core.evaluation.retraining as retraining
    import core.evaluation.storage as evaluation_storage
    import core.federated.server as fl_server
    import core.federated.storage as fl_storage
    import core.partitioning.storage as partition_storage
    import core.unlearning.storage as unlearning_storage
    import core.unlearning.unlearning_engine as unlearning_engine

    for module in (fl_storage, partition_storage, unlearning_storage, evaluation_storage):
        monkeypatch.setattr(module, "EXPERIMENTS_DIR", tmp_path)

    torch.manual_seed(7)
    train_set = _synthetic_dataset(120, seed=7)
    test_set = _synthetic_dataset(50, seed=8)

    class _FakeDataset:
        def get_train(self_inner):
            return train_set

        def get_test(self_inner):
            return test_set

    fake = _FakeDataset()
    for module in (fl_server, unlearning_engine, evaluation_engine, retraining):
        monkeypatch.setattr(module, "get_dataset", lambda dataset_id: fake)

    partition = {
        "dataset": "mnist",  # manifest pins channels=1, num_classes=10
        "num_clients": 4,
        "strategy": "iid",
        "seed": 7,
        "clients": [{"client_id": i, "indices": list(range(i * 30, (i + 1) * 30))} for i in range(4)],
    }
    exp = "retrain-synthetic"
    partition_storage.save_partition(exp, partition)
    fl_server.run_federated_training(
        experiment_id=exp, partition=partition, model_id="cnn", rounds=2, local_epochs=1,
        seed=7, lr=0.1, batch_size=16,
    )
    unlearning_engine.start_unlearning(
        experiment_id=exp, client_id=1, steps=6, lr=0.5, batch_size=8,
        kd_epochs=1, kd_lr=0.05, kd_batch_size=16,
    )
    evaluation_engine.evaluate_experiment(exp, non_member_sample_size=50)
    return {"exp": exp, "dir": tmp_path, "retraining": retraining, "storage": evaluation_storage}


def test_retraining_baseline_full_pipeline(pipeline):
    from core.evaluation.comparison import compare_with_retraining

    exp = pipeline["exp"]
    results = pipeline["retraining"].run_retraining_baseline(exp)

    assert results["status"] == "complete"
    assert results["run_kind"] == "separate_retraining_baseline"
    assert results["target_client_id"] == 1
    assert results["excluded_client_ids"] == [1]
    assert results["num_clients_trained"] == 3
    # Protocol matched to the original run.
    assert results["protocol"]["rounds"] == 2
    assert results["protocol"]["seed"] == 7
    assert results["protocol"]["lr"] == pytest.approx(0.1)
    assert results["protocol"]["hyperparameters_recorded"] is True
    assert len(results["round_history"]) == 2
    # Same four metrics, scored on the same basis as Phase 10.
    m = results["metrics"]
    for key in ("global_accuracy", "forget_client_accuracy", "retained_client_accuracy", "mia_success"):
        assert 0.0 <= m[key] <= 1.0
    assert set(m["retained_client_accuracy_per_client"]) == {"0", "2", "3"}
    assert m["mia_detail"]["non_member_count"] == 50
    assert results["runtime"]["retraining_seconds"] > 0
    assert results["runtime"]["original_training_seconds"] > 0

    assert (pipeline["dir"] / exp / "retrained_model.pt").exists()
    assert pipeline["storage"].load_retraining_results(exp) == results

    comparison = compare_with_retraining(exp)
    assert comparison["status"] == "complete"
    assert comparison["runtime"]["retraining_seconds"] == results["runtime"]["retraining_seconds"]
    assert comparison["runtime"]["unlearning_faster"] in (True, False)


def test_retraining_baseline_does_not_touch_original_artifacts(pipeline):
    """It is a *separate run*: the original experiment's history and
    checkpoint must be byte-for-byte unchanged afterwards."""
    exp, d = pipeline["exp"], pipeline["dir"]
    watched = ["fl_history.json", "global_model.pt", "unlearning_final_model.pt",
               "unlearning_status.json", "evaluation_results.json", "partition.json"]
    before = {name: (d / exp / name).read_bytes() for name in watched}

    pipeline["retraining"].run_retraining_baseline(exp)

    for name in watched:
        assert (d / exp / name).read_bytes() == before[name], f"{name} was modified"


def test_retraining_excludes_target_client_data(pipeline, monkeypatch):
    """The retrained federation must contain every client except the target."""
    import core.evaluation.retraining as retraining

    seen = {}
    real = retraining.fedavg_train

    def spy(**kwargs):
        seen["ids"] = [c["client_id"] for c in kwargs["partition"]["clients"]]
        seen["num_clients"] = kwargs["partition"]["num_clients"]
        return real(**kwargs)

    monkeypatch.setattr(retraining, "fedavg_train", spy)
    retraining.run_retraining_baseline(pipeline["exp"])
    assert seen["ids"] == [0, 2, 3]
    assert seen["num_clients"] == 3


def test_retraining_requires_completed_unlearning(tmp_path, monkeypatch):
    import core.unlearning.storage as unlearning_storage
    from core.evaluation.retraining import run_retraining_baseline

    monkeypatch.setattr(unlearning_storage, "EXPERIMENTS_DIR", tmp_path)
    unlearning_storage.save_unlearning_status("e", {"experiment_id": "e", "status": "running"})
    with pytest.raises(ValueError):
        run_retraining_baseline("e")


def test_retraining_requires_stored_evaluation(pipeline):
    (pipeline["dir"] / pipeline["exp"] / "evaluation_results.json").unlink()
    with pytest.raises(FileNotFoundError):
        pipeline["retraining"].run_retraining_baseline(pipeline["exp"])


def test_retraining_rejects_stale_evaluation_for_different_target(pipeline):
    path = pipeline["dir"] / pipeline["exp"] / "evaluation_results.json"
    stored = json.loads(path.read_text())
    stored["target_client_id"] = 3
    path.write_text(json.dumps(stored))
    with pytest.raises(ValueError, match="re-run evaluation"):
        pipeline["retraining"].run_retraining_baseline(pipeline["exp"])


def test_retraining_falls_back_to_legacy_defaults_for_old_histories(pipeline):
    """fl_history.json written before Phase 11 has no lr/batch_size."""
    path = pipeline["dir"] / pipeline["exp"] / "fl_history.json"
    history = json.loads(path.read_text())
    history.pop("lr"), history.pop("batch_size")
    path.write_text(json.dumps(history))

    results = pipeline["retraining"].run_retraining_baseline(pipeline["exp"])
    assert results["protocol"]["lr"] == pipeline["retraining"].LEGACY_LR
    assert results["protocol"]["batch_size"] == pipeline["retraining"].LEGACY_BATCH_SIZE
    assert results["protocol"]["hyperparameters_recorded"] is False
