PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS topics (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL,
    color       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
    id        TEXT PRIMARY KEY,
    topic_id  TEXT NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    title     TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
    position  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_modules_topic ON modules (topic_id, position);

CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    topic_id    TEXT REFERENCES topics (id) ON DELETE SET NULL,
    status      TEXT NOT NULL CHECK (status IN ('Planning', 'Active', 'Paused', 'Completed')),
    target_date TEXT,
    hours_spent REAL NOT NULL DEFAULT 0 CHECK (hours_spent >= 0),
    repo_url    TEXT,
    tech_stack  TEXT NOT NULL DEFAULT '[]',
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_topic ON projects (topic_id);

CREATE TABLE IF NOT EXISTS tasks (
    id         TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    completed  INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
    position   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks (project_id, position);

CREATE TABLE IF NOT EXISTS study_logs (
    id          TEXT PRIMARY KEY,
    topic_id    TEXT REFERENCES topics (id) ON DELETE SET NULL,
    topic_title TEXT NOT NULL,
    project_id  TEXT REFERENCES projects (id) ON DELETE SET NULL,
    hours       REAL NOT NULL CHECK (hours > 0),
    logged_on   TEXT NOT NULL,
    note        TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_logged_on ON study_logs (logged_on DESC, created_at DESC);
