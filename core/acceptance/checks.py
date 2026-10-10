"""Machine-checkable parts of the Final Acceptance Checklist (Ch.70).

Much of Ch.70 is about what the *dashboard shows* ("Heatmap
available", "Projector-friendly") and can only be judged by a person
looking at it -- those are covered by docs/ACCEPTANCE_CHECKLIST.md. But
the parts that are about *the data behind the screens* can be checked
by a program, and that is what this module does for one stored
experiment:

* every artifact the research story needs exists and is complete;
* the numbers are internally consistent (the partition really covers
  the dataset once, round counts match, accuracies are real
  probabilities, the retraining baseline really excluded the target and
  used the original protocol);
* nothing is fabricated or half-finished (Ch.39: no invented metrics,
  no "complete" results with missing metrics, no speedup without a
  measured runtime);
* the reproducibility record (Ch.44) is present.

It reads JSON only -- no torch, no GPU, no network -- so it runs
anywhere, including a laptop with no backend reachable, and it is safe
to run on the day of a demonstration.

Each check returns one of:
    pass  the artifact satisfies the requirement
    fail  the requirement is violated (or the artifact is missing)
    warn  not violated, but not fully recorded -- e.g. a run made
          before Phase 15 that predates the hyperparameter record
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

EXPERIMENTS_DIR = Path(__file__).resolve().parents[2] / "experiments"

PASS, FAIL, WARN = "pass", "fail", "warn"

#: The four per-model metrics every results screen shows (Ch.22).
METRIC_KEYS = ("global_accuracy", "forget_client_accuracy", "retained_client_accuracy", "mia_success")


def _load(directory: Path, name: str) -> tuple[Any | None, str | None]:
    """(data, problem). problem is None when the file loaded fine."""
    path = directory / name
    if not path.exists():
        return None, f"{name} is missing"
    try:
        return json.loads(path.read_text()), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{name} is unreadable ({exc.__class__.__name__})"


def _is_probability(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class _Report:
    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id
        self.checks: list[dict[str, str]] = []

    def add(self, section: str, check_id: str, description: str, status: str, detail: str = "") -> None:
        self.checks.append(
            {"section": section, "id": check_id, "description": description, "status": status, "detail": detail}
        )

    def ok(self, section: str, check_id: str, description: str, detail: str = "") -> None:
        self.add(section, check_id, description, PASS, detail)

    def bad(self, section: str, check_id: str, description: str, detail: str) -> None:
        self.add(section, check_id, description, FAIL, detail)

    def warn(self, section: str, check_id: str, description: str, detail: str) -> None:
        self.add(section, check_id, description, WARN, detail)

    def result(self) -> dict[str, Any]:
        counts = {PASS: 0, FAIL: 0, WARN: 0}
        for c in self.checks:
            counts[c["status"]] += 1
        return {
            "experiment_id": self.experiment_id,
            "checks": self.checks,
            "summary": {"passed": counts[PASS], "failed": counts[FAIL], "warnings": counts[WARN]},
            "ok": counts[FAIL] == 0,
        }


# -- Section checks ---------------------------------------------------------


def _check_partition(r: _Report, d: Path) -> dict | None:
    sec = "Data Distribution"
    partition, problem = _load(d, "partition.json")
    if problem:
        r.bad(sec, "partition_present", "Dataset partitioning is stored", problem)
        return None
    r.ok(sec, "partition_present", "Dataset partitioning is stored")

    clients = partition.get("clients") or []
    n = partition.get("num_clients")
    if len(clients) == n and n and n >= 2:
        r.ok(sec, "client_list", "Client list visible: one entry per configured client", f"{n} clients")
    else:
        r.bad(sec, "client_list", "Client list visible: one entry per configured client",
              f"num_clients={n} but {len(clients)} client entries")

    if partition.get("strategy") in ("iid", "non_iid"):
        r.ok(sec, "iid_flag", "IID / Non-IID is recorded", partition["strategy"])
    else:
        r.bad(sec, "iid_flag", "IID / Non-IID is recorded", f"strategy={partition.get('strategy')!r}")

    bad_counts = [
        c.get("client_id")
        for c in clients
        if c.get("num_samples") != len(c.get("indices", [])) or sum((c.get("class_counts") or {}).values()) != c.get("num_samples")
    ]
    if clients and not bad_counts:
        r.ok(sec, "samples_per_client", "Samples/client and class distribution are consistent")
    else:
        r.bad(sec, "samples_per_client", "Samples/client and class distribution are consistent",
              f"inconsistent counts for client(s) {bad_counts}" if bad_counts else "no clients")

    all_indices = [i for c in clients for i in c.get("indices", [])]
    total = partition.get("total_samples")
    if len(all_indices) == len(set(all_indices)) == total:
        r.ok(sec, "partition_covers_dataset", "Every training sample belongs to exactly one client",
             f"{total} samples")
    else:
        r.bad(sec, "partition_covers_dataset", "Every training sample belongs to exactly one client",
              f"{len(all_indices)} assigned, {len(set(all_indices))} unique, {total} expected")
    return partition


def _check_training(r: _Report, d: Path, partition: dict | None) -> dict | None:
    sec = "Federated Learning"
    history, problem = _load(d, "fl_history.json")
    if problem:
        r.bad(sec, "history_present", "Round-by-round training history is stored", problem)
        return None
    r.ok(sec, "history_present", "Round-by-round training history is stored")

    rounds = history.get("round_history") or []
    if history.get("rounds") == len(rounds) and rounds:
        r.ok(sec, "round_count", "Round progression: stored rounds match the configured count", f"{len(rounds)} rounds")
    else:
        r.bad(sec, "round_count", "Round progression: stored rounds match the configured count",
              f"rounds={history.get('rounds')} but {len(rounds)} stored")

    bad_round = next(
        (
            x.get("round")
            for x in rounds
            if not _is_probability(x.get("accuracy")) or not _is_number(x.get("loss")) or not x.get("clients")
        ),
        None,
    )
    if rounds and bad_round is None:
        r.ok(sec, "charts_data", "Accuracy and loss are real numbers for every round, with per-client updates")
    else:
        r.bad(sec, "charts_data", "Accuracy and loss are real numbers for every round, with per-client updates",
              f"round {bad_round} has a missing/invalid accuracy, loss or client list" if rounds else "no rounds")

    if rounds and history.get("final_accuracy") == rounds[-1].get("accuracy"):
        r.ok(sec, "final_matches_last_round", "Reported final accuracy equals the last round's accuracy")
    else:
        r.bad(sec, "final_matches_last_round", "Reported final accuracy equals the last round's accuracy",
              f"final_accuracy={history.get('final_accuracy')}")

    if (d / "global_model.pt").exists():
        r.ok(sec, "global_checkpoint", "Global checkpoint is stored")
    else:
        r.bad(sec, "global_checkpoint", "Global checkpoint is stored", "global_model.pt is missing")

    if partition is not None and history.get("num_clients") not in (None, partition.get("num_clients")):
        r.bad(sec, "training_matches_partition", "Training used the stored partition",
              f"history num_clients={history.get('num_clients')} vs partition {partition.get('num_clients')}")
    else:
        r.ok(sec, "training_matches_partition", "Training used the stored partition")
    return history


def _check_unlearning(r: _Report, d: Path, partition: dict | None) -> dict | None:
    sec = "Unlearning"
    status, problem = _load(d, "unlearning_status.json")
    if problem:
        r.bad(sec, "status_present", "Unlearning run is stored", problem)
        return None
    if status.get("status") != "complete":
        r.bad(sec, "status_complete", "Unlearning run completed",
              f"status={status.get('status')!r}" + (f", error: {status['error']}" if status.get("error") else ""))
        return status
    r.ok(sec, "status_complete", "Unlearning run completed")

    target = status.get("target_client_id")
    n = (partition or {}).get("num_clients")
    if isinstance(target, int) and (n is None or 0 <= target < n):
        r.ok(sec, "target_valid", "Target client exists in this experiment", f"Client {target}")
    else:
        r.bad(sec, "target_valid", "Target client exists in this experiment", f"target_client_id={target!r}, clients={n}")

    ga = status.get("gradient_ascent") or {}
    ga_steps = ga.get("step_history") or []
    if ga.get("status") == "complete" and ga_steps and len(ga_steps) == ga.get("steps_completed"):
        r.ok(sec, "ga_progress", "Gradient Ascent progress and metrics are stored", f"{len(ga_steps)} steps")
    else:
        r.bad(sec, "ga_progress", "Gradient Ascent progress and metrics are stored",
              f"steps_completed={ga.get('steps_completed')}, step_history has {len(ga_steps)}")

    kd = status.get("knowledge_distillation") or {}
    kd_epochs = kd.get("epoch_history") or []
    if kd.get("status") == "complete" and kd_epochs and len(kd_epochs) == kd.get("epochs_completed"):
        r.ok(sec, "kd_progress", "Knowledge Distillation progress and loss are stored", f"{len(kd_epochs)} epochs")
    else:
        r.bad(sec, "kd_progress", "Knowledge Distillation progress and loss are stored",
              f"epochs_completed={kd.get('epochs_completed')}, epoch_history has {len(kd_epochs)}")

    missing = [n for n in ("unlearning_ga_model.pt", "unlearning_final_model.pt") if not (d / n).exists()]
    if missing:
        r.bad(sec, "unlearned_model", "Unlearned model checkpoints are stored", f"missing: {', '.join(missing)}")
    else:
        r.ok(sec, "unlearned_model", "Unlearned model checkpoints are stored")
    return status


def _check_metrics_block(r: _Report, sec: str, check_id: str, label: str, block: Any) -> None:
    if not isinstance(block, dict):
        r.bad(sec, check_id, label, "block is missing")
        return
    missing = [k for k in METRIC_KEYS if k not in block]
    invalid = [k for k in METRIC_KEYS if k in block and not _is_probability(block[k])]
    if missing or invalid:
        r.bad(sec, check_id, label, f"missing: {missing or 'none'}; not a valid 0..1 value: {invalid or 'none'}")
    else:
        r.ok(sec, check_id, label)


def _check_evaluation(r: _Report, d: Path, unlearning: dict | None) -> dict | None:
    sec = "Evaluation"
    results, problem = _load(d, "evaluation_results.json")
    if problem:
        r.bad(sec, "results_present", "Evaluation results are stored", problem)
        return None
    if results.get("status") != "complete":
        r.bad(sec, "results_complete",
              "Evaluation is complete (incomplete metrics must never be shown as final results)",
              f"status={results.get('status')!r}")
        return results
    r.ok(sec, "results_complete", "Evaluation is complete")

    _check_metrics_block(r, sec, "before_metrics", "Original model: global, forget-client, retained-client accuracy and MIA", results.get("before"))
    _check_metrics_block(r, sec, "after_metrics", "Unlearned model: global, forget-client, retained-client accuracy and MIA", results.get("after"))

    runtime = results.get("runtime") or {}
    if _is_number(runtime.get("total_unlearning_seconds")) and runtime["total_unlearning_seconds"] > 0:
        r.ok(sec, "runtime_measured", "Unlearning runtime is a measured value", f"{runtime['total_unlearning_seconds']:.1f}s")
    else:
        r.bad(sec, "runtime_measured", "Unlearning runtime is a measured value",
              f"total_unlearning_seconds={runtime.get('total_unlearning_seconds')!r}")

    if unlearning and results.get("target_client_id") != unlearning.get("target_client_id"):
        r.bad(sec, "evaluation_matches_unlearning", "Evaluation is for the client that was unlearned",
              f"evaluated client {results.get('target_client_id')} vs unlearned client {unlearning.get('target_client_id')}")
    else:
        r.ok(sec, "evaluation_matches_unlearning", "Evaluation is for the client that was unlearned")
    return results


def _check_retraining(r: _Report, d: Path, history: dict | None, evaluation: dict | None) -> None:
    sec = "Research Comparison"
    retraining, problem = _load(d, "retraining_results.json")
    if problem:
        r.bad(sec, "baseline_present", "Full-retraining baseline is stored", problem)
        return
    if retraining.get("status") != "complete":
        r.bad(sec, "baseline_complete", "Full-retraining baseline is complete", f"status={retraining.get('status')!r}")
        return
    r.ok(sec, "baseline_complete", "Full-retraining baseline is complete")

    _check_metrics_block(r, sec, "retrained_metrics", "Retrained model: accuracy, forgetting and MIA are all present", retraining.get("metrics"))

    rt = (retraining.get("runtime") or {}).get("retraining_seconds")
    if _is_number(rt) and rt > 0:
        r.ok(sec, "retraining_runtime", "Retraining runtime is a measured value", f"{rt:.1f}s")
    else:
        r.bad(sec, "retraining_runtime", "Retraining runtime is a measured value", f"retraining_seconds={rt!r}")

    target = retraining.get("target_client_id")
    if target is not None and target in (retraining.get("excluded_client_ids") or []):
        r.ok(sec, "target_excluded", "The retrained model really excluded the target client", f"Client {target}")
    else:
        r.bad(sec, "target_excluded", "The retrained model really excluded the target client",
              f"target={target!r}, excluded={retraining.get('excluded_client_ids')!r}")

    if evaluation and evaluation.get("target_client_id") != target:
        r.bad(sec, "baseline_matches_target", "Baseline and evaluation are for the same target client",
              f"baseline client {target} vs evaluation client {evaluation.get('target_client_id')}")
    else:
        r.ok(sec, "baseline_matches_target", "Baseline and evaluation are for the same target client")

    if history:
        proto = retraining.get("protocol") or {}
        diffs = [
            f"{k}: original {history.get(h)!r} vs retrain {proto.get(k)!r}"
            for k, h in (("rounds", "rounds"), ("local_epochs", "local_epochs"), ("seed", "seed"))
            if proto.get(k) != history.get(h)
        ]
        if diffs:
            r.bad(sec, "same_protocol", "Retraining reused the original training protocol", "; ".join(diffs))
        else:
            r.ok(sec, "same_protocol", "Retraining reused the original training protocol")


def _check_reproducibility(r: _Report, partition: dict | None, history: dict | None, unlearning: dict | None) -> None:
    sec = "Reproducibility"
    fields = {
        "dataset": (history or {}).get("dataset") or (partition or {}).get("dataset"),
        "num_clients": (partition or {}).get("num_clients"),
        "partition strategy": (partition or {}).get("strategy"),
        "seed": (history or {}).get("seed"),
        "model": (history or {}).get("model"),
        "federated rounds": (history or {}).get("rounds"),
        "local epochs": (history or {}).get("local_epochs"),
    }
    missing = [k for k, v in fields.items() if v is None]
    if missing:
        r.bad(sec, "core_config", "Dataset, clients, partition, seed, model, rounds and local epochs are stored",
              f"missing: {', '.join(missing)}")
    else:
        r.ok(sec, "core_config", "Dataset, clients, partition, seed, model, rounds and local epochs are stored")

    if unlearning and unlearning.get("hyperparameters") and unlearning.get("software"):
        r.ok(sec, "unlearning_hyperparameters", "Unlearning hyperparameters and software version are stored",
             f"commit {unlearning['software'].get('git_commit') or 'unknown'}")
    elif unlearning:
        r.warn(sec, "unlearning_hyperparameters", "Unlearning hyperparameters and software version are stored",
               "not recorded -- this run was made before Phase 15; re-run unlearning to record them")


def validate_experiment(experiment_id: str, experiments_dir: Path | None = None) -> dict[str, Any]:
    """Run every machine-checkable acceptance check for one experiment."""
    base = Path(experiments_dir) if experiments_dir else EXPERIMENTS_DIR
    d = base / experiment_id
    report = _Report(experiment_id)
    if not d.is_dir():
        report.bad("Experiment", "experiment_exists", "Experiment exists", f"no folder at experiments/{experiment_id}")
        return report.result()

    partition = _check_partition(report, d)
    history = _check_training(report, d, partition)
    unlearning = _check_unlearning(report, d, partition)
    evaluation = _check_evaluation(report, d, unlearning)
    _check_retraining(report, d, history, evaluation)
    _check_reproducibility(report, partition, history, unlearning)
    return report.result()


def list_experiment_ids(experiments_dir: Path | None = None) -> list[str]:
    base = Path(experiments_dir) if experiments_dir else EXPERIMENTS_DIR
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())
