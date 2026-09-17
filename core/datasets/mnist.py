"""MNIST dataset loader (Phase 01)."""
from core.datasets.base import Dataset


class MNISTDataset(Dataset):
    id = "mnist"

    def get_train(self):
        # Imported lazily so metadata-only callers don't need torchvision.
        from torchvision import datasets, transforms

        return datasets.MNIST(
            root="./data", train=True, download=True, transform=transforms.ToTensor()
        )

    def get_test(self):
        from torchvision import datasets, transforms

        return datasets.MNIST(
            root="./data", train=False, download=True, transform=transforms.ToTensor()
        )
