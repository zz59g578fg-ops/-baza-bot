"""
Распознавание голоса через OpenAI Whisper — BAZA BOT.
Скачивает voice-файл из Telegram и отправляет в Whisper API.
"""
import os
import aiofiles
import aiohttp
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def download_voice(bot, file_id: str, dest_path: str):
    """Скачивает голосовое сообщение из Telegram."""
    file = await bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            content = await resp.read()
    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(content)


async def transcribe_voice(bot, file_id: str) -> str:
    """
    Скачивает голосовое сообщение и транскрибирует через Whisper.
    Возвращает текст или выбрасывает исключение.
    """
    os.makedirs("data/voice_tmp", exist_ok=True)
    path = f"data/voice_tmp/{file_id}.ogg"

    try:
        await download_voice(bot, file_id, path)

        with open(path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru",   # поддерживает русский
            )
        return transcript.text.strip()
    finally:
        if os.path.exists(path):
            os.remove(path)


async def parse_intent_from_text(text: str) -> dict:
    """
    Анализирует транскрибированный текст через GPT и определяет намерение:
    - create_note
    - create_task
    - create_reminder
    Возвращает структурированный dict.
    """
    system_prompt = """Ты — умный ассистент BAZA BOT. Пользователь надиктовал голосовое сообщение.
Определи намерение и верни JSON БЕЗ markdown-обёртки со следующими полями:
{
  "intent": "create_note" | "create_task" | "create_reminder" | "unknown",
  "title": "краткий заголовок (если есть)",
  "content": "полный текст или описание",
  "priority": "low" | "medium" | "high" (только для задач),
  "remind_at": "YYYY-MM-DDTHH:MM:SS" (только для напоминаний, если время понятно из текста),
  "project_hint": "название проекта если упомянуто или null"
}
Отвечай только JSON, без пояснений."""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=300,
    )

    import json
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"intent": "create_note", "content": text, "title": None,
                "priority": "medium", "remind_at": None, "project_hint": None}
