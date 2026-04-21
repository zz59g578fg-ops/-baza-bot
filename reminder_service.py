"""Сервис напоминаний — BAZA BOT."""
from datetime import datetime
from models.database import get_db


async def create_reminder(user_id: int, text: str, remind_at: datetime,
                          project_id: int = None, repeat: str = "none") -> dict:
    async with await get_db() as db:
        cursor = await db.execute(
            """INSERT INTO reminders (user_id, project_id, text, remind_at, repeat)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, project_id, text, remind_at.isoformat(), repeat)
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM reminders WHERE id = ?", (cursor.lastrowid,)
        )).fetchone()
        return dict(row)


async def get_pending_reminders(user_id: int) -> list[dict]:
    async with await get_db() as db:
        rows = await (await db.execute(
            """SELECT r.*, p.name as project_name FROM reminders r
               LEFT JOIN projects p ON r.project_id = p.id
               WHERE r.user_id = ? AND r.is_done = 0
               ORDER BY r.remind_at ASC""",
            (user_id,)
        )).fetchall()
        return [dict(r) for r in rows]


async def get_due_reminders() -> list[dict]:
    """Возвращает все просроченные напоминания (для планировщика)."""
    now = datetime.utcnow().isoformat()
    async with await get_db() as db:
        rows = await (await db.execute(
            """SELECT r.*, u.tg_id FROM reminders r
               JOIN users u ON r.user_id = u.id
               WHERE r.remind_at <= ? AND r.is_done = 0""",
            (now,)
        )).fetchall()
        return [dict(r) for r in rows]


async def mark_done(reminder_id: int):
    async with await get_db() as db:
        await db.execute(
            "UPDATE reminders SET is_done = 1 WHERE id = ?", (reminder_id,)
        )
        await db.commit()


async def reschedule_repeating(reminder: dict):
    """Сдвигает дату повторяющегося напоминания."""
    from datetime import timedelta
    repeat = reminder.get("repeat", "none")
    if repeat == "none":
        return
    old_dt = datetime.fromisoformat(reminder["remind_at"])
    if repeat == "daily":
        new_dt = old_dt + timedelta(days=1)
    elif repeat == "weekly":
        new_dt = old_dt + timedelta(weeks=1)
    elif repeat == "monthly":
        # Примерно +30 дней
        new_dt = old_dt + timedelta(days=30)
    else:
        return
    async with await get_db() as db:
        await db.execute(
            "UPDATE reminders SET remind_at = ?, is_done = 0 WHERE id = ?",
            (new_dt.isoformat(), reminder["id"])
        )
        await db.commit()


async def delete_reminder(reminder_id: int, user_id: int):
    async with await get_db() as db:
        await db.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id)
        )
        await db.commit()
