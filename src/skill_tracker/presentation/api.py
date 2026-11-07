"""HTTP routes. This module only translates HTTP <-> application services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status

from ..application.dto import ProjectInput, StudyLogInput, TopicInput
from ..application.services import (
    DashboardService,
    ProjectService,
    StudyLogService,
    TopicService,
)
from ..application.transfer import TransferService
from .schemas import (
    ChecklistItemIn,
    DashboardOut,
    ImportSummaryOut,
    ProjectIn,
    ProjectOut,
    StudyLogIn,
    StudyLogOut,
    TopicIn,
    TopicOut,
)

router = APIRouter(prefix="/api", tags=["skill-tracker"])


def _topic_service(request: Request) -> TopicService:
    return request.app.state.topic_service


def _project_service(request: Request) -> ProjectService:
    return request.app.state.project_service


def _log_service(request: Request) -> StudyLogService:
    return request.app.state.log_service


def _dashboard_service(request: Request) -> DashboardService:
    return request.app.state.dashboard_service


def _transfer_service(request: Request) -> TransferService:
    return request.app.state.transfer_service


TopicServiceDep = Annotated[TopicService, Depends(_topic_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(_project_service)]
StudyLogServiceDep = Annotated[StudyLogService, Depends(_log_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(_dashboard_service)]
TransferServiceDep = Annotated[TransferService, Depends(_transfer_service)]


def _to_topic_input(data: TopicIn) -> TopicInput:
    return TopicInput(
        title=data.title,
        category=data.category,
        color=data.color,
        description=data.description,
        notes=data.notes,
    )


def _to_project_input(data: ProjectIn) -> ProjectInput:
    return ProjectInput(
        title=data.title,
        topic_id=data.topic_id,
        status=data.status,
        target_date=data.target_date,
        repo_url=data.repo_url,
        tech_stack=data.tech_stack,
        description=data.description,
    )


# --- Dashboard -------------------------------------------------------------
@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(service: DashboardServiceDep) -> DashboardOut:
    return DashboardOut.from_summary(service.summarise())


# --- Topics ----------------------------------------------------------------
@router.get("/topics", response_model=list[TopicOut])
def list_topics(service: TopicServiceDep) -> list[TopicOut]:
    return [TopicOut.from_entity(topic) for topic in service.list_topics()]


@router.post("/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
def create_topic(
    data: TopicIn, service: TopicServiceDep
) -> TopicOut:
    return TopicOut.from_entity(service.create_topic(_to_topic_input(data)))


@router.put("/topics/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: str, data: TopicIn, service: TopicServiceDep
) -> TopicOut:
    return TopicOut.from_entity(service.update_topic(topic_id, _to_topic_input(data)))


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic_id: str, service: TopicServiceDep) -> Response:
    service.delete_topic(topic_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/topics/{topic_id}/modules",
    response_model=TopicOut,
    status_code=status.HTTP_201_CREATED,
)
def add_module(
    topic_id: str, data: ChecklistItemIn, service: TopicServiceDep
) -> TopicOut:
    return TopicOut.from_entity(service.add_module(topic_id, data.title))


@router.patch("/topics/{topic_id}/modules/{module_id}/toggle", response_model=TopicOut)
def toggle_module(
    topic_id: str, module_id: str, service: TopicServiceDep
) -> TopicOut:
    return TopicOut.from_entity(service.toggle_module(topic_id, module_id))


# --- Projects --------------------------------------------------------------
@router.get("/projects", response_model=list[ProjectOut])
def list_projects(service: ProjectServiceDep) -> list[ProjectOut]:
    return [ProjectOut.from_entity(project) for project in service.list_projects()]


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectIn, service: ProjectServiceDep
) -> ProjectOut:
    return ProjectOut.from_entity(service.create_project(_to_project_input(data)))


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str, data: ProjectIn, service: ProjectServiceDep
) -> ProjectOut:
    return ProjectOut.from_entity(service.update_project(project_id, _to_project_input(data)))


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str, service: ProjectServiceDep
) -> Response:
    service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/projects/{project_id}/tasks",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
def add_task(
    project_id: str, data: ChecklistItemIn, service: ProjectServiceDep
) -> ProjectOut:
    return ProjectOut.from_entity(service.add_task(project_id, data.title))


@router.patch("/projects/{project_id}/tasks/{task_id}/toggle", response_model=ProjectOut)
def toggle_task(
    project_id: str, task_id: str, service: ProjectServiceDep
) -> ProjectOut:
    return ProjectOut.from_entity(service.toggle_task(project_id, task_id))


# --- Study logs ------------------------------------------------------------
@router.get("/logs", response_model=list[StudyLogOut])
def list_logs(service: StudyLogServiceDep) -> list[StudyLogOut]:
    return [StudyLogOut.from_entity(log) for log in service.list_logs()]


@router.post("/logs", response_model=StudyLogOut, status_code=status.HTTP_201_CREATED)
def create_log(data: StudyLogIn, service: StudyLogServiceDep) -> StudyLogOut:
    log = service.log_session(
        StudyLogInput(
            topic_id=data.topic_id,
            project_id=data.project_id,
            hours=data.hours,
            logged_on=data.date,
            note=data.note,
        )
    )
    return StudyLogOut.from_entity(log)


# --- Excel import / export -------------------------------------------------
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/export", response_class=Response, tags=["transfer"])
def export_workbook(service: TransferServiceDep) -> Response:
    content = service.export()
    filename = f"skill-tracker-{datetime.now(UTC).date():%Y%m%d}.xlsx"
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/import",
    response_model=ImportSummaryOut,
    status_code=status.HTTP_200_OK,
    tags=["transfer"],
)
async def import_workbook(
    service: TransferServiceDep,
    file: Annotated[UploadFile, File()],
) -> ImportSummaryOut:
    data = await file.read()
    return ImportSummaryOut.from_summary(service.import_(data))
