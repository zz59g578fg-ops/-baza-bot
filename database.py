"""
Database layer — SQLite через aiosqlite.
Таблицы: users, projects, notes, reminders, tasks
"""
import aiosqlite
import os
from datetime import datetime

DB_PATH = os.getenv("DATABASE_PATH", "data/assistant.db")


async def get_db() -> aiosqlite.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Создаёт все таблицы при первом запуске."""
    async with await get_db() as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY,
            tg_id       INTEGER UNIQUE NOT NULL,
            username    TEXT,
            full_name   TEXT,
            timezone    TEXT DEFAULT 'Europe/Moscow',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT NOT NULL,
            description TEXT,
            color       TEXT DEFAULT '#4f8ef7',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            title       TEXT,
            content     TEXT NOT NULL,
            tags        TEXT DEFAULT '[]',
            source      TEXT DEFAULT 'text',   -- 'text' | 'voice'
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            text        TEXT NOT NULL,
            remind_at   TEXT NOT NULL,
            repeat      TEXT DEFAULT 'none',   -- 'none'|'daily'|'weekly'|'monthly'
            is_done     INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            title       TEXT NOT NULL,
            description TEXT,
            priority    TEXT DEFAULT 'medium', -- 'low'|'medium'|'high'
            status      TEXT DEFAULT 'todo',   -- 'todo'|'in_progress'|'done'
            due_date    TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
        CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
        """)
        await db.commit()
    print("✅ Database initialized")
