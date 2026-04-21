"""Сервис управления пользователями."""
from models.database import get_db


async def get_or_create_user(tg_id: int, username: str = None, full_name: str = None) -> dict:
    async with await get_db() as db:
        row = await (await db.execute(
            "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
        )).fetchone()

        if row:
            return dict(row)

        await db.execute(
            "INSERT INTO users (tg_id, username, full_name) VALUES (?, ?, ?)",
            (tg_id, username, full_name)
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
        )).fetchone()
        return dict(row)


async def get_user(tg_id: int) -> dict | None:
    async with await get_db() as db:
        row = await (await db.execute(
            "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
        )).fetchone()
        return dict(row) if row else None


async def update_timezone(tg_id: int, tz: str):
    async with await get_db() as db:
        await db.execute(
            "UPDATE users SET timezone = ? WHERE tg_id = ?", (tz, tg_id)
        )
        await db.commit()
