from __future__ import annotations

from typing import Optional

from progressorx.models import ProgressRecord
from progressorx.exceptions import RecordNotFoundError, IncorrectProgressValueError
from progressorx.store import ProgressStore

try:
    import redis as _redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _redis = None  # type: ignore


class RedisStore(ProgressStore):
    """Redis-backed store for progress records.

    Storage model:
      - Each task is stored as a Redis Hash under key f"{prefix}:{task_id}" with fields:
          progress -> float (stored as string)
          status   -> str

    Notes:
      - The redis dependency is optional; instantiate only if redis is installed
        or pass a pre-configured client.
    """

    def __init__(
        self,
        *,
        client: Optional["_redis.Redis"] = None,
        url: Optional[str] = None,
        prefix: str = "progressorx"
    ) -> None:
        if client is None:
            if _redis is None:
                raise RuntimeError(
                    "redis package is not installed. Install with `pip install redis` or pass a client."
                )
            if url is not None:
                client = _redis.from_url(url)
            else:
                client = _redis.Redis()
        self._r = client
        self._prefix = prefix.rstrip(":")

    def _key(self, task_id: str) -> str:
        return f"{self._prefix}:{task_id}"

    def _exists(self, task_id: str) -> bool:
        return bool(self._r.exists(self._key(task_id)))

    def create(self, task_id: str, progress: float | int = 0.0, status: str = "in_progress") -> ProgressRecord:
        self._r.hset(
            self._key(task_id),
            mapping={
                "progress": float(progress),
                "status": status,
        })
        return self.get(task_id)

    def get(self, task_id: str) -> ProgressRecord:
        key = self._key(task_id)
        data = self._r.hgetall(key)
        if not data:
            raise RecordNotFoundError
        def _decode(v):
            return v if isinstance(v, str) else v.decode("utf-8")

        progress_raw = data.get(b"progress") if b"progress" in data else data.get("progress")
        status_raw = data.get(b"status") if b"status" in data else data.get("status")
        if progress_raw is None or status_raw is None:
            raise RecordNotFoundError
        progress_val = float(_decode(progress_raw))
        status_val = _decode(status_raw)
        return ProgressRecord(task_id=task_id, progress=progress_val, status=status_val)

    def set(self, task_id: str, progress: float, status: str | None = None) -> ProgressRecord:
        if progress < 0.0 or progress > 100.0:
            raise IncorrectProgressValueError
        _ = self.get(task_id)
        status_to_set = status or ("finished" if progress >= 100.0 else "in_progress")

        self._r.hset(
            self._key(task_id),
            mapping={
                "progress": float(progress),
                "status": status_to_set,
        })
        return self.get(task_id)

    def increment(self, task_id: str, delta: float) -> ProgressRecord:
        rec = self.get(task_id)
        new_progress = rec.progress + float(delta)
        if new_progress < 0.0 or new_progress > 100.0:
            raise IncorrectProgressValueError
        return self.set(task_id, new_progress)

    def delete(self, task_id: str) -> None:
        self._r.delete(self._key(task_id))
