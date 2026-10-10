"""Phase 15 tests: reproducibility metadata and the acceptance checker.

Everything here is torch-free on purpose -- the acceptance checker only
reads JSON, and the whole point of Phase 15 is that the research story
can be verified and replayed on a machine with no GPU and no backend.
Experiments are built as small synthetic artifact folders in tmp_path,
so no dataset download or training is needed.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

import core.acceptance.checks as checks
from core.acceptance.checks import FAIL, PASS, WARN, validate_experiment
from core import provenance


# -- A complete, internally consistent synthetic experiment ----------------


def _metrics(g, f, r, m):
    return {
        "global_accuracy": g,
        "forget_client_accuracy": f,
        "retained_client_accuracy": r,
        "mia_success": m,
    }


def make_experiment(base: Path, experiment_id="exp-ok", *, hyperparameters=True):
    """Write every artifact a finished experiment has (4 clients, 8 samples)."""
    d = base / experiment_id
    d.mkdir(parents=True)

    clients = [
        {
            "client_id": i,
            "indices": [2 * i, 2 * i + 1],
            "num_samples": 2,
            "class_counts": {"0": 1, "1": 1},
        }
        for i in range(4)
    ]
    (d / "partition.json").write_text(
        json.dumps(
            {
                "dataset": "mnist",
                "num_clients": 4,
                "strategy": "non_iid",
                "seed": 42,
                "alpha": 0.5,
                "num_classes": 10,
                "total_samples": 8,
                "clients": clients,
            }
        )
    )

    rounds = [
        {
            "round": n,
            "accuracy": 0.5 + 0.1 * n,
            "loss": 1.0 / n,
            "duration_seconds": 1.0,
            "clients": [{"client_id": i, "num_samples": 2, "local_loss": 0.5, "completed": True} for i in range(4)],
        }
        for n in (1, 2, 3)
    ]
    (d / "fl_history.json").write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "dataset": "mnist",
                "model": "cnn",
                "num_clients": 4,
                "rounds": 3,
                "local_epochs": 1,
                "seed": 42,
                "lr": 0.01,
                "batch_size": 32,
                "final_accuracy": rounds[-1]["accuracy"],
                "final_loss": rounds[-1]["loss"],
                "round_history": rounds,
            }
        )
    )
    (d / "global_model.pt").write_bytes(b"x")

    status = {
        "experiment_id": experiment_id,
        "target_client_id": 2,
        "model": "cnn",
        "dataset": "mnist",
        "stage": "knowledge_distillation",
        "status": "complete",
        "gradient_ascent": {
            "status": "complete",
            "initial_loss": 0.2,
            "initial_accuracy": 0.95,
            "final_loss": 2.5,
            "final_accuracy": 0.1,
            "steps_completed": 2,
            "steps_requested": 2,
            "stopped_early": False,
            "step_history": [
                {"step": 1, "loss": 1.0, "accuracy": 0.5, "grad_norm": 0.9},
                {"step": 2, "loss": 2.5, "accuracy": 0.1, "grad_norm": 1.0},
            ],
        },
        "knowledge_distillation": {
            "status": "complete",
            "temperature": 4.0,
            "alpha": 0.5,
            "epochs_completed": 2,
            "epochs_requested": 2,
            "initial_retained_accuracy": 0.7,
            "final_retained_accuracy": 0.88,
            "per_client_accuracy_before": {"0": 0.7, "1": 0.7, "3": 0.7},
            "per_client_accuracy_after": {"0": 0.88, "1": 0.88, "3": 0.88},
            "epoch_history": [
                {"epoch": 1, "kd_loss": 0.9, "retained_accuracy": 0.8},
                {"epoch": 2, "kd_loss": 0.5, "retained_accuracy": 0.88},
            ],
        },
        "duration_seconds": 12.5,
    }
    if hyperparameters:
        status["method"] = "gradient_ascent+knowledge_distillation"
        status["hyperparameters"] = {
            "gradient_ascent": {"steps": 2, "lr": 0.01, "batch_size": 32},
            "knowledge_distillation": {"epochs": 2, "lr": 0.01, "temperature": 4.0, "alpha": 0.5, "batch_size": 64},
        }
        status["software"] = {"project_version": "1.0.0", "git_commit": "abc1234"}
    (d / "unlearning_status.json").write_text(json.dumps(status))
    (d / "unlearning_ga_model.pt").write_bytes(b"x")
    (d / "unlearning_final_model.pt").write_bytes(b"x")

    (d / "evaluation_results.json").write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "target_client_id": 2,
                "before": _metrics(0.9, 0.95, 0.9, 0.8),
                "after": _metrics(0.85, 0.1, 0.88, 0.5),
                "runtime": {
                    "gradient_ascent_seconds": 5.0,
                    "knowledge_distillation_seconds": 7.5,
                    "total_unlearning_seconds": 12.5,
                },
                "status": "complete",
            }
        )
    )
    (d / "retraining_results.json").write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "target_client_id": 2,
                "excluded_client_ids": [2],
                "protocol": {"rounds": 3, "local_epochs": 1, "seed": 42},
                "metrics": _metrics(0.86, 0.09, 0.87, 0.5),
                "runtime": {"retraining_seconds": 40.0},
                "status": "complete",
            }
        )
    )
    return d


def _statuses(report):
    return {c["id"]: c["status"] for c in report["checks"]}


def _edit(path: Path, mutate):
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


# -- The happy path ---------------------------------------------------------


def test_complete_experiment_passes_everything(tmp_path):
    make_experiment(tmp_path)
    report = validate_experiment("exp-ok", tmp_path)
    assert report["ok"] is True
    assert report["summary"]["failed"] == 0
    assert report["summary"]["warnings"] == 0
    assert all(c["status"] == PASS for c in report["checks"])


def test_pre_phase15_run_warns_but_does_not_fail(tmp_path):
    # An older unlearning run has no recorded hyperparameters/software.
    make_experiment(tmp_path, hyperparameters=False)
    report = validate_experiment("exp-ok", tmp_path)
    assert report["ok"] is True
    assert _statuses(report)["unlearning_hyperparameters"] == WARN


def test_missing_experiment_fails(tmp_path):
    report = validate_experiment("does-not-exist", tmp_path)
    assert report["ok"] is False
    assert _statuses(report)["experiment_exists"] == FAIL


# -- Things that must be caught (Ch.39 "must NOT happen") ------------------


def test_missing_artifacts_fail_clearly(tmp_path):
    d = make_experiment(tmp_path)
    (d / "retraining_results.json").unlink()
    (d / "global_model.pt").unlink()
    report = validate_experiment("exp-ok", tmp_path)
    st = _statuses(report)
    assert st["baseline_present"] == FAIL
    assert st["global_checkpoint"] == FAIL
    assert report["ok"] is False


def test_corrupt_json_is_reported_not_raised(tmp_path):
    d = make_experiment(tmp_path)
    (d / "evaluation_results.json").write_text('{"status": "comp')  # killed mid-write
    report = validate_experiment("exp-ok", tmp_path)
    assert _statuses(report)["results_present"] == FAIL
    detail = next(c["detail"] for c in report["checks"] if c["id"] == "results_present")
    assert "unreadable" in detail


def test_incomplete_evaluation_is_not_accepted_as_a_result(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "evaluation_results.json", lambda r: r.update(status="running"))
    report = validate_experiment("exp-ok", tmp_path)
    assert _statuses(report)["results_complete"] == FAIL
    assert report["ok"] is False


@pytest.mark.parametrize("bad_value", [1.5, -0.1, None, "0.9"])
def test_metric_must_be_a_real_probability(tmp_path, bad_value):
    d = make_experiment(tmp_path)
    _edit(d / "evaluation_results.json", lambda r: r["after"].update(mia_success=bad_value))
    assert _statuses(validate_experiment("exp-ok", tmp_path))["after_metrics"] == FAIL


def test_missing_metric_fails(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "retraining_results.json", lambda r: r["metrics"].pop("mia_success"))
    assert _statuses(validate_experiment("exp-ok", tmp_path))["retrained_metrics"] == FAIL


def test_runtime_must_be_measured(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "retraining_results.json", lambda r: r["runtime"].update(retraining_seconds=None))
    _edit(d / "evaluation_results.json", lambda r: r["runtime"].update(total_unlearning_seconds=0))
    st = _statuses(validate_experiment("exp-ok", tmp_path))
    assert st["retraining_runtime"] == FAIL
    assert st["runtime_measured"] == FAIL


def test_partition_must_cover_dataset_exactly_once(tmp_path):
    d = make_experiment(tmp_path)
    # Client 1 now shares a sample with client 0.
    def overlap(p):
        p["clients"][1]["indices"] = [0, 3]

    _edit(d / "partition.json", overlap)
    assert _statuses(validate_experiment("exp-ok", tmp_path))["partition_covers_dataset"] == FAIL


def test_round_count_must_match(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "fl_history.json", lambda h: h.update(rounds=5))
    assert _statuses(validate_experiment("exp-ok", tmp_path))["round_count"] == FAIL


def test_retraining_must_exclude_target_and_reuse_protocol(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "retraining_results.json", lambda r: r.update(excluded_client_ids=[0]))
    _edit(d / "retraining_results.json", lambda r: r["protocol"].update(seed=7))
    st = _statuses(validate_experiment("exp-ok", tmp_path))
    assert st["target_excluded"] == FAIL
    assert st["same_protocol"] == FAIL


def test_baseline_for_a_different_client_is_rejected(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "retraining_results.json", lambda r: r.update(target_client_id=1, excluded_client_ids=[1]))
    assert _statuses(validate_experiment("exp-ok", tmp_path))["baseline_matches_target"] == FAIL


def test_failed_unlearning_run_is_reported_with_its_error(tmp_path):
    d = make_experiment(tmp_path)
    _edit(
        d / "unlearning_status.json",
        lambda s: s.update(status="failed", stage="gradient_ascent", error="out of memory"),
    )
    report = validate_experiment("exp-ok", tmp_path)
    check = next(c for c in report["checks"] if c["id"] == "status_complete")
    assert check["status"] == FAIL
    assert "out of memory" in check["detail"]


def test_target_client_must_exist(tmp_path):
    d = make_experiment(tmp_path)
    _edit(d / "unlearning_status.json", lambda s: s.update(target_client_id=9))
    assert _statuses(validate_experiment("exp-ok", tmp_path))["target_valid"] == FAIL


# -- CLI ---------------------------------------------------------------------


def test_cli_exit_codes(tmp_path, monkeypatch, capsys):
    from core.acceptance import cli

    monkeypatch.setattr(checks, "EXPERIMENTS_DIR", tmp_path)
    make_experiment(tmp_path, "good")
    assert cli.main(["--experiment-id", "good"]) == 0

    bad = make_experiment(tmp_path, "bad")
    (bad / "retraining_results.json").unlink()
    assert cli.main(["--experiment-id", "bad"]) == 1
    assert cli.main(["--all"]) == 1  # one failing experiment fails the batch

    capsys.readouterr()
    cli.main(["--experiment-id", "good", "--json"])
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["ok"] is True and parsed["reports"][0]["experiment_id"] == "good"


def test_cli_with_no_experiments_is_an_error(tmp_path, monkeypatch):
    from core.acceptance import cli

    monkeypatch.setattr(checks, "EXPERIMENTS_DIR", tmp_path)
    assert cli.main(["--all"]) == 1


# -- Provenance ----------------------------------------------------------------


def test_software_info_shape():
    info = provenance.software_info()
    assert info["project_version"] == provenance.PROJECT_VERSION
    assert info["python"]
    assert set(info) == {"project_version", "git_commit", "python", "torch", "numpy"}


def test_software_info_never_raises_without_git(monkeypatch):
    def no_git(*a, **k):
        raise FileNotFoundError("git not installed")

    provenance._git_commit.cache_clear()
    monkeypatch.setattr(provenance.subprocess, "run", no_git)
    try:
        info = provenance.software_info()
        assert info["git_commit"] is None  # reported as unknown, never invented
    finally:
        provenance._git_commit.cache_clear()


def test_acceptance_cli_runs_as_a_module_without_torch():
    # The checker must work on a machine with no torch at all.
    root = Path(__file__).resolve().parents[1]
    out = subprocess.run(
        [sys.executable, "-m", "core.acceptance.cli", "--experiment-id", "definitely-not-real"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert out.returncode == 1
    assert "experiment_exists" not in out.stderr  # no traceback
    assert "Traceback" not in out.stderr
