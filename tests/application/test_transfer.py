from decimal import Decimal

import pytest

from skill_tracker.application.dto import ProjectInput, StudyLogInput, TopicInput
from skill_tracker.application.services import (
    ProjectService,
    StudyLogService,
    TopicService,
)
from skill_tracker.application.transfer import TrackerSnapshot, TransferService
from skill_tracker.domain.entities import Project, StudyLog, Topic
from skill_tracker.infrastructure.database import initialise_database
from skill_tracker.infrastructure.excel_codec import OpenpyxlExcelCodec
from skill_tracker.infrastructure.sqlite_unit_of_work import SqliteUnitOfWork


@pytest.fixture()
def factory(tmp_path):
    db_path = tmp_path / "transfer.db"
    initialise_database(db_path)

    def make_uow() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    return make_uow


@pytest.fixture()
def service(factory) -> TransferService:
    return TransferService(factory, OpenpyxlExcelCodec())


def _seed(factory) -> None:
    topics = TopicService(factory)
    projects = ProjectService(factory)
    logs = StudyLogService(factory)

    topic = topics.create_topic(
        TopicInput(
            title="Databases",
            category="Engineering",
            color="cyan",
            description="Storage engines",
            notes="Index wisely",
        )
    )
    topics.add_module(topic.id, "B-trees")
    module = topics.add_module(topic.id, "WAL").modules[-1]
    topics.toggle_module(topic.id, module.id)

    project = projects.create_project(
        ProjectInput(
            title="Query planner",
            topic_id=topic.id,
            status="Planning",
            target_date="2027-03-01",
            repo_url="https://example.com/planner",
            tech_stack=["Rust", "SQLite"],
            description="Cost based planner",
        )
    )
    projects.add_task(project.id, "Sketch path costs")
    task = projects.add_task(project.id, "Benchmark").tasks[-1]
    projects.toggle_task(project.id, task.id)

    logs.log_session(
        StudyLogInput(
            topic_id=topic.id,
            project_id=project.id,
            hours=1.5,
            logged_on="2026-11-01",
            note="Read the WAL paper",
        )
    )


def test_export_then_import_restores_every_sheet(service: TransferService, factory) -> None:
    _seed(factory)
    workbook = service.export()
    assert workbook.startswith(b"PK")

    summary = service.import_(workbook)

    assert summary.topics_imported == 1
    assert summary.projects_imported == 1
    assert summary.logs_imported == 1

    with factory() as uow:
        topics = uow.topics.list()
        projects = uow.projects.list()
        logs = uow.logs.list()

    assert [topic.title for topic in topics] == ["Databases"]
    assert [module.title for module in topics[0].modules] == ["B-trees", "WAL"]
    assert topics[0].modules[1].completed is True
    assert topics[0].color.value == "cyan"
    assert projects[0].status.value == "Planning"
    assert projects[0].topic_id == topics[0].id
    assert [task.title for task in projects[0].tasks] == ["Sketch path costs", "Benchmark"]
    assert projects[0].tasks[1].completed is True
    assert projects[0].hours_spent == Decimal("1.5")
    assert logs[0].topic_id == topics[0].id
    assert logs[0].project_id == projects[0].id
    assert logs[0].logged_on.isoformat() == "2026-11-01"
    assert logs[0].note == "Read the WAL paper"


def test_import_replaces_existing_data(service: TransferService, factory) -> None:
    _seed(factory)
    workbook = service.export()

    with factory() as uow:
        uow.topics.add(Topic.create("Scratch"))
        uow.projects.add(Project.create("Throwaway"))

    service.import_(workbook)

    with factory() as uow:
        assert [topic.title for topic in uow.topics.list()] == ["Databases"]
        assert [project.title for project in uow.projects.list()] == ["Query planner"]
        assert len(uow.logs.list()) == 1


def test_import_detaches_unknown_references(service: TransferService, factory) -> None:
    snapshot = TrackerSnapshot(
        topics=[Topic.create("Kernel", topic_id="topic-1")],
        projects=[Project.create("Drivers", topic_id="missing", project_id="project-1")],
        logs=[
            StudyLog.create(
                topic_id="missing",
                topic_title="Ghost",
                project_id="missing-project",
                hours=1,
                logged_on="2026-11-02",
                log_id="log-1",
            )
        ],
    )

    service.import_(OpenpyxlExcelCodec().encode(snapshot))

    with factory() as uow:
        projects = uow.projects.list()
        logs = uow.logs.list()

    assert projects[0].topic_id is None
    assert logs[0].topic_id is None
    assert logs[0].project_id is None
    assert logs[0].topic_title == "Ghost"
