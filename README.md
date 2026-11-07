# SkillTrack Studio

A personal learning and project tracker built with **Python**, **FastAPI**, and **SQLite**. The backend follows a **Domain-Driven Design** layout with clear separation between domain rules, use cases, persistence, and HTTP.

Track learning topics and modules, manage side projects and tasks, log study sessions, and see progress on a live dashboard.

## Features

- Learning topics with ordered modules and completion progress
- Projects linked to topics, with task checklists, status, and target dates
- Study session logs with automatic project-hour accumulation
- Dashboard summary: active topics/projects, module completion, total hours, recent activity
- Dark mode and a responsive, build-free single-page UI
- SQLite persistence with transactions, foreign keys, and cascading deletes
- Typed domain model with validation and unit/API tests

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

skill-tracker
# or: PYTHONPATH=src uvicorn skill_tracker.presentation.app:app --reload
```

Open <http://127.0.0.1:8000>. The database is created and seeded automatically on first run.

## Architecture

```
src/skill_tracker/
  domain/          Entities, value objects, repository ports, domain errors
  application/     Use-case services, DTOs, Unit of Work port
  infrastructure/  SQLite schema, repositories, Unit of Work, seed data
  presentation/    FastAPI routes, Pydantic schemas, app composition root
web/               Static SPA (HTML + vanilla JS + Tailwind CDN)
tests/             Domain, application, and HTTP tests
```

Dependencies point inward: `presentation -> application -> domain`, and `infrastructure` implements ports owned by the inner layers. The domain has no framework or database imports.

## API

All endpoints are under `/api`. Request and response fields use camelCase.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/dashboard` | Dashboard summary and recent logs |
| `GET` | `/api/topics` | List learning topics |
| `POST` | `/api/topics` | Create a topic |
| `PUT` | `/api/topics/{id}` | Update a topic |
| `DELETE` | `/api/topics/{id}` | Delete a topic |
| `POST` | `/api/topics/{id}/modules` | Add a module |
| `PATCH` | `/api/topics/{id}/modules/{moduleId}/toggle` | Toggle module completion |
| `GET` | `/api/projects` | List projects |
| `POST` | `/api/projects` | Create a project |
| `PUT` | `/api/projects/{id}` | Update a project |
| `DELETE` | `/api/projects/{id}` | Delete a project |
| `POST` | `/api/projects/{id}/tasks` | Add a task |
| `PATCH` | `/api/projects/{id}/tasks/{taskId}/toggle` | Toggle task completion |
| `GET` | `/api/logs` | List study logs |
| `POST` | `/api/logs` | Log a study session |

Interactive docs are available at `/docs`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SKILL_TRACKER_DB` | `./skill_tracker.db` | SQLite database path |
| `SKILL_TRACKER_WEB` | `./web` | Static frontend directory |
| `SKILL_TRACKER_HOST` | `127.0.0.1` | Server bind host |
| `SKILL_TRACKER_PORT` | `8000` | Server port |

## Testing

```bash
python3 -m pytest
ruff check src tests
```

Tests use temporary SQLite databases and cover domain invariants, use-case transactions, and the HTTP API.

## License

MIT
