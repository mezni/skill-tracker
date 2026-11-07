"""Aggregate roots and entities.

Entities enforce their own invariants and are unaware of persistence or HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import uuid4

from .errors import EntityNotFoundError, ValidationError
from .value_objects import (
    Progress,
    ProjectStatus,
    StudyHours,
    TopicColor,
    optional_text,
    optional_url,
    parse_optional_iso_date,
    quantise_hours,
    require_text,
)


def _new_id() -> str:
    return str(uuid4())


@dataclass
class Module:
    id: str
    title: str
    completed: bool = False

    @classmethod
    def create(cls, title: object, *, module_id: str | None = None) -> Module:
        return cls(id=module_id or _new_id(), title=require_text(title, "module title", max_length=300))


@dataclass
class Task:
    id: str
    title: str
    completed: bool = False

    @classmethod
    def create(cls, title: object, *, task_id: str | None = None) -> Task:
        return cls(id=task_id or _new_id(), title=require_text(title, "task title", max_length=300))


@dataclass
class Topic:
    """A learning domain composed of ordered modules."""

    id: str
    title: str
    category: str
    color: TopicColor = TopicColor.INDIGO
    description: str = ""
    notes: str = ""
    modules: list[Module] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        title: object,
        *,
        category: object = "General",
        color: object = TopicColor.INDIGO,
        description: object = "",
        notes: object = "",
        topic_id: str | None = None,
    ) -> Topic:
        return cls(
            id=topic_id or _new_id(),
            title=require_text(title, "topic title", max_length=300),
            category=require_text(category or "General", "category", max_length=100),
            color=TopicColor.parse(color),
            description=optional_text(description),
            notes=optional_text(notes),
        )

    def update_details(
        self,
        *,
        title: object,
        category: object,
        color: object,
        description: object,
        notes: object,
    ) -> None:
        self.title = require_text(title, "topic title", max_length=300)
        self.category = require_text(category or "General", "category", max_length=100)
        self.color = TopicColor.parse(color)
        self.description = optional_text(description)
        self.notes = optional_text(notes)

    def add_module(self, title: object, *, module_id: str | None = None) -> Module:
        module = Module.create(title, module_id=module_id)
        self.modules.append(module)
        return module

    def toggle_module(self, module_id: str) -> Module:
        module = self.find_module(module_id)
        module.completed = not module.completed
        return module

    def find_module(self, module_id: str) -> Module:
        for module in self.modules:
            if module.id == module_id:
                return module
        raise EntityNotFoundError(f"Module {module_id!r} does not belong to topic {self.id!r}")

    @property
    def progress(self) -> Progress:
        return Progress(
            completed=sum(1 for module in self.modules if module.completed),
            total=len(self.modules),
        )


@dataclass
class Project:
    """A side project, optionally linked to a learning topic."""

    id: str
    title: str
    topic_id: str | None
    status: ProjectStatus
    target_date: date | None
    hours_spent: Decimal
    repo_url: str | None
    tech_stack: list[str]
    description: str
    tasks: list[Task] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        title: object,
        *,
        topic_id: str | None = None,
        status: object = ProjectStatus.ACTIVE,
        target_date: object = None,
        repo_url: object = None,
        tech_stack: object = None,
        description: object = "",
        hours_spent: object = Decimal(0),
        project_id: str | None = None,
    ) -> Project:
        return cls(
            id=project_id or _new_id(),
            title=require_text(title, "project title", max_length=300),
            topic_id=_clean_optional_id(topic_id),
            status=ProjectStatus.parse(status),
            target_date=parse_optional_iso_date(target_date, "targetDate"),
            hours_spent=_parse_hours_spent(hours_spent),
            repo_url=optional_url(repo_url, "repoUrl"),
            tech_stack=_parse_tech_stack(tech_stack),
            description=optional_text(description),
        )

    def update_details(
        self,
        *,
        title: object,
        topic_id: object,
        status: object,
        target_date: object,
        repo_url: object,
        tech_stack: object,
        description: object,
    ) -> None:
        self.title = require_text(title, "project title", max_length=300)
        self.topic_id = _clean_optional_id(topic_id)
        self.status = ProjectStatus.parse(status)
        self.target_date = parse_optional_iso_date(target_date, "targetDate")
        self.repo_url = optional_url(repo_url, "repoUrl")
        self.tech_stack = _parse_tech_stack(tech_stack)
        self.description = optional_text(description)

    def add_hours(self, hours: StudyHours) -> None:
        self.hours_spent = quantise_hours(self.hours_spent + hours.value)

    def add_task(self, title: object, *, task_id: str | None = None) -> Task:
        task = Task.create(title, task_id=task_id)
        self.tasks.append(task)
        return task

    def toggle_task(self, task_id: str) -> Task:
        task = self.find_task(task_id)
        task.completed = not task.completed
        return task

    def find_task(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise EntityNotFoundError(f"Task {task_id!r} does not belong to project {self.id!r}")

    @property
    def task_progress(self) -> Progress:
        return Progress(
            completed=sum(1 for task in self.tasks if task.completed),
            total=len(self.tasks),
        )


@dataclass(frozen=True)
class StudyLog:
    """An immutable record of a study session.

    ``topic_title`` is a snapshot so history stays readable after a topic is
    deleted or renamed.
    """

    id: str
    topic_id: str | None
    topic_title: str
    project_id: str | None
    hours: Decimal
    logged_on: date
    note: str

    @classmethod
    def create(
        cls,
        *,
        topic_id: str,
        topic_title: str,
        hours: object,
        logged_on: object,
        project_id: str | None = None,
        note: object = "",
        log_id: str | None = None,
    ) -> StudyLog:
        parsed_hours = StudyHours.parse(hours)
        return cls(
            id=log_id or _new_id(),
            topic_id=_clean_optional_id(topic_id),
            topic_title=require_text(topic_title, "topic title", max_length=300),
            project_id=_clean_optional_id(project_id),
            hours=parsed_hours.value,
            logged_on=parse_optional_iso_date(logged_on, "date") or date.today(),  # noqa: DTZ011 - study date is local
            note=optional_text(note),
        )


def _clean_optional_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_hours_spent(value: object) -> Decimal:
    try:
        hours = Decimal(str(value or "0"))
    except Exception as exc:
        raise ValidationError("hoursSpent must be a number") from exc
    if not hours.is_finite() or hours < 0:
        raise ValidationError("hoursSpent cannot be negative")
    return quantise_hours(hours)


def _parse_tech_stack(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = list(value)

    items: list[str] = []
    for raw in raw_items:
        item = str(raw).strip()
        if item and item not in items:
            items.append(item)
    return items
