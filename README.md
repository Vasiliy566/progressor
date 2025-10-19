# progressorx


`progressor` — lightweight progress-tracking package for long-running tasks.


Features:
- `report_progress(task_id, progress=None, increase=None)` — set or increment progress (0..100).
- `get_progress(task_id)` — get current progress and status.
- Pluggable backends: InMemory, Redis, SQLAlchemy (SQLite/Postgres).
- Thread/process/distributed safe when using a proper backend (Redis/SQL).


## Quick example
```python
from progressorx import ProgressManager
from progressorx.backends.memory import InMemoryStore


store = InMemoryStore()
mgr = ProgressManager(store)


mgr.report_progress('task-1', progress=10)
mgr.report_progress('task-1', increase=5)
print(mgr.get_progress('task-1')) # {'task_id': 'task-1', 'progress': 15, 'status': 'in_progress'}
```


See examples/fastapi_example.py for how to integrate with FastAPI.
