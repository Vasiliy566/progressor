from __future__ import annotations

from typing import Any, Dict

import pytest

from progressorx.backends.redis_store import RedisStore
from progressorx.exceptions import RecordNotFoundError, IncorrectProgressValueError


class FakeRedis:
    """Minimal in-memory Redis-like client for tests.

    Implements only the subset of commands used by RedisStore: exists, hset, hgetall, delete.
    Behaves like redis-py with decode_responses=False (bytes keys and values on read).
    """

    def __init__(self) -> None:
        self._data: Dict[str, Dict[bytes, bytes]] = {}

    # Key helpers
    def exists(self, key: str) -> int:
        return 1 if key in self._data else 0

    # Hash commands
    def hset(self, key: str, mapping: Dict[str, Any]) -> None:
        h = self._data.setdefault(key, {})
        for k, v in mapping.items():
            kb = k if isinstance(k, bytes) else str(k).encode("utf-8")
            # In redis, numbers are stored as strings
            if isinstance(v, bytes):
                vb = v
            else:
                vb = str(v).encode("utf-8")
            h[kb] = vb

    def hgetall(self, key: str) -> Dict[bytes, bytes]:
        return dict(self._data.get(key, {}))

    def delete(self, key: str) -> int:
        return 1 if self._data.pop(key, None) is not None else 0


def make_store() -> RedisStore:
    return RedisStore(client=FakeRedis())


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
