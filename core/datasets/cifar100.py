"""CIFAR-100 dataset loader (Phase 01)."""
from core.datasets.base import Dataset


class CIFAR100Dataset(Dataset):
    id = "cifar100"

    def get_train(self):
        from torchvision import datasets, transforms

        return datasets.CIFAR100(
            root="./data", train=True, download=True, transform=transforms.ToTensor()
        )

    def get_test(self):
        from torchvision import datasets, transforms

        return datasets.CIFAR100(
            root="./data", train=False, download=True, transform=transforms.ToTensor()
        )
