"""Сервис управления проектами — BAZA BOT."""
from models.database import get_db


async def create_project(user_id: int, name: str, description: str = None, color: str = "#4f8ef7") -> dict:
    async with await get_db() as db:
        cursor = await db.execute(
            "INSERT INTO projects (user_id, name, description, color) VALUES (?, ?, ?, ?)",
            (user_id, name, description, color)
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,)
        )).fetchone()
        return dict(row)


async def get_projects(user_id: int) -> list[dict]:
    async with await get_db() as db:
        rows = await (await db.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        )).fetchall()
        return [dict(r) for r in rows]


async def get_project(project_id: int, user_id: int) -> dict | None:
    async with await get_db() as db:
        row = await (await db.execute(
            "SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
        )).fetchone()
        return dict(row) if row else None


async def delete_project(project_id: int, user_id: int):
    async with await get_db() as db:
        await db.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
        )
        await db.commit()


async def get_project_stats(project_id: int) -> dict:
    async with await get_db() as db:
        tasks_total = (await (await db.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE project_id = ?", (project_id,)
        )).fetchone())["c"]
        tasks_done = (await (await db.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE project_id = ? AND status = 'done'", (project_id,)
        )).fetchone())["c"]
        notes_count = (await (await db.execute(
            "SELECT COUNT(*) as c FROM notes WHERE project_id = ?", (project_id,)
        )).fetchone())["c"]
        reminders_count = (await (await db.execute(
            "SELECT COUNT(*) as c FROM reminders WHERE project_id = ? AND is_done = 0", (project_id,)
        )).fetchone())["c"]
        return {
            "tasks_total": tasks_total,
            "tasks_done": tasks_done,
            "notes_count": notes_count,
            "active_reminders": reminders_count,
        }
