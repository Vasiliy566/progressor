from __future__ import annotations

import pytest

from progressorx.backends.sql_store import SQLStore
from progressorx.exceptions import RecordNotFoundError, IncorrectProgressValueError


class FakeCursor:
    def __init__(self, db: "FakeConn") -> None:
        self.db = db
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str, params=None):
        s = sql.strip().lower()
        # We only emulate the few statements used by SQLStore
        if s.startswith("create table"):
            # no-op, table auto-exists in memory
            self._row = None
            return
        if s.startswith("insert into"):
            task_id, progress, status = params
            rec = self.db._data.get(task_id)
            if rec is None:
                self.db._data[task_id] = {
                    "task_id": task_id,
                    "progress": float(progress),
                    "status": status,
                }
            else:
                rec["progress"] = float(progress)
                rec["status"] = status
            self._row = (task_id, float(progress), status)
            return
        if s.startswith("select"):
            # WHERE task_id = %s
            (task_id,) = params
            rec = self.db._data.get(task_id)
            if rec is None:
                self._row = None
            else:
                self._row = (rec["task_id"], float(rec["progress"]), rec["status"]) 
            return
        if s.startswith("update"):
            progress, status, task_id = params
            rec = self.db._data.get(task_id)
            if rec is None:
                self._row = None
            else:
                rec["progress"] = float(progress)
                rec["status"] = status
                self._row = (task_id, float(progress), status)
            return
        if s.startswith("delete"):
            (task_id,) = params
            self.db._data.pop(task_id, None)
            self._row = None
            return
        raise NotImplementedError(f"SQL not supported in fake: {sql}")

    def fetchone(self):
        return self._row


class FakeConn:
    def __init__(self):
        self._data: dict[str, dict] = {}

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        pass


# Helper to construct store using fake connection

def make_store():
    return SQLStore(conn=FakeConn(), auto_create_table=True)


def test_create_and_get_defaults():
    store = make_store()
    store.create("t1")
    rec = store.get("t1")
    assert rec.task_id == "t1"
    assert rec.progress == 0.0
    assert rec.status == "in_progress"


def test_create_with_values():
    store = make_store()
    store.create("t2", progress=12.5, status="pending")
    rec = store.get("t2")
    assert rec.progress == 12.5
    assert rec.status == "pending"


def test_set_and_get():
    store = make_store()
    store.create("t3")
    rec = store.set("t3", 10)
    assert rec.progress == 10
    assert rec.status == "in_progress"


def test_set_to_100_marks_finished():
    store = make_store()
    store.create("t4")
    rec = store.set("t4", 100)
    assert rec.progress == 100
    assert rec.status == "finished"


def test_increment_and_bounds():
    store = make_store()
    store.create("t5")
    store.set("t5", 90)
    rec = store.increment("t5", 10)
    assert rec.progress == 100
    assert rec.status == "finished"

    with pytest.raises(IncorrectProgressValueError):
        store.increment("t5", 1)


def test_set_out_of_bounds_raises():
    store = make_store()
    store.create("t6")
    with pytest.raises(IncorrectProgressValueError):
        store.set("t6", -0.01)
    with pytest.raises(IncorrectProgressValueError):
        store.set("t6", 100.01)


def test_get_missing_and_delete():
    store = make_store()
    with pytest.raises(RecordNotFoundError):
        store.get("missing")

    store.create("t7", progress=5)
    assert store.get("t7").progress == 5
    store.delete("t7")
    with pytest.raises(RecordNotFoundError):
        store.get("t7")
