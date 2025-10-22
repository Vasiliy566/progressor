"""
Basic runnable example for progressorx.

Run:
    python -m progressorx.examples.basic
"""
from __future__ import annotations

import time

from progressorx import ProgressManager
from progressorx.backends.memory import InMemoryStore


def main() -> None:
    store = InMemoryStore()
    mgr = ProgressManager(store)

    task_id = "demo-task"
    mgr.create(task_id, progress=0)

    total_steps = 10
    print(f"Starting {task_id}...")
    for i in range(total_steps):
        # simulate work
        time.sleep(0.2)
        # report progress increase
        mgr.report_progress(task_id, increase=100 / total_steps)
        rec = mgr.get_progress(task_id)
        print(f"Progress: {rec.progress:.0f}% (status={rec.status})")

    rec = mgr.get_progress(task_id)
    print(f"Finished {task_id}: {rec.progress:.0f}% (status={rec.status})")


if __name__ == "__main__":
    main()
