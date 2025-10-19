from progressorx.models import ProgressRecord
from progressorx.exceptions import RecordNotFoundError, IncorrectProgressValueError
from progressorx.store import ProgressStore


class InMemoryStore(ProgressStore):
    """Simple in-memory store. Not for production, useful for tests and single-process usage."""

    def __init__(self):
        self._data: dict[str, ProgressRecord] = {}

    def create(self, task_id: str, progress: float | int = 0.0, status: str = "in_progress") -> ProgressRecord:
        self._data[task_id] = ProgressRecord(task_id, progress, status)
        return self.get(task_id)

    def get(self, task_id: str) -> ProgressRecord:
        try:
            return self._data[task_id]
        except KeyError:
            raise RecordNotFoundError

    def set(self, task_id: str, progress: float, status: str | None = None) -> ProgressRecord:
        if progress < 0.0 or progress > 100.0:
            raise IncorrectProgressValueError
        rec = self.get(task_id)
        rec.progress = progress
        rec.status = status or ("finished" if progress >= 100.0 else "in_progress")
        self._data[task_id] = rec
        return rec

    def increment(self, task_id: str, delta: float) -> ProgressRecord:
        rec = self.get(task_id)
        new_progress = rec.progress + delta
        if new_progress < 0.0 or new_progress > 100.0:
            raise IncorrectProgressValueError
        return self.set(task_id, new_progress)

    def delete(self, task_id: str) -> None:
        self._data.pop(task_id, None)
