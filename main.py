"""
BAZA BOT — главный файл запуска.
Telegram-бот-ассистент: заметки, задачи, напоминания, голос, проекты.

Запуск:
  python main.py

Требования:
  pip install -r requirements.txt
  Скопируй .env.example → .env и заполни токены.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from models.database import init_db
from handlers.all_handlers import router
from services.scheduler import start_scheduler, stop_scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BAZA_BOT")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан в .env файле!")


async def main():
    logger.info("🚀 BAZA BOT запускается...")

    # Инициализация БД
    await init_db()

    # Создание бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Запуск планировщика напоминаний
    start_scheduler(bot)

    logger.info("✅ BAZA BOT запущен! Жду сообщений...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        stop_scheduler()
        await bot.session.close()
        logger.info("👋 BAZA BOT остановлен.")


if __name__ == "__main__":
    asyncio.run(main())
