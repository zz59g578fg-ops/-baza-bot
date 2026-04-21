"""
Все хэндлеры BAZA BOT.
Подключаются к роутеру и регистрируются в main.py
"""
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from services.user_service import get_or_create_user, get_user
from services.note_service import create_note, get_notes, search_notes, delete_note
from services.task_service import create_task, get_tasks, update_task_status, assign_task_to_project, delete_task, PRIORITY_EMOJI, STATUS_EMOJI
from services.reminder_service import create_reminder, get_pending_reminders, mark_done, delete_reminder
from services.project_service import create_project, get_projects, get_project, delete_project, get_project_stats
from services.voice_service import transcribe_voice, parse_intent_from_text
from utils.keyboards import (
    main_menu_kb, projects_kb, task_actions_kb, reminder_actions_kb,
    note_actions_kb, voice_result_kb, cancel_kb, priority_kb
)
from utils.date_parser import parse_datetime, format_dt_ru

router = Router()


# ══════════════════════════════════════════════
#  FSM States
# ══════════════════════════════════════════════

class NoteForm(StatesGroup):
    content = State()
    project = State()

class TaskForm(StatesGroup):
    title = State()
    priority = State()
    due_date = State()
    project = State()

class ReminderForm(StatesGroup):
    text = State()
    time = State()
    repeat = State()
    project = State()

class ProjectForm(StatesGroup):
    name = State()
    description = State()

class VoiceForm(StatesGroup):
    confirming = State()

class SearchForm(StatesGroup):
    query = State()


# ══════════════════════════════════════════════
#  START / HELP
# ══════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Я <b>BAZA BOT</b> — твой личный ассистент.\n\n"
        f"Что умею:\n"
        f"📝 Создавать заметки (текст + голос)\n"
        f"📋 Вести задачи по проектам\n"
        f"⏰ Отправлять напоминания\n"
        f"🎙 Распознавать голосовые сообщения\n\n"
        f"Просто напиши или надиктуй что нужно сделать!",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>BAZA BOT — справка</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/note — новая заметка\n"
        "/task — новая задача\n"
        "/remind — новое напоминание\n"
        "/projects — мои проекты\n"
        "/tasks — список задач\n"
        "/notes — список заметок\n"
        "/reminders — список напоминаний\n\n"
        "<b>Голос:</b>\n"
        "Отправь голосовое — я распознаю и предложу что с ним сделать 🎙",
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════
#  ЗАМЕТКИ
# ══════════════════════════════════════════════

@router.message(F.text == "📝 Заметки")
@router.message(Command("notes"))
async def show_notes(message: Message):
    user = await get_or_create_user(message.from_user.id)
    notes = await get_notes(user["id"], limit=8)
    if not notes:
        await message.answer("📝 У тебя пока нет заметок.\n\nНапиши /note чтобы создать первую!")
        return
    text = "<b>📝 Последние заметки:</b>\n\n"
    for n in notes:
        title = n["title"] or n["content"][:40]
        proj = f" • {n.get('project_name','')}" if n.get("project_name") else ""
        src = "🎙" if n["source"] == "voice" else "✏️"
        text += f"{src} <b>{title}</b>{proj}\n<code>/note_{n['id']}</code>\n\n"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("note"))
async def cmd_new_note(message: Message, state: FSMContext):
    # Если текст после команды — сразу создаём
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        user = await get_or_create_user(message.from_user.id)
        note = await create_note(user["id"], content=args[1])
        await message.answer(
            f"✅ Заметка сохранена!\n\n📝 {args[1][:200]}",
            reply_markup=note_actions_kb(note["id"])
        )
        return
    await state.set_state(NoteForm.content)
    await message.answer("📝 Напиши текст заметки:", reply_markup=cancel_kb())


@router.message(NoteForm.content)
async def note_content_received(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)
    note = await create_note(user["id"], content=message.text)
    await state.clear()
    projects = await get_projects(user["id"])
    if projects:
        await state.update_data(note_id=note["id"])
        await state.set_state(NoteForm.project)
        await message.answer(
            f"✅ <b>Заметка сохранена!</b>\n\nПривязать к проекту?",
            parse_mode="HTML",
            reply_markup=projects_kb(projects, action="note_assign"),
        )
    else:
        await message.answer(
            f"✅ <b>Заметка сохранена!</b>",
            parse_mode="HTML",
            reply_markup=note_actions_kb(note["id"])
        )


# ══════════════════════════════════════════════
#  ЗАДАЧИ
# ══════════════════════════════════════════════

@router.message(F.text == "📋 Задачи")
@router.message(Command("tasks"))
async def show_tasks(message: Message):
    user = await get_or_create_user(message.from_user.id)
    tasks = await get_tasks(user["id"], status="todo", limit=10)
    tasks += await get_tasks(user["id"], status="in_progress", limit=5)
    if not tasks:
        await message.answer("📋 Задач нет. Напиши /task чтобы добавить!")
        return
    text = "<b>📋 Активные задачи:</b>\n\n"
    for t in tasks:
        p = PRIORITY_EMOJI.get(t["priority"], "")
        s = STATUS_EMOJI.get(t["status"], "")
        proj = f" • <i>{t.get('project_name','')}</i>" if t.get("project_name") else ""
        due = f" 📅 {t['due_date'][:10]}" if t.get("due_date") else ""
        text += f"{p}{s} <b>{t['title']}</b>{proj}{due}\n<code>/task_{t['id']}</code>\n\n"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/task_"))
async def task_detail(message: Message):
    try:
        task_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        return
    user = await get_or_create_user(message.from_user.id)
    tasks = await get_tasks(user["id"])
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        await message.answer("❌ Задача не найдена.")
        return
    p = PRIORITY_EMOJI.get(task["priority"], "")
    s = STATUS_EMOJI.get(task["status"], "")
    proj = f"\n📁 Проект: <b>{task.get('project_name','')}</b>" if task.get("project_name") else ""
    due = f"\n📅 Срок: <b>{task['due_date'][:10]}</b>" if task.get("due_date") else ""
    desc = f"\n\n{task['description']}" if task.get("description") else ""
    await message.answer(
        f"{p}{s} <b>{task['title']}</b>{proj}{due}{desc}",
        parse_mode="HTML",
        reply_markup=task_actions_kb(task_id, task["status"]),
    )


@router.message(F.text == "➕ Быстрая задача")
@router.message(Command("task"))
async def cmd_new_task(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        user = await get_or_create_user(message.from_user.id)
        task = await create_task(user["id"], title=args[1])
        await message.answer(
            f"✅ Задача добавлена!\n📋 {args[1]}",
            reply_markup=task_actions_kb(task["id"], task["status"])
        )
        return
    await state.set_state(TaskForm.title)
    await message.answer("📋 Название задачи:", reply_markup=cancel_kb())


@router.message(TaskForm.title)
async def task_title_received(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskForm.priority)
    await message.answer("Приоритет задачи:", reply_markup=priority_kb("taskprio"))


@router.message(TaskForm.due_date)
async def task_due_received(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)
    data = await state.get_data()
    due = None
    if message.text.lower() not in ("нет", "пропустить", "-"):
        dt = parse_datetime(message.text, user.get("timezone", "Europe/Moscow"))
        due = dt.isoformat() if dt else message.text
    task = await create_task(
        user["id"],
        title=data["title"],
        priority=data.get("priority", "medium"),
        due_date=due,
    )
    await state.clear()
    await message.answer(
        f"✅ <b>Задача создана!</b>\n📋 {task['title']}",
        parse_mode="HTML",
        reply_markup=task_actions_kb(task["id"], task["status"])
    )


# ══════════════════════════════════════════════
#  НАПОМИНАНИЯ
# ══════════════════════════════════════════════

@router.message(F.text == "⏰ Напоминания")
@router.message(Command("reminders"))
async def show_reminders(message: Message):
    user = await get_or_create_user(message.from_user.id)
    reminders = await get_pending_reminders(user["id"])
    if not reminders:
        await message.answer("⏰ Активных напоминаний нет.\n\nНапиши /remind чтобы добавить!")
        return
    text = "<b>⏰ Активные напоминания:</b>\n\n"
    for r in reminders:
        proj = f" • <i>{r.get('project_name','')}</i>" if r.get("project_name") else ""
        dt_str = format_dt_ru(r["remind_at"])
        repeat = {"daily": " 🔁ежедневно", "weekly": " 🔁нед.", "monthly": " 🔁мес."}.get(r.get("repeat",""), "")
        text += f"📅 <b>{dt_str}</b>{repeat}\n{r['text']}{proj}\n<code>/rem_{r['id']}</code>\n\n"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("remind"))
async def cmd_new_reminder(message: Message, state: FSMContext):
    await state.set_state(ReminderForm.text)
    await message.answer(
        "⏰ Что напомнить?\n\nНапример: <i>Позвонить клиенту</i>",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )


@router.message(ReminderForm.text)
async def reminder_text_received(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(ReminderForm.time)
    await message.answer(
        "📅 Когда напомнить?\n\n"
        "Примеры:\n"
        "• <code>завтра в 10:00</code>\n"
        "• <code>через 2 часа</code>\n"
        "• <code>15 мая в 18:30</code>\n"
        "• <code>в пятницу в 9</code>",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )


@router.message(ReminderForm.time)
async def reminder_time_received(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)
    tz = user.get("timezone", "Europe/Moscow")
    dt = parse_datetime(message.text, tz)
    if not dt:
        await message.answer(
            "❓ Не смог разобрать дату. Попробуй ещё раз:\n"
            "<code>завтра в 10:00</code> или <code>через 2 часа</code>",
            parse_mode="HTML"
        )
        return
    data = await state.get_data()
    reminder = await create_reminder(user["id"], text=data["text"], remind_at=dt)
    await state.clear()
    dt_nice = format_dt_ru(reminder["remind_at"], tz)
    await message.answer(
        f"✅ <b>Напоминание создано!</b>\n\n"
        f"📅 {dt_nice}\n"
        f"💬 {data['text']}",
        parse_mode="HTML",
        reply_markup=reminder_actions_kb(reminder["id"])
    )


# ══════════════════════════════════════════════
#  ПРОЕКТЫ
# ══════════════════════════════════════════════

@router.message(F.text == "📁 Проекты")
@router.message(Command("projects"))
async def show_projects(message: Message):
    user = await get_or_create_user(message.from_user.id)
    projects = await get_projects(user["id"])
    if not projects:
        await message.answer(
            "📁 Проектов пока нет.\n\nНажми кнопку ниже чтобы создать первый!",
            reply_markup=projects_kb([], "open")
        )
        return
    await message.answer(
        f"📁 <b>Твои проекты ({len(projects)}):</b>",
        parse_mode="HTML",
        reply_markup=projects_kb(projects, "open")
    )


@router.message(ProjectForm.name)
async def project_name_received(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProjectForm.description)
    await message.answer("📝 Описание проекта (или напиши «-» пропустить):", reply_markup=cancel_kb())


@router.message(ProjectForm.description)
async def project_desc_received(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)
    data = await state.get_data()
    desc = None if message.text.strip() in ("-", "пропустить") else message.text
    project = await create_project(user["id"], name=data["name"], description=desc)
    await state.clear()
    await message.answer(
        f"✅ <b>Проект создан!</b>\n📁 {project['name']}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


# ══════════════════════════════════════════════
#  ГОЛОС
# ══════════════════════════════════════════════

@router.message(F.voice)
async def voice_handler(message: Message, state: FSMContext, bot: Bot):
    proc_msg = await message.answer("🎙 Распознаю голосовое...")
    try:
        text = await transcribe_voice(bot, message.voice.file_id)
        intent_data = await parse_intent_from_text(text)
        await state.update_data(voice_text=text, voice_intent=intent_data)
        await state.set_state(VoiceForm.confirming)
        intent_label = {
            "create_note": "📝 заметку",
            "create_task": "📋 задачу",
            "create_reminder": "⏰ напоминание",
        }.get(intent_data.get("intent"), "запись")
        await proc_msg.edit_text(
            f"🎙 <b>Распознано:</b>\n\n<i>{text}</i>\n\n"
            f"💡 Похоже на {intent_label}. Сохранить как:",
            parse_mode="HTML",
            reply_markup=voice_result_kb(intent_data.get("intent", ""))
        )
    except Exception as e:
        await proc_msg.edit_text(f"❌ Не удалось распознать голос: {e}")


# ══════════════════════════════════════════════
#  ПОИСК
# ══════════════════════════════════════════════

@router.message(F.text == "🔍 Поиск")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(SearchForm.query)
    await message.answer("🔍 Что искать? (ищу по заметкам):", reply_markup=cancel_kb())


@router.message(SearchForm.query)
async def search_query(message: Message, state: FSMContext):
    user = await get_or_create_user(message.from_user.id)
    results = await search_notes(user["id"], message.text)
    await state.clear()
    if not results:
        await message.answer(f"🔍 По запросу «{message.text}» ничего не найдено.")
        return
    text = f"🔍 <b>Найдено {len(results)} заметок:</b>\n\n"
    for n in results[:5]:
        title = n["title"] or n["content"][:50]
        text += f"• {title}\n<code>/note_{n['id']}</code>\n\n"
    await message.answer(text, parse_mode="HTML")


# ══════════════════════════════════════════════
#  CALLBACK HANDLERS
# ══════════════════════════════════════════════

@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("task:"))
async def cb_task(callback: CallbackQuery):
    _, action, task_id_str = callback.data.split(":")
    task_id = int(task_id_str)
    user = await get_or_create_user(callback.from_user.id)

    if action in ("done", "in_progress", "todo"):
        task = await update_task_status(task_id, user["id"], action)
        label = {"done": "✅ Готово", "in_progress": "⚡ В работе", "todo": "📋 Открыта"}.get(action, action)
        await callback.answer(f"{label}!")
        await callback.message.edit_reply_markup(
            reply_markup=task_actions_kb(task_id, action) if action != "done" else None
        )
    elif action == "delete":
        await delete_task(task_id, user["id"])
        await callback.message.edit_text("🗑 Задача удалена.")
        await callback.answer()
    elif action == "assign":
        projects = await get_projects(user["id"])
        if projects:
            await callback.message.edit_reply_markup(
                reply_markup=projects_kb(projects, f"task_assign_{task_id}")
            )
        await callback.answer()


@router.callback_query(F.data.startswith("reminder:"))
async def cb_reminder(callback: CallbackQuery):
    _, action, rid_str = callback.data.split(":")
    rid = int(rid_str)
    user = await get_or_create_user(callback.from_user.id)

    if action == "done":
        await mark_done(rid)
        await callback.message.edit_text("✅ Напоминание выполнено!")
    elif action == "delete":
        await delete_reminder(rid, user["id"])
        await callback.message.edit_text("🗑 Напоминание удалено.")
    await callback.answer()


@router.callback_query(F.data.startswith("note:"))
async def cb_note(callback: CallbackQuery):
    _, action, nid_str = callback.data.split(":")
    nid = int(nid_str)
    user = await get_or_create_user(callback.from_user.id)

    if action == "delete":
        await delete_note(nid, user["id"])
        await callback.message.edit_text("🗑 Заметка удалена.")
    elif action == "assign":
        projects = await get_projects(user["id"])
        if projects:
            await callback.message.edit_reply_markup(
                reply_markup=projects_kb(projects, f"note_assign_{nid}")
            )
    await callback.answer()


@router.callback_query(F.data.startswith("project:"))
async def cb_project(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    action = parts[1]
    project_id = int(parts[2]) if len(parts) > 2 else 0

    if action == "create":
        await state.set_state(ProjectForm.name)
        await callback.message.answer("📁 Название нового проекта:", reply_markup=cancel_kb())
        await callback.answer()
        return

    if action == "open" and project_id:
        user = await get_or_create_user(callback.from_user.id)
        project = await get_project(project_id, user["id"])
        stats = await get_project_stats(project_id)
        if project:
            await callback.message.answer(
                f"📁 <b>{project['name']}</b>\n"
                f"{project.get('description','') or ''}\n\n"
                f"📋 Задач: {stats['tasks_total']} (выполнено {stats['tasks_done']})\n"
                f"📝 Заметок: {stats['notes_count']}\n"
                f"⏰ Напоминаний: {stats['active_reminders']}",
                parse_mode="HTML"
            )
    await callback.answer()


@router.callback_query(F.data.startswith("taskprio:"))
async def cb_task_priority(callback: CallbackQuery, state: FSMContext):
    priority = callback.data.split(":")[1]
    await state.update_data(priority=priority)
    await state.set_state(TaskForm.due_date)
    await callback.message.edit_text(
        "📅 Срок выполнения?\n\nНапиши дату или <code>нет</code>:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("voice:"))
async def cb_voice(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    text = data.get("voice_text", "")
    intent = data.get("voice_intent", {})
    user = await get_or_create_user(callback.from_user.id)
    await state.clear()

    if action == "note":
        note = await create_note(user["id"], content=text, source="voice",
                                 title=intent.get("title"))
        await callback.message.edit_text(
            f"✅ <b>Заметка из голоса сохранена!</b>\n\n📝 {text[:200]}",
            parse_mode="HTML",
            reply_markup=note_actions_kb(note["id"])
        )
    elif action == "task":
        task = await create_task(user["id"], title=intent.get("title") or text[:100],
                                 description=text,
                                 priority=intent.get("priority", "medium"))
        await callback.message.edit_text(
            f"✅ <b>Задача из голоса создана!</b>\n\n📋 {task['title']}",
            parse_mode="HTML",
            reply_markup=task_actions_kb(task["id"], task["status"])
        )
    elif action == "reminder":
        remind_at = None
        if intent.get("remind_at"):
            from utils.date_parser import parse_datetime
            remind_at = parse_datetime(intent["remind_at"], user.get("timezone", "Europe/Moscow"))
        if remind_at:
            reminder = await create_reminder(user["id"], text=text, remind_at=remind_at)
            dt_nice = format_dt_ru(reminder["remind_at"], user.get("timezone", "Europe/Moscow"))
            await callback.message.edit_text(
                f"✅ <b>Напоминание из голоса!</b>\n\n📅 {dt_nice}\n💬 {text}",
                parse_mode="HTML",
                reply_markup=reminder_actions_kb(reminder["id"])
            )
        else:
            await callback.message.edit_text(
                "⏰ Не смог разобрать время из голоса.\n"
                "Напиши /remind чтобы задать вручную."
            )
    await callback.answer()
