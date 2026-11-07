"""openpyxl adapter implementing the workbook codec port."""

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ..application.transfer import ExcelCodec, TrackerSnapshot
from ..domain.entities import Project, StudyLog, Topic
from ..domain.errors import ValidationError

TOPICS = "Topics"
MODULES = "Modules"
PROJECTS = "Projects"
TASKS = "Tasks"
LOGS = "StudyLogs"

TOPIC_HEADERS = ["id", "title", "category", "color", "description", "notes"]
MODULE_HEADERS = ["id", "topicId", "title", "completed", "position"]
PROJECT_HEADERS = [
    "id",
    "title",
    "topicId",
    "status",
    "targetDate",
    "hoursSpent",
    "repoUrl",
    "techStack",
    "description",
]
TASK_HEADERS = ["id", "projectId", "title", "completed", "position"]
LOG_HEADERS = ["id", "topicId", "topicTitle", "projectId", "hours", "date", "note"]

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1E293B")


class OpenpyxlExcelCodec(ExcelCodec):
    def encode(self, snapshot: TrackerSnapshot) -> bytes:
        workbook = Workbook()

        topics_sheet = workbook.active
        topics_sheet.title = TOPICS
        self._write(
            topics_sheet,
            TOPIC_HEADERS,
            [
                [
                    topic.id,
                    topic.title,
                    topic.category,
                    topic.color.value,
                    topic.description,
                    topic.notes,
                ]
                for topic in snapshot.topics
            ],
            widths=[38, 32, 16, 12, 50, 50],
        )

        modules_sheet = workbook.create_sheet(MODULES)
        self._write(
            modules_sheet,
            MODULE_HEADERS,
            [
                [module.id, topic.id, module.title, module.completed, position]
                for topic in snapshot.topics
                for position, module in enumerate(topic.modules, start=1)
            ],
            widths=[38, 38, 40, 12, 10],
        )

        projects_sheet = workbook.create_sheet(PROJECTS)
        self._write(
            projects_sheet,
            PROJECT_HEADERS,
            [
                [
                    project.id,
                    project.title,
                    project.topic_id,
                    project.status.value,
                    project.target_date.isoformat() if project.target_date else "",
                    float(project.hours_spent),
                    project.repo_url,
                    ", ".join(project.tech_stack),
                    project.description,
                ]
                for project in snapshot.projects
            ],
            widths=[38, 32, 38, 12, 14, 12, 42, 36, 50],
        )

        tasks_sheet = workbook.create_sheet(TASKS)
        self._write(
            tasks_sheet,
            TASK_HEADERS,
            [
                [task.id, project.id, task.title, task.completed, position]
                for project in snapshot.projects
                for position, task in enumerate(project.tasks, start=1)
            ],
            widths=[38, 38, 40, 12, 10],
        )

        logs_sheet = workbook.create_sheet(LOGS)
        self._write(
            logs_sheet,
            LOG_HEADERS,
            [
                [
                    log.id,
                    log.topic_id,
                    log.topic_title,
                    log.project_id,
                    float(log.hours),
                    log.logged_on.isoformat(),
                    log.note,
                ]
                for log in snapshot.logs
            ],
            widths=[38, 38, 32, 38, 10, 14, 50],
        )

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def decode(self, data: bytes) -> TrackerSnapshot:
        if not data:
            raise ValidationError("Workbook file is empty")

        try:
            workbook = load_workbook(BytesIO(data), data_only=True, read_only=True)
        except Exception as exc:
            raise ValidationError("File is not a valid .xlsx workbook") from exc

        try:
            if TOPICS not in workbook.sheetnames:
                raise ValidationError("Workbook must contain a 'Topics' sheet")

            topics = self._decode_topics(self._rows(workbook, TOPICS))
            projects = self._decode_projects(self._rows(workbook, PROJECTS))
            self._decode_modules(self._rows(workbook, MODULES), topics)
            self._decode_tasks(self._rows(workbook, TASKS), projects)
            logs = self._decode_logs(self._rows(workbook, LOGS))
        finally:
            workbook.close()

        return TrackerSnapshot(topics=list(topics.values()), projects=projects, logs=logs)

    # -- decoding helpers ---------------------------------------------------
    @staticmethod
    def _decode_topics(rows: list[dict[str, Any]]) -> dict[str, Topic]:
        topics: dict[str, Topic] = {}
        for row in rows:
            topic = Topic.create(
                title=_text(row.get("title")),
                category=_text(row.get("category")) or "General",
                color=_text(row.get("color")) or "indigo",
                description=_text(row.get("description")),
                notes=_text(row.get("notes")),
                topic_id=_optional(row.get("id")),
            )
            if topic.id in topics:
                raise ValidationError(f"Duplicate topic id {topic.id!r}")
            topics[topic.id] = topic
        return topics

    @staticmethod
    def _decode_modules(rows: list[dict[str, Any]], topics: dict[str, Topic]) -> None:
        for row in _ordered(rows):
            topic_id = _text(row.get("topicId"))
            topic = topics.get(topic_id)
            if topic is None:
                raise ValidationError(f"Module references unknown topic {topic_id!r}")
            module = topic.add_module(
                _text(row.get("title")), module_id=_optional(row.get("id"))
            )
            module.completed = _parse_bool(row.get("completed"))

    @staticmethod
    def _decode_projects(rows: list[dict[str, Any]]) -> list[Project]:
        projects: list[Project] = []
        seen: set[str] = set()
        for row in rows:
            project = Project.create(
                title=_text(row.get("title")),
                topic_id=_optional(row.get("topicId")),
                status=_text(row.get("status")) or "Active",
                target_date=_date_text(row.get("targetDate")),
                repo_url=_optional(row.get("repoUrl")),
                tech_stack=_text(row.get("techStack")),
                description=_text(row.get("description")),
                hours_spent=row.get("hoursSpent") or 0,
                project_id=_optional(row.get("id")),
            )
            if project.id in seen:
                raise ValidationError(f"Duplicate project id {project.id!r}")
            seen.add(project.id)
            projects.append(project)
        return projects

    @staticmethod
    def _decode_tasks(rows: list[dict[str, Any]], projects: list[Project]) -> None:
        projects_by_id = {project.id: project for project in projects}
        for row in _ordered(rows):
            project_id = _text(row.get("projectId"))
            project = projects_by_id.get(project_id)
            if project is None:
                raise ValidationError(f"Task references unknown project {project_id!r}")
            task = project.add_task(_text(row.get("title")), task_id=_optional(row.get("id")))
            task.completed = _parse_bool(row.get("completed"))

    @staticmethod
    def _decode_logs(rows: list[dict[str, Any]]) -> list[StudyLog]:
        logs: list[StudyLog] = []
        seen: set[str] = set()
        for row in rows:
            log = StudyLog.create(
                topic_id=_optional(row.get("topicId")) or "",
                topic_title=_text(row.get("topicTitle")),
                project_id=_optional(row.get("projectId")),
                hours=row.get("hours") or 0,
                logged_on=_date_text(row.get("date")),
                note=_text(row.get("note")),
                log_id=_optional(row.get("id")),
            )
            if log.id in seen:
                raise ValidationError(f"Duplicate log id {log.id!r}")
            seen.add(log.id)
            logs.append(log)
        return logs

    # -- sheet helpers ------------------------------------------------------
    @staticmethod
    def _write(
        sheet: Worksheet,
        headers: list[str],
        rows: list[list[Any]],
        *,
        widths: list[int],
    ) -> None:
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL

        for row in rows:
            sheet.append(row)

        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(sheet.max_row, 1)}"
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width

    @staticmethod
    def _rows(workbook, name: str) -> list[dict[str, Any]]:
        if name not in workbook.sheetnames:
            return []
        sheet = workbook[name]
        iterator = sheet.iter_rows(values_only=True)
        try:
            header_cells = next(iterator)
        except StopIteration:
            return []

        headers = [_text(cell) for cell in header_cells]
        rows: list[dict[str, Any]] = []
        for values in iterator:
            if values is None or all(_is_blank(value) for value in values):
                continue
            rows.append(
                {
                    headers[index]: values[index]
                    for index in range(min(len(headers), len(values)))
                    if headers[index]
                }
            )
        return rows


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _text(value: Any) -> str:
    if _is_blank(value):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _optional(value: Any) -> str | None:
    text = _text(value)
    return text or None


def _date_text(value: Any) -> str | None:
    text = _text(value)
    return text or None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _text(value).lower() in {"1", "true", "yes", "y", "x", "done", "completed"}


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(_text(value)))
    except (TypeError, ValueError):
        return default


def _ordered(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: _parse_int(row.get("position")))
