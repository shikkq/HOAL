import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart  # Text убран
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env файла в окружение
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

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

@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=theme.title(), callback_data=f"theme:{theme}")]
            for theme in knowledge_base
        ]
    )
    await message.answer("Привет! Выбери тему:", reply_markup=kb)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data or ""
    
    if data.startswith("theme:"):
        theme = data.split(":", 1)[1]
        subtopics = knowledge_base.get(theme, {})
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=sub.title(), callback_data=f"sub:{theme}:{sub}")]
                for sub in subtopics
            ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]]
        )
        await callback.message.edit_text(f"Выбрана тема: {theme.title()}\nВыбери вопрос:", reply_markup=kb)
    
    elif data.startswith("sub:"):
        _, theme, sub = data.split(":", 2)
        answer = knowledge_base.get(theme, {}).get(sub, {}).get("answer", "Ответ не найден.")
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]]
        )
        await callback.message.edit_text(f"🧾 {sub.title()}:\n\n{answer}", reply_markup=kb)
    
    elif data == "back_to_menu":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=theme.title(), callback_data=f"theme:{theme}")]
                for theme in knowledge_base
            ]
        )
        await callback.message.edit_text("Выбери тему:", reply_markup=kb)
    
    else:
        await callback.answer()  # Чтобы не висело "часики"

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
