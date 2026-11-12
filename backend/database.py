"""SQLite 连接、事务和初始化辅助。"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .models import init_schema

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "data" / "campus_market.db"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat(timespec="seconds")


def resolve_database_path(path: str | os.PathLike[str] | None = None) -> Path:
    raw = path or os.getenv("DATABASE_PATH")
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate.resolve()
    return DEFAULT_DB_PATH


class Database:
    """轻量 SQLite 封装；每个请求使用独立连接，避免跨线程共享。"""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = resolve_database_path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def init_schema(self) -> None:
        connection = self.connect()
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            init_schema(connection)
        finally:
            connection.close()

    def reset_schema(self) -> None:
        """仅供显式 seed --reset 使用。"""
        connection = self.connect()
        try:
            connection.execute("PRAGMA foreign_keys = OFF")
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            for table in tables:
                connection.execute(f'DROP TABLE IF EXISTS "{table["name"]}"')
            connection.commit()
            connection.execute("PRAGMA foreign_keys = ON")
        finally:
            connection.close()
        self.init_schema()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """BEGIN IMMEDIATE 事务，用于订单等需要原子性的写操作。"""
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        connection = self.connect()
        try:
            return connection.execute(sql, params).fetchone()
        finally:
            connection.close()

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        connection = self.connect()
        try:
            return list(connection.execute(sql, params).fetchall())
        finally:
            connection.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        connection = self.connect()
        try:
            cursor = connection.execute(sql, params)
            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None
