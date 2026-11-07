"""Framework-free input/output data structures for use cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ..domain.entities import StudyLog


@dataclass(frozen=True)
class TopicInput:
    title: str
    category: str = "General"
    color: str = "indigo"
    description: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ProjectInput:
    title: str
    topic_id: str | None = None
    status: str = "Active"
    target_date: str | None = None
    repo_url: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class StudyLogInput:
    topic_id: str
    hours: Decimal | float | str
    project_id: str | None = None
    logged_on: str | date | None = None
    note: str = ""


@dataclass(frozen=True)
class DashboardSummary:
    active_topics_count: int
    total_modules: int
    completed_modules: int
    module_completion_pct: int
    active_projects_count: int
    completed_projects_count: int
    total_hours_logged: Decimal
    recent_logs: list[StudyLog]
