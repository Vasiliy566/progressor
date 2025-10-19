from abc import ABC, abstractmethod

from progressorx.models import ProgressRecord


class ProgressStore(ABC):
    """Abstract storage backend for progress records."""
    @abstractmethod
    def create(self, task_id: str, progress: float | int = 0.0, status: str = "in_progress") -> ProgressRecord:
        raise NotImplementedError


    @abstractmethod
    def set(self, task_id: str, progress: float, status: str | None = None) -> ProgressRecord:
        raise NotImplementedError


    @abstractmethod
    def increment(self, task_id: str, delta: float) -> ProgressRecord:
        raise NotImplementedError


    @abstractmethod
    def get(self, task_id: str) -> ProgressRecord:
        raise NotImplementedError


    @abstractmethod
    def delete(self, task_id: str) -> None:
        raise NotImplementedError