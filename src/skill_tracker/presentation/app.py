"""FastAPI application factory and composition root."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..application.services import (
    DashboardService,
    ProjectService,
    StudyLogService,
    TopicService,
)
from ..config import database_path, static_dir
from ..domain.errors import EntityNotFoundError, ValidationError
from ..infrastructure.database import initialise_database
from ..infrastructure.seed import seed_if_empty
from ..infrastructure.sqlite_unit_of_work import SqliteUnitOfWork
from .api import router as api_router


def create_app(db_path: str | Path | None = None) -> FastAPI:
    resolved_db = Path(db_path) if db_path is not None else database_path()
    initialise_database(resolved_db)

    def uow_factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(resolved_db)

    seed_if_empty(uow_factory)

    app = FastAPI(
        title="SkillTracker API",
        version="1.0.0",
        description="Learning and project tracker with a DDD-oriented SQLite backend.",
    )
    app.state.uow_factory = uow_factory
    app.state.topic_service = TopicService(uow_factory)
    app.state.project_service = ProjectService(uow_factory)
    app.state.log_service = StudyLogService(uow_factory)
    app.state.dashboard_service = DashboardService(uow_factory)

    @app.exception_handler(ValidationError)
    def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(EntityNotFoundError)
    def handle_not_found(_: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/api/health", tags=["skill-tracker"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)

    web_root = static_dir()
    if web_root.is_dir():
        app.mount("/", StaticFiles(directory=web_root, html=True), name="web")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "skill_tracker.presentation.app:app",
        host=os.getenv("SKILL_TRACKER_HOST", "127.0.0.1"),
        port=int(os.getenv("SKILL_TRACKER_PORT", "8000")),
    )
