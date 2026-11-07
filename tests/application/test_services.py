from decimal import Decimal

import pytest

from skill_tracker.application.dto import ProjectInput, StudyLogInput, TopicInput
from skill_tracker.application.services import (
    DashboardService,
    ProjectService,
    StudyLogService,
    TopicService,
)
from skill_tracker.domain.errors import EntityNotFoundError, ValidationError
from skill_tracker.infrastructure.database import initialise_database
from skill_tracker.infrastructure.sqlite_unit_of_work import SqliteUnitOfWork


@pytest.fixture()
def factory(tmp_path):
    db_path = tmp_path / "test.db"
    initialise_database(db_path)

    def make_uow() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    return make_uow


@pytest.fixture()
def topics(factory) -> TopicService:
    return TopicService(factory)


@pytest.fixture()
def projects(factory) -> ProjectService:
    return ProjectService(factory)


@pytest.fixture()
def logs(factory) -> StudyLogService:
    return StudyLogService(factory)


def test_topic_crud_roundtrip(topics: TopicService) -> None:
    created = topics.create_topic(
        TopicInput(title="Databases", category="Engineering", color="cyan", notes="Index wisely")
    )

    listed = topics.list_topics()
    assert [topic.title for topic in listed] == ["Databases"]
    assert listed[0].color.value == "cyan"

    updated = topics.update_topic(
        created.id,
        TopicInput(title="Databases II", category="Engineering", color="blue"),
    )
    assert updated.title == "Databases II"

    topics.delete_topic(created.id)
    assert topics.list_topics() == []

    with pytest.raises(EntityNotFoundError):
        topics.delete_topic(created.id)


def test_add_and_toggle_module_persists(topics: TopicService) -> None:
    topic = topics.create_topic(TopicInput(title="Algorithms"))
    topic = topics.add_module(topic.id, "Dynamic programming")

    module_id = topic.modules[0].id
    toggled = topics.toggle_module(topic.id, module_id)

    assert toggled.modules[0].completed is True
    assert topics.list_topics()[0].modules[0].completed is True


def test_project_requires_existing_topic(projects: ProjectService) -> None:
    with pytest.raises(EntityNotFoundError):
        projects.create_project(ProjectInput(title="Ghost", topic_id="does-not-exist"))


def test_project_crud(projects: ProjectService, topics: TopicService) -> None:
    topic = topics.create_topic(TopicInput(title="Rust"))
    project = projects.create_project(
        ProjectInput(
            title="CLI",
            topic_id=topic.id,
            status="Planning",
            target_date="2027-01-01",
            tech_stack=["Rust", "SQLite"],
        )
    )

    assert project.status.value == "Planning"
    assert project.tech_stack == ["Rust", "SQLite"]

    project = projects.add_task(project.id, "Sketch CLI")
    task_id = project.tasks[0].id
    project = projects.toggle_task(project.id, task_id)
    assert project.tasks[0].completed is True

    updated = projects.update_project(
        project.id, ProjectInput(title="CLI v2", topic_id=topic.id, status="Active")
    )
    assert updated.title == "CLI v2"
    assert updated.status.value == "Active"


def test_study_log_adds_hours_to_linked_project(
    factory, topics: TopicService, projects: ProjectService, logs: StudyLogService
) -> None:
    topic = topics.create_topic(TopicInput(title="Kafka"))
    project = projects.create_project(
        ProjectInput(title="Pipeline", topic_id=topic.id, status="Active")
    )

    log = logs.log_session(
        StudyLogInput(
            topic_id=topic.id,
            project_id=project.id,
            hours="1.5",
            logged_on="2026-11-07",
            note="Consumer groups",
        )
    )

    assert log.topic_title == "Kafka"
    assert log.hours == Decimal("1.50")

    refreshed = projects.list_projects()[0]
    assert refreshed.hours_spent == Decimal("1.50")


def test_study_log_rejects_zero_hours(logs: StudyLogService, topics: TopicService) -> None:
    topic = topics.create_topic(TopicInput(title="Math"))
    with pytest.raises(ValidationError):
        logs.log_session(StudyLogInput(topic_id=topic.id, hours="0"))


def test_dashboard_summary(factory, topics, projects, logs) -> None:
    topic = topics.create_topic(TopicInput(title="Networks"))
    topic = topics.add_module(topic.id, "TCP")
    topics.toggle_module(topic.id, topic.modules[0].id)

    projects.create_project(ProjectInput(title="Chat", topic_id=topic.id, status="Active"))
    projects.create_project(ProjectInput(title="Blog", topic_id=None, status="Completed"))
    logs.log_session(StudyLogInput(topic_id=topic.id, hours="2"))

    summary = DashboardService(factory).summarise()

    assert summary.active_topics_count == 1
    assert summary.total_modules == 1
    assert summary.completed_modules == 1
    assert summary.module_completion_pct == 100
    assert summary.active_projects_count == 1
    assert summary.completed_projects_count == 1
    assert summary.total_hours_logged == Decimal("2.00")
    assert len(summary.recent_logs) == 1
