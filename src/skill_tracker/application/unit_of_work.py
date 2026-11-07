"""Unit of Work port.

A unit of work groups repositories behind a single transaction and connection,
so application services never touch database concerns directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.repositories import ProjectRepository, StudyLogRepository, TopicRepository


class UnitOfWork(ABC):
    topics: TopicRepository
    projects: ProjectRepository
    logs: StudyLogRepository

    @abstractmethod
    def __enter__(self) -> UnitOfWork:
        """Begin a transaction and return this unit of work."""

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None:
        """Commit on success, roll back on failure, and release resources."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Discard pending changes."""
