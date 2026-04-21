"""Сервис задач — BAZA BOT."""
from models.database import get_db


async def create_task(user_id: int, title: str, description: str = None,
                      project_id: int = None, priority: str = "medium", due_date: str = None) -> dict:
    async with await get_db() as db:
        cursor = await db.execute(
            """INSERT INTO tasks (user_id, project_id, title, description, priority, due_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, project_id, title, description, priority, due_date)
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
        )).fetchone()
        return dict(row)


async def get_tasks(user_id: int, project_id: int = None,
                    status: str = None, limit: int = 20) -> list[dict]:
    async with await get_db() as db:
        conditions = ["t.user_id = ?"]
        values = [user_id]
        if project_id:
            conditions.append("t.project_id = ?")
            values.append(project_id)
        if status:
            conditions.append("t.status = ?")
            values.append(status)
        where = " AND ".join(conditions)
        rows = await (await db.execute(
            f"""SELECT t.*, p.name as project_name FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE {where}
                ORDER BY
                  CASE t.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                  t.due_date ASC NULLS LAST,
                  t.created_at DESC
                LIMIT ?""",
            values + [limit]
        )).fetchall()
        return [dict(r) for r in rows]


async def update_task_status(task_id: int, user_id: int, status: str) -> dict | None:
    async with await get_db() as db:
        await db.execute(
            "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (status, task_id, user_id)
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        )).fetchone()
        return dict(row) if row else None


async def assign_task_to_project(task_id: int, user_id: int, project_id: int) -> bool:
    async with await get_db() as db:
        result = await db.execute(
            "UPDATE tasks SET project_id = ? WHERE id = ? AND user_id = ?",
            (project_id, task_id, user_id)
        )
        await db.commit()
        return result.rowcount > 0


async def delete_task(task_id: int, user_id: int):
    async with await get_db() as db:
        await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        )
        await db.commit()


PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_EMOJI = {"todo": "📋", "in_progress": "⚡", "done": "✅"}
