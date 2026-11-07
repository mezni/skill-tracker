"""Pydantic contracts for the HTTP API (camelCase over the wire)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ..application.dto import DashboardSummary
from ..application.transfer import ImportSummary
from ..domain.entities import Project, StudyLog, Topic


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------
class TopicIn(ApiModel):
    title: str
    category: str = "General"
    color: str = "indigo"
    description: str = ""
    notes: str = ""


class ProjectIn(ApiModel):
    title: str
    topic_id: str | None = None
    status: str = "Active"
    target_date: str | None = None
    repo_url: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    description: str = ""


class StudyLogIn(ApiModel):
    topic_id: str
    project_id: str | None = None
    hours: float
    date: str | None = None
    note: str = ""


class ChecklistItemIn(ApiModel):
    title: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------
class ModuleOut(ApiModel):
    id: str
    title: str
    completed: bool

    @classmethod
    def from_entity(cls, module) -> ModuleOut:
        return cls(id=module.id, title=module.title, completed=module.completed)


class TopicOut(ApiModel):
    id: str
    title: str
    category: str
    color: str
    description: str
    notes: str
    modules: list[ModuleOut]
    total_modules: int
    completed_modules: int
    completion_percentage: int

    @classmethod
    def from_entity(cls, topic: Topic) -> TopicOut:
        progress = topic.progress
        return cls(
            id=topic.id,
            title=topic.title,
            category=topic.category,
            color=topic.color.value,
            description=topic.description,
            notes=topic.notes,
            modules=[ModuleOut.from_entity(module) for module in topic.modules],
            total_modules=progress.total,
            completed_modules=progress.completed,
            completion_percentage=progress.percentage,
        )


class TaskOut(ApiModel):
    id: str
    title: str
    completed: bool

    @classmethod
    def from_entity(cls, task) -> TaskOut:
        return cls(id=task.id, title=task.title, completed=task.completed)


class ProjectOut(ApiModel):
    id: str
    title: str
    topic_id: str | None
    status: str
    target_date: str | None
    hours_spent: float
    repo_url: str | None
    tech_stack: list[str]
    description: str
    tasks: list[TaskOut]
    total_tasks: int
    completed_tasks: int
    task_completion_percentage: int

    @classmethod
    def from_entity(cls, project: Project) -> ProjectOut:
        progress = project.task_progress
        return cls(
            id=project.id,
            title=project.title,
            topic_id=project.topic_id,
            status=project.status.value,
            target_date=project.target_date.isoformat() if project.target_date else None,
            hours_spent=float(project.hours_spent),
            repo_url=project.repo_url,
            tech_stack=project.tech_stack,
            description=project.description,
            tasks=[TaskOut.from_entity(task) for task in project.tasks],
            total_tasks=progress.total,
            completed_tasks=progress.completed,
            task_completion_percentage=progress.percentage,
        )


class StudyLogOut(ApiModel):
    id: str
    topic_id: str | None
    topic_title: str
    project_id: str | None
    hours: float
    date: str
    note: str

    @classmethod
    def from_entity(cls, log: StudyLog) -> StudyLogOut:
        return cls(
            id=log.id,
            topic_id=log.topic_id,
            topic_title=log.topic_title,
            project_id=log.project_id,
            hours=float(log.hours),
            date=log.logged_on.isoformat(),
            note=log.note,
        )


class ImportSummaryOut(ApiModel):
    topics_imported: int
    projects_imported: int
    logs_imported: int

    @classmethod
    def from_summary(cls, summary: ImportSummary) -> ImportSummaryOut:
        return cls(
            topics_imported=summary.topics_imported,
            projects_imported=summary.projects_imported,
            logs_imported=summary.logs_imported,
        )


class DashboardOut(ApiModel):
    active_topics_count: int
    total_modules: int
    completed_modules: int
    module_completion_pct: int
    active_projects_count: int
    completed_projects_count: int
    total_hours_logged: float
    recent_logs: list[StudyLogOut]

    @classmethod
    def from_summary(cls, summary: DashboardSummary) -> DashboardOut:
        return cls(
            active_topics_count=summary.active_topics_count,
            total_modules=summary.total_modules,
            completed_modules=summary.completed_modules,
            module_completion_pct=summary.module_completion_pct,
            active_projects_count=summary.active_projects_count,
            completed_projects_count=summary.completed_projects_count,
            total_hours_logged=float(summary.total_hours_logged),
            recent_logs=[StudyLogOut.from_entity(log) for log in summary.recent_logs],
        )
