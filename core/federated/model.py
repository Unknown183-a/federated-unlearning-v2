"""Model architectures for the federated learning engine (Phase 05).

A single small CNN, parameterized from a dataset's manifest metadata
(channels, image_size, num_classes) so the same code trains on MNIST,
CIFAR-10, or CIFAR-100 without per-dataset branching. An adaptive
pooling layer absorbs the 28x28 vs 32x32 input-size difference.

`model_id="resnet"` is accepted (it's one of the two choices in the
experiment config, Ch.34) but currently maps to the same small CNN --
a real ResNet is out of scope for Phase 05, whose acceptance criteria
only require converging on MNIST with a working FedAvg loop.
"""
from __future__ import annotations

import torch
from torch import nn


class SmallCNN(nn.Module):
    """Two conv blocks + a linear head. Small enough to train fast on CPU."""

    def __init__(self, channels: int, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(channels, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Fixes the spatial size regardless of 28x28 vs 32x32 input.
            nn.AdaptiveAvgPool2d((7, 7)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


def build_model(model_id: str, channels: int, num_classes: int) -> nn.Module:
    """Factory: look up a model implementation by experiment-config id.

    Both "cnn" and "resnet" currently build the same SmallCNN -- see
    the module docstring for why.
    """
    if model_id not in ("cnn", "resnet"):
        raise ValueError(f"Unknown model id '{model_id}' (expected 'cnn' or 'resnet')")
    return SmallCNN(channels=channels, num_classes=num_classes)
