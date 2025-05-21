import asyncio
import json
import hashlib
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

CACHE_FILE = "callback_cache.json"
callback_data_map = {}  # id -> (theme) или (theme, subtopic)

knowledge_base = {
    "аренда жилья": {
        "как безопасно арендовать": {
            "keywords": ["арендовать", "безопасно", "договор", "аренда"],
            "answer": "Для безопасной аренды жилья: 1) читайте договор, 2) не передавайте деньги без расписок."
        },
        "как вернуть залог": {
            "keywords": ["залог", "вернуть", "депозит"],
            "answer": "Залог возвращается после окончания аренды, если нет повреждений. Требуйте расписку."
        }
    },
    "медицина": {
        "как получить полис омс": {
            "keywords": ["полис", "омс", "медицинский"],
            "answer": "Для получения полиса ОМС нужно обратиться в МФЦ с паспортом и СНИЛС."
        },
        "как записаться к врачу": {
            "keywords": ["врач", "записаться", "поликлиника"],
            "answer": "Запись к врачу возможна через Госуслуги или по телефону регистратуры."
        }
    },
}


def make_id(text: str) -> str:
    """Генерируем короткий ID (хеш) из текста"""
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def load_cache():
    global callback_data_map
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            callback_data_map = json.load(f)
    else:
        callback_data_map = {}


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(callback_data_map, f, ensure_ascii=False, indent=2)


def build_cache():
    """
    Строим кеш callback_data_map по knowledge_base
    format:
      theme_id: theme_name
      sub_id: [theme_name, subtopic_name]
    """
    for theme in knowledge_base:
        theme_id = make_id(theme)
        callback_data_map[theme_id] = theme
        for sub in knowledge_base[theme]:
            sub_id = make_id(theme + sub)
            callback_data_map[sub_id] = [theme, sub]
    save_cache()


def create_theme_buttons():
    buttons = []
    for theme_id, value in callback_data_map.items():
        # value может быть str (тема) или list (тема, подтема)
        if isinstance(value, str):
            buttons.append(
                InlineKeyboardButton(text=value.title(), callback_data=f"theme:{theme_id}")
            )
    return buttons


def create_subtopic_buttons(theme_id):
    buttons = []
    value = callback_data_map.get(theme_id)
    if not value or not isinstance(value, str):
        return buttons
    theme = value
    for sub in knowledge_base.get(theme, {}):
        sub_id = make_id(theme + sub)
        buttons.append(
            InlineKeyboardButton(text=sub.title(), callback_data=f"sub:{sub_id}")
        )
    buttons.append(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return buttons


async def send_long_text(chat_id: int, text: str, reply_markup=None):
    MAX_LEN = 4000  # чуть меньше лимита Telegram
    parts = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for part in parts:
        await bot.send_message(chat_id, part, reply_markup=reply_markup)
        await asyncio.sleep(0.1)


@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for btn in create_theme_buttons():
        kb.add(btn)
    await message.answer("Привет! Выбери тему:", reply_markup=kb)


@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data or ""
    chat_id = callback.message.chat.id

    if data.startswith("theme:"):
        theme_id = data.split(":", 1)[1]
        kb = InlineKeyboardMarkup(row_width=1)
        for btn in create_subtopic_buttons(theme_id):
            kb.add(btn)
        theme_name = callback_data_map.get(theme_id, "Неизвестная тема")
        await callback.message.edit_text(f"Выбрана тема: {theme_name.title()}\nВыбери вопрос:", reply_markup=kb)

    elif data.startswith("sub:"):
        sub_id = data.split(":", 1)[1]
        val = callback_data_map.get(sub_id)
        if not val or not isinstance(val, list):
            await callback.answer("Ошибка: вопрос не найден", show_alert=True)
            return
        theme, subtopic = val
        answer = knowledge_base.get(theme, {}).get(subtopic, {}).get("answer", "Ответ не найден.")
        kb = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")
        )
        # Удаляем сообщение с кнопками (чтобы не путать) и отправляем длинный текст
        await callback.message.delete()
        await send_long_text(chat_id, f"🧾 {subtopic.title()}:\n\n{answer}")
        await bot.send_message(chat_id, "Вы можете вернуться в меню:", reply_markup=kb)

    elif data == "back_to_menu":
        kb = InlineKeyboardMarkup(row_width=1)
        for btn in create_theme_buttons():
            kb.add(btn)
        await callback.message.edit_text("Выбери тему:", reply_markup=kb)

    else:
        await callback.answer()  # Для закрытия "часиков"


async def main():
    load_cache()
    # Если кеш пустой — создадим и сохраним
    if not callback_data_map:
        build_cache()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
