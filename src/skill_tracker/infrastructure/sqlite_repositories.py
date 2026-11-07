"""SQLite implementations of the domain repository ports."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from decimal import Decimal

from ..domain.entities import Module, Project, StudyLog, Task, Topic
from ..domain.errors import EntityNotFoundError
from ..domain.repositories import ProjectRepository, StudyLogRepository, TopicRepository
from ..domain.value_objects import ProjectStatus, TopicColor


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SqliteTopicRepository(TopicRepository):
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, topic: Topic) -> None:
        self._connection.execute(
            """
            INSERT INTO topics (id, title, category, color, description, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic.id,
                topic.title,
                topic.category,
                topic.color.value,
                topic.description,
                topic.notes,
                _now(),
            ),
        )
        self._replace_modules(topic)

    def update(self, topic: Topic) -> None:
        cursor = self._connection.execute(
            """
            UPDATE topics
               SET title = ?, category = ?, color = ?, description = ?, notes = ?
             WHERE id = ?
            """,
            (
                topic.title,
                topic.category,
                topic.color.value,
                topic.description,
                topic.notes,
                topic.id,
            ),
        )
        if cursor.rowcount == 0:
            raise EntityNotFoundError(f"Topic {topic.id!r} does not exist")
        self._connection.execute("DELETE FROM modules WHERE topic_id = ?", (topic.id,))
        self._replace_modules(topic)

    def get(self, topic_id: str) -> Topic:
        row = self._connection.execute(
            "SELECT * FROM topics WHERE id = ?", (topic_id,)
        ).fetchone()
        if row is None:
            raise EntityNotFoundError(f"Topic {topic_id!r} does not exist")
        return self._to_entity(row, self._load_modules([topic_id]).get(topic_id, []))

    def list(self) -> list[Topic]:
        rows = self._connection.execute(
            "SELECT * FROM topics ORDER BY created_at ASC, rowid ASC"
        ).fetchall()
        modules = self._load_modules([row["id"] for row in rows])
        return [self._to_entity(row, modules.get(row["id"], [])) for row in rows]

    def delete(self, topic_id: str) -> None:
        cursor = self._connection.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        if cursor.rowcount == 0:
            raise EntityNotFoundError(f"Topic {topic_id!r} does not exist")

    def delete_all(self) -> None:
        self._connection.execute("DELETE FROM topics")

    def _replace_modules(self, topic: Topic) -> None:
        self._connection.executemany(
            "INSERT INTO modules (id, topic_id, title, completed, position) VALUES (?, ?, ?, ?, ?)",
            [
                (module.id, topic.id, module.title, int(module.completed), position)
                for position, module in enumerate(topic.modules)
            ],
        )

    def _load_modules(self, topic_ids: list[str]) -> dict[str, list[Module]]:
        if not topic_ids:
            return {}
        placeholders = ",".join("?" for _ in topic_ids)
        rows = self._connection.execute(
            f"""
            SELECT * FROM modules
             WHERE topic_id IN ({placeholders})
             ORDER BY position ASC, rowid ASC
            """,
            topic_ids,
        ).fetchall()
        grouped: dict[str, list[Module]] = {}
        for row in rows:
            grouped.setdefault(row["topic_id"], []).append(
                Module(id=row["id"], title=row["title"], completed=bool(row["completed"]))
            )
        return grouped

    @staticmethod
    def _to_entity(row: sqlite3.Row, modules: list[Module]) -> Topic:
        return Topic(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            color=TopicColor.parse(row["color"]),
            description=row["description"],
            notes=row["notes"],
            modules=modules,
        )


class SqliteProjectRepository(ProjectRepository):
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, project: Project) -> None:
        self._connection.execute(
            """
            INSERT INTO projects
                (id, title, topic_id, status, target_date, hours_spent,
                 repo_url, tech_stack, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project.id,
                project.title,
                project.topic_id,
                project.status.value,
                project.target_date.isoformat() if project.target_date else None,
                float(project.hours_spent),
                project.repo_url,
                json.dumps(project.tech_stack),
                project.description,
                _now(),
            ),
        )
        self._replace_tasks(project)

    def update(self, project: Project) -> None:
        cursor = self._connection.execute(
            """
            UPDATE projects
               SET title = ?, topic_id = ?, status = ?, target_date = ?,
                   hours_spent = ?, repo_url = ?, tech_stack = ?, description = ?
             WHERE id = ?
            """,
            (
                project.title,
                project.topic_id,
                project.status.value,
                project.target_date.isoformat() if project.target_date else None,
                float(project.hours_spent),
                project.repo_url,
                json.dumps(project.tech_stack),
                project.description,
                project.id,
            ),
        )
        if cursor.rowcount == 0:
            raise EntityNotFoundError(f"Project {project.id!r} does not exist")
        self._connection.execute("DELETE FROM tasks WHERE project_id = ?", (project.id,))
        self._replace_tasks(project)

    def get(self, project_id: str) -> Project:
        row = self._connection.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise EntityNotFoundError(f"Project {project_id!r} does not exist")
        return self._to_entity(row, self._load_tasks([project_id]).get(project_id, []))

    def list(self) -> list[Project]:
        rows = self._connection.execute(
            "SELECT * FROM projects ORDER BY created_at ASC, rowid ASC"
        ).fetchall()
        tasks = self._load_tasks([row["id"] for row in rows])
        return [self._to_entity(row, tasks.get(row["id"], [])) for row in rows]

    def delete(self, project_id: str) -> None:
        cursor = self._connection.execute(
            "DELETE FROM projects WHERE id = ?", (project_id,)
        )
        if cursor.rowcount == 0:
            raise EntityNotFoundError(f"Project {project_id!r} does not exist")

    def delete_all(self) -> None:
        self._connection.execute("DELETE FROM projects")

    def _replace_tasks(self, project: Project) -> None:
        self._connection.executemany(
            "INSERT INTO tasks (id, project_id, title, completed, position) VALUES (?, ?, ?, ?, ?)",
            [
                (task.id, project.id, task.title, int(task.completed), position)
                for position, task in enumerate(project.tasks)
            ],
        )

    def _load_tasks(self, project_ids: list[str]) -> dict[str, list[Task]]:
        if not project_ids:
            return {}
        placeholders = ",".join("?" for _ in project_ids)
        rows = self._connection.execute(
            f"""
            SELECT * FROM tasks
             WHERE project_id IN ({placeholders})
             ORDER BY position ASC, rowid ASC
            """,
            project_ids,
        ).fetchall()
        grouped: dict[str, list[Task]] = {}
        for row in rows:
            grouped.setdefault(row["project_id"], []).append(
                Task(id=row["id"], title=row["title"], completed=bool(row["completed"]))
            )
        return grouped

    @staticmethod
    def _to_entity(row: sqlite3.Row, tasks: list[Task]) -> Project:
        tech_stack = json.loads(row["tech_stack"]) if row["tech_stack"] else []
        return Project(
            id=row["id"],
            title=row["title"],
            topic_id=row["topic_id"],
            status=ProjectStatus.parse(row["status"]),
            target_date=date.fromisoformat(row["target_date"]) if row["target_date"] else None,
            hours_spent=Decimal(str(row["hours_spent"])),
            repo_url=row["repo_url"],
            tech_stack=list(tech_stack),
            description=row["description"],
            tasks=tasks,
        )


class SqliteStudyLogRepository(StudyLogRepository):
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, log: StudyLog) -> None:
        self._connection.execute(
            """
            INSERT INTO study_logs
                (id, topic_id, topic_title, project_id, hours, logged_on, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.id,
                log.topic_id,
                log.topic_title,
                log.project_id,
                float(log.hours),
                log.logged_on.isoformat(),
                log.note,
                _now(),
            ),
        )

    def list(self) -> list[StudyLog]:
        rows = self._connection.execute(
            "SELECT * FROM study_logs ORDER BY logged_on DESC, created_at DESC, rowid DESC"
        ).fetchall()
        return [
            StudyLog(
                id=row["id"],
                topic_id=row["topic_id"],
                topic_title=row["topic_title"],
                project_id=row["project_id"],
                hours=Decimal(str(row["hours"])),
                logged_on=date.fromisoformat(row["logged_on"]),
                note=row["note"],
            )
            for row in rows
        ]

    def delete_all(self) -> None:
        self._connection.execute("DELETE FROM study_logs")
