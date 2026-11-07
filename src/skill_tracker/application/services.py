"""Application services: one method per use case, one transaction per method."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal

from ..domain.entities import Project, StudyLog, Topic
from ..domain.errors import EntityNotFoundError
from ..domain.value_objects import ProjectStatus, StudyHours
from .dto import DashboardSummary, ProjectInput, StudyLogInput, TopicInput
from .unit_of_work import UnitOfWork

UnitOfWorkFactory = Callable[[], UnitOfWork]


class TopicService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_topics(self) -> list[Topic]:
        with self._uow_factory() as uow:
            return uow.topics.list()

    def create_topic(self, data: TopicInput) -> Topic:
        topic = Topic.create(
            title=data.title,
            category=data.category,
            color=data.color,
            description=data.description,
            notes=data.notes,
        )
        with self._uow_factory() as uow:
            uow.topics.add(topic)
        return topic

    def update_topic(self, topic_id: str, data: TopicInput) -> Topic:
        with self._uow_factory() as uow:
            topic = uow.topics.get(topic_id)
            topic.update_details(
                title=data.title,
                category=data.category,
                color=data.color,
                description=data.description,
                notes=data.notes,
            )
            uow.topics.update(topic)
            return topic

    def delete_topic(self, topic_id: str) -> None:
        with self._uow_factory() as uow:
            uow.topics.delete(topic_id)

    def add_module(self, topic_id: str, title: str) -> Topic:
        with self._uow_factory() as uow:
            topic = uow.topics.get(topic_id)
            topic.add_module(title)
            uow.topics.update(topic)
            return topic

    def toggle_module(self, topic_id: str, module_id: str) -> Topic:
        with self._uow_factory() as uow:
            topic = uow.topics.get(topic_id)
            topic.toggle_module(module_id)
            uow.topics.update(topic)
            return topic


class ProjectService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_projects(self) -> list[Project]:
        with self._uow_factory() as uow:
            return uow.projects.list()

    def create_project(self, data: ProjectInput) -> Project:
        self._assert_topic_exists(data.topic_id)
        project = Project.create(
            title=data.title,
            topic_id=data.topic_id,
            status=data.status,
            target_date=data.target_date,
            repo_url=data.repo_url,
            tech_stack=data.tech_stack,
            description=data.description,
        )
        with self._uow_factory() as uow:
            uow.projects.add(project)
        return project

    def update_project(self, project_id: str, data: ProjectInput) -> Project:
        self._assert_topic_exists(data.topic_id)
        with self._uow_factory() as uow:
            project = uow.projects.get(project_id)
            project.update_details(
                title=data.title,
                topic_id=data.topic_id,
                status=data.status,
                target_date=data.target_date,
                repo_url=data.repo_url,
                tech_stack=data.tech_stack,
                description=data.description,
            )
            uow.projects.update(project)
            return project

    def delete_project(self, project_id: str) -> None:
        with self._uow_factory() as uow:
            uow.projects.delete(project_id)

    def add_task(self, project_id: str, title: str) -> Project:
        with self._uow_factory() as uow:
            project = uow.projects.get(project_id)
            project.add_task(title)
            uow.projects.update(project)
            return project

    def toggle_task(self, project_id: str, task_id: str) -> Project:
        with self._uow_factory() as uow:
            project = uow.projects.get(project_id)
            project.toggle_task(task_id)
            uow.projects.update(project)
            return project

    def _assert_topic_exists(self, topic_id: str | None) -> None:
        if not topic_id:
            return
        with self._uow_factory() as uow:
            uow.topics.get(topic_id)


class StudyLogService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_logs(self) -> list[StudyLog]:
        with self._uow_factory() as uow:
            return uow.logs.list()

    def log_session(self, data: StudyLogInput) -> StudyLog:
        with self._uow_factory() as uow:
            topic = uow.topics.get(data.topic_id)
            project = self._find_project(uow, data.project_id)

            log = StudyLog.create(
                topic_id=topic.id,
                topic_title=topic.title,
                project_id=project.id if project else None,
                hours=data.hours,
                logged_on=data.logged_on or date.today(),
                note=data.note,
            )
            uow.logs.add(log)

            if project is not None:
                project.add_hours(StudyHours.parse(data.hours))
                uow.projects.update(project)

            return log

    @staticmethod
    def _find_project(uow: UnitOfWork, project_id: str | None) -> Project | None:
        if not project_id:
            return None
        return uow.projects.get(project_id)


class DashboardService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def summarise(self) -> DashboardSummary:
        with self._uow_factory() as uow:
            topics = uow.topics.list()
            projects = uow.projects.list()
            logs = uow.logs.list()

        total_modules = sum(topic.progress.total for topic in topics)
        completed_modules = sum(topic.progress.completed for topic in topics)
        active_projects = sum(
            1
            for project in projects
            if project.status in (ProjectStatus.ACTIVE, ProjectStatus.PLANNING)
        )
        total_hours = sum((log.hours for log in logs), Decimal(0))

        return DashboardSummary(
            active_topics_count=len(topics),
            total_modules=total_modules,
            completed_modules=completed_modules,
            module_completion_pct=(
                round(completed_modules / total_modules * 100) if total_modules else 0
            ),
            active_projects_count=active_projects,
            completed_projects_count=sum(
                1 for project in projects if project.status is ProjectStatus.COMPLETED
            ),
            total_hours_logged=total_hours,
            recent_logs=logs[:5],
        )


__all__ = [
    "DashboardService",
    "EntityNotFoundError",
    "ProjectService",
    "StudyLogService",
    "TopicService",
    "UnitOfWorkFactory",
]
