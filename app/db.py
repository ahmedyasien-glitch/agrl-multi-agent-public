from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    """Small DB adapter: Neon/PostgreSQL in production, SQLite fallback for local testing."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.backend = "postgres" if self.database_url else "sqlite"
        if self.backend == "sqlite":
            root = Path(__file__).resolve().parent.parent
            self.sqlite_path = Path(os.getenv("AGRL_DB_PATH", str(root / "data" / "agrl_multi_agent_v2.sqlite3"))).expanduser()
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.sqlite_path = None

    @contextmanager
    def connect(self):
        if self.backend == "sqlite":
            con = sqlite3.connect(self.sqlite_path, timeout=20)
            con.row_factory = sqlite3.Row
            try:
                yield con
                con.commit()
            finally:
                con.close()
            return

        try:
            import psycopg
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "DATABASE_URL is set but psycopg is not installed. Install psycopg[binary]>=3.2,<4."
            ) from exc
        url = self.database_url
        if "sslmode=" not in url and "localhost" not in url and "127.0.0.1" not in url:
            url += ("&" if "?" in url else "?") + "sslmode=require"
        con = psycopg.connect(url)
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _adapt(self, sql: str) -> str:
        return sql if self.backend == "postgres" else sql.replace("%s", "?")

    def init_schema(self) -> None:
        if self.backend == "postgres":
            schema = Path(__file__).resolve().parent.parent / "migrations" / "001_neon_schema.sql"
            sql = schema.read_text(encoding="utf-8")
            with self.connect() as con:
                with con.cursor() as cur:
                    cur.execute(sql)
            return

        schema = Path(__file__).resolve().parent.parent / "migrations" / "001_sqlite_schema.sql"
        sql = schema.read_text(encoding="utf-8")
        with self.connect() as con:
            con.executescript(sql)

    def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        with self.connect() as con:
            if self.backend == "postgres":
                with con.cursor() as cur:
                    cur.execute(sql, tuple(params))
            else:
                con.execute(self._adapt(sql), tuple(params))

    def fetch_one(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        with self.connect() as con:
            if self.backend == "postgres":
                with con.cursor() as cur:
                    cur.execute(sql, tuple(params))
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [d.name for d in cur.description]
                    return dict(zip(cols, row))
            row = con.execute(self._adapt(sql), tuple(params)).fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self.connect() as con:
            if self.backend == "postgres":
                with con.cursor() as cur:
                    cur.execute(sql, tuple(params))
                    rows = cur.fetchall()
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in rows]
            return [dict(r) for r in con.execute(self._adapt(sql), tuple(params)).fetchall()]

    def insert_returning_id(self, sql: str, params: Iterable[Any] = ()) -> int:
        if self.backend == "postgres":
            with self.connect() as con:
                with con.cursor() as cur:
                    cur.execute(sql, tuple(params))
                    row = cur.fetchone()
                    return int(row[0])
        with self.connect() as con:
            cur = con.execute(self._adapt(sql), tuple(params))
            return int(cur.lastrowid)

    def json(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)


db = Database()
