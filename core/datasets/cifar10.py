"""CIFAR-10 dataset loader (Phase 01)."""
from core.datasets.base import Dataset


class CIFAR10Dataset(Dataset):
    id = "cifar10"

    def get_train(self):
        from torchvision import datasets, transforms

        return datasets.CIFAR10(
            root="./data", train=True, download=True, transform=transforms.ToTensor()
        )

    def get_test(self):
        from torchvision import datasets, transforms

        return datasets.CIFAR10(
            root="./data", train=False, download=True, transform=transforms.ToTensor()
        )
