"""Repository ports (interfaces owned by the domain).

Implementations live in the infrastructure layer; the application depends only
on these abstractions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import Project, StudyLog, Topic


class TopicRepository(ABC):
    @abstractmethod
    def add(self, topic: Topic) -> None:
        """Persist a new topic aggregate."""

    @abstractmethod
    def update(self, topic: Topic) -> None:
        """Persist changes to an existing topic aggregate."""

    @abstractmethod
    def get(self, topic_id: str) -> Topic:
        """Return a topic or raise ``EntityNotFoundError``."""

    @abstractmethod
    def list(self) -> list[Topic]:
        """Return all topics ordered by creation time."""

    @abstractmethod
    def delete(self, topic_id: str) -> None:
        """Delete a topic; modules cascade and references are detached."""


class ProjectRepository(ABC):
    @abstractmethod
    def add(self, project: Project) -> None:
        """Persist a new project aggregate."""

    @abstractmethod
    def update(self, project: Project) -> None:
        """Persist changes to an existing project aggregate."""

    @abstractmethod
    def get(self, project_id: str) -> Project:
        """Return a project or raise ``EntityNotFoundError``."""

    @abstractmethod
    def list(self) -> list[Project]:
        """Return all projects ordered by creation time."""

    @abstractmethod
    def delete(self, project_id: str) -> None:
        """Delete a project; tasks cascade and log references are detached."""


class StudyLogRepository(ABC):
    @abstractmethod
    def add(self, log: StudyLog) -> None:
        """Persist a study log."""

    @abstractmethod
    def list(self) -> list[StudyLog]:
        """Return all logs, newest first."""
