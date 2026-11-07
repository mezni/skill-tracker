"""Backup and restore use cases backed by a workbook codec port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

from ..domain.entities import Project, StudyLog, Topic
from .services import UnitOfWorkFactory
from .unit_of_work import UnitOfWork


@dataclass(frozen=True)
class TrackerSnapshot:
    topics: list[Topic]
    projects: list[Project]
    logs: list[StudyLog]


@dataclass(frozen=True)
class ImportSummary:
    topics_imported: int
    projects_imported: int
    logs_imported: int


class ExcelCodec(ABC):
    """Port for encoding/decoding a full tracker snapshot as a workbook."""

    @abstractmethod
    def encode(self, snapshot: TrackerSnapshot) -> bytes:
        """Serialise the snapshot to XLSX bytes."""

    @abstractmethod
    def decode(self, data: bytes) -> TrackerSnapshot:
        """Parse XLSX bytes into a snapshot, raising ``ValidationError`` if invalid."""


class TransferService:
    """Export everything, or restore everything in a single transaction.

    Import is a *restore*: it replaces the current data set so exported
    workbooks round-trip exactly. References to entities that are not part of
    the workbook are detached, matching normal cascade-delete behaviour.
    """

    def __init__(self, uow_factory: UnitOfWorkFactory, codec: ExcelCodec) -> None:
        self._uow_factory = uow_factory
        self._codec = codec

    def export(self) -> bytes:
        with self._uow_factory() as uow:
            snapshot = TrackerSnapshot(
                topics=uow.topics.list(),
                projects=uow.projects.list(),
                logs=uow.logs.list(),
            )
        return self._codec.encode(snapshot)

    def import_(self, data: bytes) -> ImportSummary:
        snapshot = self._normalise(self._codec.decode(data))
        with self._uow_factory() as uow:
            self._clear(uow)
            for topic in snapshot.topics:
                uow.topics.add(topic)
            for project in snapshot.projects:
                uow.projects.add(project)
            for log in snapshot.logs:
                uow.logs.add(log)

        return ImportSummary(
            topics_imported=len(snapshot.topics),
            projects_imported=len(snapshot.projects),
            logs_imported=len(snapshot.logs),
        )

    @staticmethod
    def _clear(uow: UnitOfWork) -> None:
        uow.logs.delete_all()
        uow.projects.delete_all()
        uow.topics.delete_all()

    @staticmethod
    def _normalise(snapshot: TrackerSnapshot) -> TrackerSnapshot:
        topic_ids = {topic.id for topic in snapshot.topics}

        projects: list[Project] = []
        for project in snapshot.projects:
            if project.topic_id not in topic_ids:
                project.topic_id = None
            projects.append(project)

        project_ids = {project.id for project in projects}
        logs = [
            replace(
                log,
                topic_id=log.topic_id if log.topic_id in topic_ids else None,
                project_id=log.project_id if log.project_id in project_ids else None,
            )
            for log in snapshot.logs
        ]
        return TrackerSnapshot(topics=snapshot.topics, projects=projects, logs=logs)
