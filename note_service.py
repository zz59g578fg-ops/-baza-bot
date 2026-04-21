"""Сервис заметок — BAZA BOT."""
import json
from models.database import get_db


async def create_note(user_id: int, content: str, title: str = None,
                      project_id: int = None, tags: list = None, source: str = "text") -> dict:
    async with await get_db() as db:
        cursor = await db.execute(
            """INSERT INTO notes (user_id, project_id, title, content, tags, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, project_id, title, content, json.dumps(tags or []), source)
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM notes WHERE id = ?", (cursor.lastrowid,)
        )).fetchone()
        return dict(row)


async def get_notes(user_id: int, project_id: int = None, limit: int = 10, offset: int = 0) -> list[dict]:
    async with await get_db() as db:
        if project_id:
            rows = await (await db.execute(
                "SELECT * FROM notes WHERE user_id = ? AND project_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, project_id, limit, offset)
            )).fetchall()
        else:
            rows = await (await db.execute(
                "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset)
            )).fetchall()
        return [dict(r) for r in rows]


async def search_notes(user_id: int, query: str) -> list[dict]:
    async with await get_db() as db:
        rows = await (await db.execute(
            """SELECT * FROM notes
               WHERE user_id = ? AND (content LIKE ? OR title LIKE ? OR tags LIKE ?)
               ORDER BY created_at DESC LIMIT 20""",
            (user_id, f"%{query}%", f"%{query}%", f"%{query}%")
        )).fetchall()
        return [dict(r) for r in rows]


async def delete_note(note_id: int, user_id: int):
    async with await get_db() as db:
        await db.execute(
            "DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id)
        )
        await db.commit()


async def update_note(note_id: int, user_id: int, **fields) -> dict | None:
    allowed = {"title", "content", "project_id", "tags"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return None
    if "tags" in updates:
        updates["tags"] = json.dumps(updates["tags"])
    updates["updated_at"] = "datetime('now')"
    set_clause = ", ".join(f"{k} = ?" for k in updates if k != "updated_at")
    set_clause += ", updated_at = datetime('now')"
    values = [v for k, v in updates.items() if k != "updated_at"]
    values += [note_id, user_id]
    async with await get_db() as db:
        await db.execute(
            f"UPDATE notes SET {set_clause} WHERE id = ? AND user_id = ?", values
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        )).fetchone()
        return dict(row) if row else None
