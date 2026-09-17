"""Dataset interface (Dashboard Spec Ch.3-5, Phase 01).

Every dataset (MNIST, CIFAR-10, CIFAR-100, and anything added later)
implements this interface. Metadata comes from manifest.json so the
backend can serve it without importing torch/torchvision at all --
those heavy deps are only needed once someone actually calls
get_train()/get_test().
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent / "manifest.json"


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


class Dataset(ABC):
    """Interface every dataset loader implements."""

    #: manifest key, e.g. "mnist" -- set by subclasses
    id: str

    def get_metadata(self) -> dict:
        """Return this dataset's entry from manifest.json.

        No heavy imports required -- safe to call even if torch/
        torchvision aren't installed yet.
        """
        manifest = load_manifest()
        if self.id not in manifest:
            raise KeyError(f"No manifest entry for dataset id '{self.id}'")
        return manifest[self.id]

    @abstractmethod
    def get_train(self):
        """Return the training split. Requires torch/torchvision."""
        raise NotImplementedError

    @abstractmethod
    def get_test(self):
        """Return the test split. Requires torch/torchvision."""
        raise NotImplementedError


def get_dataset(dataset_id: str) -> Dataset:
    """Factory: look up a Dataset implementation by manifest id."""
    # Local imports: keeps this module importable with zero
    # torch/torchvision installed for metadata-only use (e.g. the
    # backend's dataset picker endpoint, tested without ML deps).
    from core.datasets.mnist import MNISTDataset
    from core.datasets.cifar10 import CIFAR10Dataset
    from core.datasets.cifar100 import CIFAR100Dataset

    registry = {
        "mnist": MNISTDataset,
        "cifar10": CIFAR10Dataset,
        "cifar100": CIFAR100Dataset,
    }
    if dataset_id not in registry:
        raise KeyError(f"Unknown dataset id '{dataset_id}'")
    return registry[dataset_id]()
