"""Утилиты парсинга дат — BAZA BOT."""
import re
from datetime import datetime, timedelta
import pytz


MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

WEEKDAYS_RU = {
    "понедельник": 0, "вторник": 1, "среда": 2, "среду": 2,
    "четверг": 3, "пятница": 4, "пятницу": 4,
    "суббота": 5, "субботу": 5, "воскресенье": 6,
}


def parse_datetime(text: str, user_tz: str = "Europe/Moscow") -> datetime | None:
    """
    Разбирает дату из текста на русском.
    Примеры: 'завтра в 10:00', 'через 2 часа', '15 января в 18:30', 'в пятницу в 9'
    """
    tz = pytz.timezone(user_tz)
    now = datetime.now(tz)
    text = text.lower().strip()

    # Через N минут/часов/дней
    m = re.search(r"через\s+(\d+)\s+(минут|час|день|дн)", text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "минут" in unit:
            dt = now + timedelta(minutes=n)
        elif "час" in unit:
            dt = now + timedelta(hours=n)
        else:
            dt = now + timedelta(days=n)
        return dt.astimezone(pytz.utc).replace(tzinfo=None)

    # Сегодня / завтра / послезавтра
    base_day = None
    if "послезавтра" in text:
        base_day = now + timedelta(days=2)
    elif "завтра" in text:
        base_day = now + timedelta(days=1)
    elif "сегодня" in text:
        base_day = now

    # День недели
    for day_name, day_num in WEEKDAYS_RU.items():
        if day_name in text:
            days_ahead = (day_num - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            base_day = now + timedelta(days=days_ahead)
            break

    # Конкретная дата: 15 января
    m = re.search(r"(\d{1,2})\s+(" + "|".join(MONTHS_RU.keys()) + r")", text)
    if m:
        day = int(m.group(1))
        month = MONTHS_RU[m.group(2)]
        year = now.year if month >= now.month else now.year + 1
        base_day = now.replace(year=year, month=month, day=day)

    # ISO datetime (из GPT)
    m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})", text)
    if m:
        try:
            dt = datetime.fromisoformat(m.group(1))
            return tz.localize(dt).astimezone(pytz.utc).replace(tzinfo=None)
        except ValueError:
            pass

    # Время
    time_match = re.search(r"в\s+(\d{1,2})(?::(\d{2}))?", text)
    hour, minute = None, 0
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0

    if base_day and hour is not None:
        dt = base_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return tz.normalize(dt).astimezone(pytz.utc).replace(tzinfo=None)
    elif base_day:
        dt = base_day.replace(hour=9, minute=0, second=0, microsecond=0)
        return tz.normalize(dt).astimezone(pytz.utc).replace(tzinfo=None)
    elif hour is not None:
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt < now:
            dt += timedelta(days=1)
        return tz.normalize(dt).astimezone(pytz.utc).replace(tzinfo=None)

    return None


def format_dt_ru(dt_str: str, user_tz: str = "Europe/Moscow") -> str:
    """Форматирует ISO datetime в читаемый русский вид."""
    try:
        dt = datetime.fromisoformat(dt_str)
        tz = pytz.timezone(user_tz)
        dt_local = pytz.utc.localize(dt).astimezone(tz)
        return dt_local.strftime("%d.%m.%Y в %H:%M")
    except Exception:
        return dt_str
