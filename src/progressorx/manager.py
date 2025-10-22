from progressorx.models import ProgressRecord
from progressorx.store import ProgressStore


class ProgressManager:
    """Facade over a ProgressStore

    Public API:
    - report_progress(task_id, progress=None, increase=None)
    - get_progress(task_id) -> dict or None
    """

    def __init__(self, store: ProgressStore):
        self.store: ProgressStore = store

    def create(self, task_id: str, *, progress: float | int = 0.0, status: str = "in_progress"):
        return self.store.create(task_id, progress, status)

    def report_progress(self, task_id: str, *, progress: int | float = None,
                        increase: int | float = None) -> ProgressRecord:
        if progress is None and increase is None:
            raise ValueError("Either progress or increase must be provided")
        if progress is not None and increase is not None:
            raise ValueError("Only one of progress or increase must be provided")

        if progress is not None:
            return self.store.set(task_id, progress)
        return self.store.increment(task_id, increase)

    def set_failed(self, task_id: str, ):
        return self.store.set(task_id, progress=0, status="failed")

    def get_progress(self, task_id: str) -> ProgressRecord:
        return self.store.get(task_id)
