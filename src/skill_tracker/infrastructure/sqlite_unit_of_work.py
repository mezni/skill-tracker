"""SQLite Unit of Work: one connection and one transaction per use case."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Self

from ..application.unit_of_work import UnitOfWork
from .database import connect
from .sqlite_repositories import (
    SqliteProjectRepository,
    SqliteStudyLogRepository,
    SqliteTopicRepository,
)


class SqliteUnitOfWork(UnitOfWork):
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = db_path
        self._connection = None

    def __enter__(self) -> Self:
        self._connection = connect(self._db_path)
        self._connection.execute("BEGIN")
        self.topics = SqliteTopicRepository(self._connection)
        self.projects = SqliteProjectRepository(self._connection)
        self.logs = SqliteStudyLogRepository(self._connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
        return False

    def commit(self) -> None:
        if self._connection is not None:
            self._connection.execute("COMMIT")

    def rollback(self) -> None:
        if self._connection is not None:
            self._connection.execute("ROLLBACK")
