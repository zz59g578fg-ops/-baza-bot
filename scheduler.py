"""
Планировщик напоминаний — BAZA BOT.
Каждую минуту проверяет БД и отправляет напоминания в Telegram.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from services.reminder_service import get_due_reminders, mark_done, reschedule_repeating

scheduler = AsyncIOScheduler()


async def check_and_send_reminders(bot: Bot):
    """Проверяет и рассылает напоминания."""
    due = await get_due_reminders()
    for reminder in due:
        try:
            project_label = f"\n📁 Проект: <b>{reminder.get('project_name', '')}</b>" \
                if reminder.get("project_name") else ""
            repeat_label = ""
            if reminder.get("repeat") and reminder["repeat"] != "none":
                repeats = {"daily": "ежедневно", "weekly": "каждую неделю", "monthly": "каждый месяц"}
                repeat_label = f"\n🔁 Повтор: {repeats.get(reminder['repeat'], reminder['repeat'])}"

            text = (
                f"⏰ <b>Напоминание!</b>\n\n"
                f"{reminder['text']}"
                f"{project_label}"
                f"{repeat_label}"
            )
            await bot.send_message(
                chat_id=reminder["tg_id"],
                text=text,
                parse_mode="HTML",
            )

            if reminder.get("repeat") and reminder["repeat"] != "none":
                await reschedule_repeating(reminder)
            else:
                await mark_done(reminder["id"])

        except Exception as e:
            print(f"[Scheduler] Ошибка отправки reminder {reminder['id']}: {e}")


def start_scheduler(bot: Bot):
    scheduler.add_job(
        check_and_send_reminders,
        trigger=IntervalTrigger(minutes=1),
        args=[bot],
        id="reminder_check",
        replace_existing=True,
    )
    scheduler.start()
    print("✅ Планировщик запущен")


def stop_scheduler():
    scheduler.shutdown(wait=False)
