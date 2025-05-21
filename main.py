import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Text

TOKEN = "ТВОЙ_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 👇 СЮДА ДОБАВЛЯЙТЕ ТЕМЫ, ПОДТЕМЫ, КЛЮЧЕВЫЕ СЛОВА И ОТВЕТЫ 👇

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
    # 🎯 ПРИМЕР ДОБАВЛЕНИЯ НОВОЙ ТЕМЫ:
    # "работа": {
    #     "как составить резюме": {
    #         "keywords": ["резюме", "работа"],
    #         "answer": "Для хорошего резюме: 1) кратко, 2) по делу, 3) адаптируйте под вакансию."
    #     }
    # }
}

# 👆 ВСЁ ДОБАВЛЯЕТСЯ ТОЛЬКО СЮДА. НИЧЕГО БОЛЬШЕ ТРОГАТЬ НЕ НАДО 👆

# Команда /start
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=theme.title(), callback_data=f"theme:{theme}")]
            for theme in knowledge_base
        ]
    )
    await message.answer("Привет! Выбери тему:", reply_markup=kb)

# Показ подтем
@dp.callback_query(Text(startswith="theme:"))
async def show_subtopics(callback: types.CallbackQuery):
    theme = callback.data.split(":")[1]
    subtopics = knowledge_base[theme]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=sub.title(), callback_data=f"sub:{theme}:{sub}")]
            for sub in subtopics
        ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]]
    )
    await callback.message.edit_text(f"Выбрана тема: {theme.title()}\nВыбери вопрос:", reply_markup=kb)

# Ответ на подтему
@dp.callback_query(Text(startswith="sub:"))
async def show_answer(callback: types.CallbackQuery):
    _, theme, sub = callback.data.split(":", 2)
    answer = knowledge_base[theme][sub]["answer"]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]]
    )
    await callback.message.edit_text(f"🧾 {sub.title()}:\n\n{answer}", reply_markup=kb)

# Назад в меню
@dp.callback_query(Text("back_to_menu"))
async def back_to_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=theme.title(), callback_data=f"theme:{theme}")]
            for theme in knowledge_base
        ]
    )
    await callback.message.edit_text("Выбери тему:", reply_markup=kb)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
