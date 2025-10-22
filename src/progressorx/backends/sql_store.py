from __future__ import annotations

from typing import Optional, Protocol, Any

from progressorx.models import ProgressRecord
from progressorx.exceptions import RecordNotFoundError, IncorrectProgressValueError
from progressorx.store import ProgressStore

# Optional postgres client(s)
try:  # pragma: no cover - optional dependency
    import psycopg as _psycopg  # psycopg 3
except Exception:  # pragma: no cover - optional dependency
    _psycopg = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import psycopg2 as _psycopg2  # psycopg 2
except Exception:  # pragma: no cover - optional dependency
    _psycopg2 = None  # type: ignore


class _ConnectionLike(Protocol):  # minimal protocol we rely on
    def cursor(self) -> Any: ...
    def commit(self) -> None: ...


class SQLStore(ProgressStore):
    """PostgreSQL-backed store for progress records.

    Notes:
      - Only PostgreSQL is supported (via psycopg or psycopg2).
      - The dependency is optional; instantiate only if a driver is installed
        or pass a pre-configured connection.
    """

    def __init__(
        self,
        *,
        conn: Optional[_ConnectionLike] = None,
        dsn: Optional[str] = None,
        table: str = "progressorx_progress",
        auto_create_table: bool = True,
    ) -> None:
        if conn is None:
            # Lazily try to connect using available driver and provided DSN
            if dsn is None:
                raise RuntimeError(
                    "No PostgreSQL connection provided. Pass conn or dsn (e.g., postgresql://user:pass@host/db)."
                )
            if _psycopg is not None:  # psycopg3
                conn = _psycopg.connect(dsn)
            elif _psycopg2 is not None:  # psycopg2
                conn = _psycopg2.connect(dsn)  # type: ignore
            else:
                raise RuntimeError(
                    "No postgres driver found. Install `psycopg[binary]` (preferred) or `psycopg2`."
                )
        self._conn: _ConnectionLike = conn
        self._table = table

        if auto_create_table:
            self._ensure_table()

    # --- schema helpers ---
    def _ensure_table(self) -> None:
        sql = (
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                task_id TEXT PRIMARY KEY,
                progress DOUBLE PRECISION NOT NULL,
                status TEXT NOT NULL
            );
            """
        )
        with self._conn.cursor() as cur:  # type: ignore[attr-defined]
            cur.execute(sql)
        self._conn.commit()

    # --- CRUD API ---
    def create(self, task_id: str, progress: float | int = 0.0, status: str = "in_progress") -> ProgressRecord:
        # Upsert to allow idempotent create
        sql = (
            f"""
            INSERT INTO {self._table} (task_id, progress, status)
            VALUES (%s, %s, %s)
            ON CONFLICT (task_id) DO UPDATE SET progress = EXCLUDED.progress, status = EXCLUDED.status
            RETURNING task_id, progress, status;
            """
        )
        with self._conn.cursor() as cur:  # type: ignore[attr-defined]
            cur.execute(sql, (task_id, float(progress), status))
            row = cur.fetchone()
        self._conn.commit()
        return ProgressRecord(task_id=row[0], progress=float(row[1]), status=row[2])

    def get(self, task_id: str) -> ProgressRecord:
        sql = f"SELECT task_id, progress, status FROM {self._table} WHERE task_id = %s;"
        with self._conn.cursor() as cur:  # type: ignore[attr-defined]
            cur.execute(sql, (task_id,))
            row = cur.fetchone()
        if not row:
            raise RecordNotFoundError
        return ProgressRecord(task_id=row[0], progress=float(row[1]), status=row[2])

    def set(self, task_id: str, progress: float, status: str | None = None) -> ProgressRecord:
        if progress < 0.0 or progress > 100.0:
            raise IncorrectProgressValueError
        # ensure exists
        _ = self.get(task_id)
        status_to_set = status or ("finished" if progress >= 100.0 else "in_progress")
        sql = f"UPDATE {self._table} SET progress = %s, status = %s WHERE task_id = %s RETURNING task_id, progress, status;"
        with self._conn.cursor() as cur:  # type: ignore[attr-defined]
            cur.execute(sql, (float(progress), status_to_set, task_id))
            row = cur.fetchone()
        self._conn.commit()
        if not row:
            # Should not happen due to get() above, but keep safety
            raise RecordNotFoundError
        return ProgressRecord(task_id=row[0], progress=float(row[1]), status=row[2])

    def increment(self, task_id: str, delta: float) -> ProgressRecord:
        rec = self.get(task_id)
        new_progress = rec.progress + float(delta)
        if new_progress < 0.0 or new_progress > 100.0:
            raise IncorrectProgressValueError
        return self.set(task_id, new_progress)

    def delete(self, task_id: str) -> None:
        sql = f"DELETE FROM {self._table} WHERE task_id = %s;"
        with self._conn.cursor() as cur:  # type: ignore[attr-defined]
            cur.execute(sql, (task_id,))
        self._conn.commit()
