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
- Excel backup and restore: export everything to `.xlsx`, import it back to restore
- Typed domain model with validation and unit/API tests

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management and running commands

`uv` can install the required Python version for you with `uv python install 3.13`.

## Quick start

```bash
uv sync
uv run skill-tracker
# or: uv run uvicorn skill_tracker.presentation.app:app --reload
```

Open <http://127.0.0.1:8000>. The database is created and seeded automatically on first run.

`uv sync` installs the runtime dependencies plus the `dev` dependency group from the committed `uv.lock`, so every machine resolves the same versions.

## Architecture

```
src/skill_tracker/
  domain/          Entities, value objects, repository ports, domain errors
  application/     Use-case services, DTOs, Unit of Work port, Excel transfer service
  infrastructure/  SQLite schema, repositories, Unit of Work, seed data, openpyxl codec
  presentation/    FastAPI routes, Pydantic schemas, app composition root
web/               Static SPA (HTML + vanilla JS + Tailwind CDN)
tests/             Domain, application, and HTTP tests
```

Dependencies point inward: `presentation -> application -> domain`, and `infrastructure` implements ports owned by the inner layers. The domain has no framework or database imports.

The Excel codec is a port in `application/transfer.py` implemented by `infrastructure/excel_codec.py`, so `TransferService` and its tests do not depend on `openpyxl`.

### Data model

| Entity | Relationships |
| --- | --- |
| `Topic` | Has ordered `Module`s; owns category and color tokens |
| `Project` | Optionally linked to a `Topic`; has ordered `Task`s |
| `StudyLog` | Optionally references a `Topic` and `Project`; stores `topicTitle` and quarter-hour `hours` |

Deleting a topic removes its modules and detaches linked projects and logs. Deleting a project removes its tasks and detaches logs.

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
| `GET` | `/api/export` | Download all data as an `.xlsx` workbook |
| `POST` | `/api/import` | Restore all data from an uploaded `.xlsx` workbook |

Interactive docs are available at `/docs`.

### Example

```bash
TOPIC=$(curl -s -X POST http://127.0.0.1:8000/api/topics \
  -H 'Content-Type: application/json' \
  -d '{"title":"Compilers","category":"Engineering","color":"cyan"}' | jq -r .id)

PROJECT=$(curl -s -X POST http://127.0.0.1:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d "{\"title\":\"Tiny compiler\",\"topicId\":\"$TOPIC\",\"techStack\":[\"Python\"]}" | jq -r .id)

curl -X POST http://127.0.0.1:8000/api/logs \
  -H 'Content-Type: application/json' \
  -d "{\"topicId\":\"$TOPIC\",\"projectId\":\"$PROJECT\",\"hours\":1.5,\"date\":\"2026-11-07\",\"note\":\"Lexer\"}"
```

## Excel backup and restore

`GET /api/export` returns a workbook with one sheet per entity:

| Sheet | Contents |
| --- | --- |
| `Topics` | id, title, category, color, description, notes |
| `Modules` | id, topicId, title, completed, position |
| `Projects` | id, title, topicId, status, targetDate, hoursSpent, repoUrl, techStack, description |
| `Tasks` | id, projectId, title, completed, position |
| `StudyLogs` | id, topicId, topicTitle, projectId, hours, date, note |

Export is a full backup. Import is a **restore**: it replaces all existing data inside a single transaction, keeping ids so the workbook round-trips exactly. Rows that reference a topic or project absent from the workbook are kept with that reference detached, matching normal cascade-delete behaviour.

Use the UI's Export and Import buttons or the API directly:

```bash
curl -O http://127.0.0.1:8000/api/export
curl -F "file=@skill-tracker-20261107.xlsx" http://127.0.0.1:8000/api/import
```

Notes for editing a workbook by hand:

- Keep the sheet names and header row unchanged; headers drive the import.
- Keep ids unique. Leave an id blank to let the app generate one.
- `position` orders modules and tasks within their parent (1-based).
- Dates use `YYYY-MM-DD`. Statuses are `Planning`, `Active`, `Paused`, or `Completed`.
- Colors are one of `indigo`, `blue`, `purple`, `emerald`, `amber`, `rose`, `slate`, `cyan`, `pink`.
- Hours are quantised to 0.25 and must be between 0.01 and 24 per log.
- `topicTitle` is required on every log row, even when `topicId` is present.
- Blank rows are ignored, and missing optional sheets are treated as empty.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SKILL_TRACKER_DB` | `./skill_tracker.db` | SQLite database path |
| `SKILL_TRACKER_WEB` | `./web` | Static frontend directory |
| `SKILL_TRACKER_HOST` | `127.0.0.1` | Server bind host |
| `SKILL_TRACKER_PORT` | `8000` | Server port |

## Development

```bash
uv sync
uv run uvicorn skill_tracker.presentation.app:app --reload
uv run pytest
uv run ruff check src tests
```

Tests use temporary SQLite databases and cover domain invariants, use-case transactions, Excel round-trips, and the HTTP API.

## License

MIT
