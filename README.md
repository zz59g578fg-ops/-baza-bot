# 🤖 BAZA BOT

Твой личный Telegram-ассистент. Заметки, задачи, напоминания, голос, проекты.

---

## ⚡ Быстрый старт

### 1. Клонируй и установи зависимости
```bash
pip install -r requirements.txt
```

### 2. Настрой окружение
```bash
cp .env.example .env
```
Открой `.env` и заполни:
```
BOT_TOKEN=токен_от_@BotFather
OPENAI_API_KEY=ключ_OpenAI_для_Whisper
TIMEZONE=Europe/Moscow
```

### 3. Запусти
```bash
python main.py
```

---

## 🛠 Возможности

| Функция | Описание |
|---|---|
| 📝 Заметки | Создание, поиск, привязка к проекту |
| 📋 Задачи | Приоритеты, статусы, сроки, проекты |
| ⏰ Напоминания | Гибкий парсинг дат, повторы (daily/weekly/monthly) |
| 🎙 Голос | Whisper → текст → автоопределение намерения |
| 📁 Проекты | Группировка задач, заметок и напоминаний |
| 🔍 Поиск | По заметкам полнотекстовый поиск |

---

## 📂 Структура проекта

```
tg-assistant-bot/
├── main.py                    # Точка входа
├── requirements.txt
├── .env.example
├── models/
│   └── database.py            # SQLite схема и подключение
├── services/
│   ├── user_service.py        # Пользователи
│   ├── note_service.py        # Заметки
│   ├── task_service.py        # Задачи
│   ├── reminder_service.py    # Напоминания
│   ├── project_service.py     # Проекты
│   ├── voice_service.py       # Whisper + GPT парсинг намерений
│   └── scheduler.py           # APScheduler — рассылка напоминаний
├── handlers/
│   └── all_handlers.py        # Все команды, FSM, callback-кнопки
└── utils/
    ├── keyboards.py           # Inline и Reply клавиатуры
    └── date_parser.py         # Парсинг дат на русском
```

---

## 🗣 Команды бота

```
/start        — Приветствие и главное меню
/help         — Справка
/note [текст] — Новая заметка
/notes        — Список заметок
/task [текст] — Новая задача
/tasks        — Список задач
/remind       — Новое напоминание
/reminders    — Список напоминаний
/projects     — Мои проекты
```

---

## 🎙 Голосовые сообщения

Отправь голосовое — BAZA BOT:
1. Транскрибирует через **OpenAI Whisper**
2. Анализирует намерение через **GPT-4o-mini**
3. Предлагает сохранить как заметку / задачу / напоминание

---

## 📅 Форматы дат для напоминаний

```
завтра в 10:00
через 2 часа
15 мая в 18:30
в пятницу в 9
послезавтра
```

---

## 🗄 База данных

SQLite файл создаётся автоматически в `data/assistant.db`.

Таблицы: `users`, `projects`, `notes`, `tasks`, `reminders`

---

## 📦 Зависимости

- **aiogram 3.7** — Telegram Bot API
- **aiosqlite** — асинхронный SQLite
- **APScheduler** — планировщик напоминаний
- **OpenAI** — Whisper (голос) + GPT-4o-mini (намерения)
- **pytz** — работа с часовыми поясами
