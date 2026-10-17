import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

torch = pytest.importorskip("torch")

from torch.utils.data import TensorDataset

from core.federated.model import build_model
from core.unlearning.calibration import CalibrationConfig, ks_distance
from core.unlearning.gradient_ascent import run_gradient_ascent


def _dataset(num_samples=120, num_classes=3, seed=0):
    g = torch.Generator().manual_seed(seed)
    images = torch.randn(num_samples, 1, 8, 8, generator=g)
    labels = torch.randint(0, num_classes, (num_samples,), generator=g)
    return TensorDataset(images, labels)


def test_ks_distance_identical_samples_is_zero():
    a = torch.rand(200, generator=torch.Generator().manual_seed(1))
    assert ks_distance(a, a.clone()) == pytest.approx(0.0)


def test_ks_distance_disjoint_samples_is_one():
    assert ks_distance(torch.zeros(50), torch.ones(50)) == pytest.approx(1.0)


def test_ks_distance_rejects_empty():
    with pytest.raises(ValueError):
        ks_distance(torch.empty(0), torch.ones(3))


def _fit(model, dataset, indices, epochs=60):
    opt = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9)
    loss_fn = torch.nn.CrossEntropyLoss()
    images = torch.stack([dataset[i][0] for i in indices])
    labels = torch.tensor([dataset[i][1] for i in indices])
    for _ in range(epochs):
        opt.zero_grad()
        loss_fn(model(images), labels).backward()
        opt.step()


def _setup():
    dataset = _dataset()
    target = list(range(0, 40))
    reference = list(range(80, 120))
    model = build_model("cnn", channels=1, num_classes=3)
    _fit(model, dataset, target)  # memorise the target samples
    return dataset, target, reference, model


def test_calibrated_ascent_reports_reason_and_selected_step():
    dataset, target, reference, model = _setup()
    cfg = CalibrationConfig(reference_dataset=dataset, reference_indices=reference, ks_target=0.2)
    result = run_gradient_ascent(
        global_state=model.state_dict(), model_id="cnn", channels=1, num_classes=3,
        dataset=dataset, target_indices=target, steps=30, lr=0.01, calibration=cfg,
    )
    cal = result["calibration"]
    assert cal["stop_reason"] in {
        "already_calibrated", "ks_target_reached", "ks_no_improvement",
        "retain_guard", "step_budget_exhausted",
    }
    assert cal["selected_ks_distance"] <= cal["initial_ks_distance"] + 1e-9
    assert 0 <= cal["selected_step"] <= result["steps_completed"]


def test_calibrated_ascent_never_returns_worse_ks_than_start():
    dataset, target, reference, model = _setup()
    cfg = CalibrationConfig(reference_dataset=dataset, reference_indices=reference, ks_target=0.0)
    result = run_gradient_ascent(
        global_state=model.state_dict(), model_id="cnn", channels=1, num_classes=3,
        dataset=dataset, target_indices=target, steps=15, lr=0.01, calibration=cfg,
    )
    assert result["calibration"]["selected_ks_distance"] <= result["calibration"]["initial_ks_distance"] + 1e-9


def test_retain_guard_rolls_back_when_tolerance_is_zero_and_accuracy_drops():
    dataset, target, reference, model = _setup()
    cfg = CalibrationConfig(
        reference_dataset=dataset, reference_indices=reference,
        guard_dataset=dataset, guard_indices=list(range(40, 80)),
        ks_target=0.0, max_retain_drop=0.0, patience=100,
    )
    result = run_gradient_ascent(
        global_state=model.state_dict(), model_id="cnn", channels=1, num_classes=3,
        dataset=dataset, target_indices=target, steps=30, lr=0.05, calibration=cfg,
    )
    assert result["calibration"]["stop_reason"] in {"retain_guard", "step_budget_exhausted", "already_calibrated"}


def test_empty_reference_is_rejected():
    dataset, target, _, model = _setup()
    cfg = CalibrationConfig(reference_dataset=dataset, reference_indices=[])
    with pytest.raises(ValueError):
        run_gradient_ascent(
            global_state=model.state_dict(), model_id="cnn", channels=1, num_classes=3,
            dataset=dataset, target_indices=target, steps=5, calibration=cfg,
        )


def test_without_calibration_result_has_no_calibration_key():
    dataset, target, _, model = _setup()
    result = run_gradient_ascent(
        global_state=model.state_dict(), model_id="cnn", channels=1, num_classes=3,
        dataset=dataset, target_indices=target, steps=3,
    )
    assert "calibration" not in result
