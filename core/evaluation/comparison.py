"""Original vs Unlearned vs Retrained comparison (Phase 11, Ch.24-25, Ch.54).

Pure data: this reads the two stored artifacts -- Phase 10's
``evaluation_results.json`` (original + unlearned metrics, unlearning
runtime) and Phase 11's ``retraining_results.json`` (retrained metrics,
retraining runtime) -- and lines them up. It never trains or evaluates
anything, so it is cheap to call and needs no torch.

Honesty rules from the spec are enforced here rather than left to the UI:

* Every runtime number is a measured wall-clock time from a stored run.
  A speedup is only reported when both times exist, and if unlearning
  was *not* faster the result says so (negative time saved,
  ``unlearning_faster: False``) instead of being clamped or hidden
  (Ch.25: "Do not claim a speedup unless measured").
* Metrics that got worse are left as they are (Ch.23).
* The retrained numbers are labeled as coming from a separate run.
"""
from __future__ import annotations

from core.evaluation.storage import load_evaluation_results, load_retraining_results

#: (key in the metrics dicts, human label). Same four metrics as Page 7.
METRICS = [
    ("global_accuracy", "Global Accuracy"),
    ("forget_client_accuracy", "Forget-Client Accuracy"),
    ("retained_client_accuracy", "Retained-Client Accuracy"),
    ("mia_success", "MIA Success"),
]


def _model_row(metrics: dict) -> dict:
    return {key: metrics[key] for key, _ in METRICS}


def build_comparison(evaluation: dict, retraining: dict) -> dict:
    """Line up original / unlearned / retrained from two stored result dicts.

    Raises ValueError if the two artifacts don't describe the same
    experiment target (e.g. the user unlearned a different client after
    the baseline was run), since comparing them would be meaningless.
    """
    if evaluation.get("target_client_id") != retraining.get("target_client_id"):
        raise ValueError(
            f"Retraining baseline excludes client {retraining.get('target_client_id')} but the "
            f"stored evaluation is for client {evaluation.get('target_client_id')} -- "
            "re-run the retraining baseline for the current target"
        )

    original = _model_row(evaluation["before"])
    unlearned = _model_row(evaluation["after"])
    retrained = _model_row(retraining["metrics"])

    metrics = []
    for key, label in METRICS:
        gap_unlearned = unlearned[key] - retrained[key]
        gap_original = original[key] - retrained[key]
        metrics.append(
            {
                "key": key,
                "label": label,
                "original": original[key],
                "unlearned": unlearned[key],
                "retrained": retrained[key],
                # Signed distance to the retraining reference (the "ideal").
                "unlearned_minus_retrained": gap_unlearned,
                "original_minus_retrained": gap_original,
                # Did unlearning move this metric toward what retraining produced?
                "unlearned_closer_to_retrained": abs(gap_unlearned) < abs(gap_original),
            }
        )

    unlearning_seconds = (evaluation.get("runtime") or {}).get("total_unlearning_seconds")
    retraining_seconds = (retraining.get("runtime") or {}).get("retraining_seconds")
    original_training_seconds = (retraining.get("runtime") or {}).get("original_training_seconds")

    runtime = {
        "unlearning_seconds": unlearning_seconds,
        "retraining_seconds": retraining_seconds,
        "original_training_seconds": original_training_seconds,
        "time_saved_seconds": None,
        "time_saved_fraction": None,
        "speedup_factor": None,
        "unlearning_faster": None,
    }
    if unlearning_seconds is not None and retraining_seconds:
        saved = retraining_seconds - unlearning_seconds
        runtime["time_saved_seconds"] = saved
        runtime["time_saved_fraction"] = saved / retraining_seconds
        runtime["unlearning_faster"] = saved > 0
        if unlearning_seconds > 0:
            runtime["speedup_factor"] = retraining_seconds / unlearning_seconds

    return {
        "experiment_id": evaluation.get("experiment_id"),
        "target_client_id": evaluation.get("target_client_id"),
        "model": evaluation.get("model"),
        "dataset": evaluation.get("dataset"),
        "metrics": metrics,
        "runtime": runtime,
        "retraining_run": {
            "run_kind": retraining.get("run_kind", "separate_retraining_baseline"),
            "excluded_client_ids": retraining.get("excluded_client_ids", []),
            "num_clients_trained": retraining.get("num_clients_trained"),
            "protocol": retraining.get("protocol", {}),
        },
        "status": "complete",
    }


def compare_with_retraining(experiment_id: str) -> dict:
    """Load both stored artifacts for `experiment_id` and compare them.

    Mirrors the conceptual ``compare_with_retraining(unlearned_results,
    retraining_results)`` from the Dashboard Spec (Ch.36), mapped onto
    this repo's stored-artifact layout.

    Raises FileNotFoundError if evaluation (Phase 10) or the retraining
    baseline hasn't been run yet, or ValueError on a target mismatch.
    """
    evaluation = load_evaluation_results(experiment_id)
    retraining = load_retraining_results(experiment_id)
    return build_comparison(evaluation, retraining)
