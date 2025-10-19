from dataclasses import dataclass


@dataclass
class ProgressRecord:
    task_id: str
    progress: float = 0.0 # 0..100
    status: str = "pending" # pending, in_progress, finished, failed