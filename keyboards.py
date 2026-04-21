"""Клавиатуры и кнопки — BAZA BOT."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Задачи"), KeyboardButton(text="📝 Заметки")],
            [KeyboardButton(text="⏰ Напоминания"), KeyboardButton(text="📁 Проекты")],
            [KeyboardButton(text="➕ Быстрая задача"), KeyboardButton(text="🔍 Поиск")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или напишите...",
    )


def projects_kb(projects: list[dict], action: str = "open") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{p['color'] and '●'} {p['name']}",
            callback_data=f"project:{action}:{p['id']}"
        )]
        for p in projects
    ]
    buttons.append([InlineKeyboardButton(text="➕ Новый проект", callback_data="project:create:0")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_actions_kb(task_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status != "in_progress":
        buttons.append(InlineKeyboardButton(text="⚡ В работу", callback_data=f"task:in_progress:{task_id}"))
    if status != "done":
        buttons.append(InlineKeyboardButton(text="✅ Готово", callback_data=f"task:done:{task_id}"))
    buttons.append(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"task:delete:{task_id}"))
    row2 = [InlineKeyboardButton(text="📁 Привязать проект", callback_data=f"task:assign:{task_id}")]
    return InlineKeyboardMarkup(inline_keyboard=[buttons, row2])


def reminder_actions_kb(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Выполнено", callback_data=f"reminder:done:{reminder_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"reminder:delete:{reminder_id}"),
    ]])


def note_actions_kb(note_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📁 В проект", callback_data=f"note:assign:{note_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"note:delete:{note_id}"),
    ]])


def voice_result_kb(intent: str) -> InlineKeyboardMarkup:
    """Кнопки после распознавания голоса."""
    buttons = [
        InlineKeyboardButton(text="📝 Как заметку", callback_data=f"voice:note"),
        InlineKeyboardButton(text="📋 Как задачу", callback_data=f"voice:task"),
        InlineKeyboardButton(text="⏰ Как напоминание", callback_data=f"voice:reminder"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], [buttons[2]]])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    ]])


def priority_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔴 Высокий", callback_data=f"{prefix}:high"),
        InlineKeyboardButton(text="🟡 Средний", callback_data=f"{prefix}:medium"),
        InlineKeyboardButton(text="🟢 Низкий", callback_data=f"{prefix}:low"),
    ]])
