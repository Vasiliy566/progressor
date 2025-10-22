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

# create task
mgr.create('task-1')

# set and increment progress
mgr.report_progress('task-1', progress=10)
mgr.report_progress('task-1', increase=5)

rec = mgr.get_progress('task-1')
print(rec.task_id, rec.progress, rec.status)  # task-1 15.0 in_progress
```

## Examples
- Basic runnable example: src/progressorx/examples/basic.py
  - Run: `python -m progressorx.examples.basic`
- FastAPI integration: src/progressorx/examples/fastapi.py
  - Run: `uvicorn progressorx.examples.fastapi:app --reload`
