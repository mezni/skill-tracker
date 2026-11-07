from decimal import Decimal

import pytest

from skill_tracker.domain.entities import Project, StudyLog, Topic
from skill_tracker.domain.errors import EntityNotFoundError, ValidationError
from skill_tracker.domain.value_objects import ProjectStatus, StudyHours, TopicColor


def test_topic_tracks_module_progress() -> None:
    topic = Topic.create("Distributed Systems", category="Engineering")
    first = topic.add_module("Caching")
    second = topic.add_module("Queues")

    assert topic.progress.total == 2
    assert topic.progress.percentage == 0

    topic.toggle_module(first.id)
    assert topic.find_module(first.id).completed is True
    assert topic.progress.completed == 1
    assert topic.progress.percentage == 50

    topic.toggle_module(first.id)
    assert second.completed is False
    assert topic.progress.percentage == 0


def test_topic_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        Topic.create("   ")


def test_topic_color_accepts_legacy_css_token() -> None:
    topic = Topic.create("Design", color="bg-blue-500")
    assert topic.color is TopicColor.BLUE


def test_toggling_unknown_module_raises() -> None:
    topic = Topic.create("Design")
    with pytest.raises(EntityNotFoundError):
        topic.toggle_module("missing")


def test_project_status_is_validated() -> None:
    with pytest.raises(ValidationError):
        Project.create("Portfolio", status="Almost done")


def test_project_adds_study_hours() -> None:
    project = Project.create("Portfolio", hours_spent=2)
    project.add_hours(StudyHours.parse("1.5"))
    assert project.hours_spent == Decimal("3.50")


def test_project_task_progress() -> None:
    project = Project.create("Portfolio")
    task = project.add_task("Ship it")
    assert project.task_progress.percentage == 0
    project.toggle_task(task.id)
    assert project.task_progress.percentage == 100


def test_study_hours_rejects_invalid_values() -> None:
    for value in (0, -1, "abc", 25):
        with pytest.raises(ValidationError):
            StudyHours.parse(value)


def test_study_hours_quantise_to_quarters() -> None:
    assert StudyHours.parse("1.3").value == Decimal("1.25")


def test_study_log_keeps_topic_snapshot() -> None:
    log = StudyLog.create(
        topic_id="t1",
        topic_title="System Design",
        hours="2",
        logged_on="2026-11-07",
        note="Consistent hashing",
    )
    assert log.topic_title == "System Design"
    assert log.hours == Decimal("2.00")
    assert log.logged_on.isoformat() == "2026-11-07"


def test_project_status_enum_values() -> None:
    assert ProjectStatus.parse("Planning") is ProjectStatus.PLANNING
    assert ProjectStatus.parse(ProjectStatus.COMPLETED) is ProjectStatus.COMPLETED
