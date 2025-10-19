from fastapi import FastAPI, BackgroundTasks, HTTPException

import time
import uuid

from progressorx import ProgressManager
from progressorx.backends.memory import InMemoryStore

app = FastAPI()
store = InMemoryStore()
mgr = ProgressManager(store)


@app.post('/create')
def create(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())

    mgr.create(task_id, progress=0)
    background_tasks.add_task(long_work, task_id)
    return {"task_id": task_id}


def long_work(task_id: str):
    total = 10
    for i in range(total + 1):
        time.sleep(1) # simulate work
        mgr.report_progress(task_id, increase=100 / total)


@app.get('/progress/{task_id}')
def progress(task_id: str):
    res = mgr.get_progress(task_id)
    if res is None:
        raise HTTPException(status_code=404, detail='task not found')
    return res