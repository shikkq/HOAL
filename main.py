import asyncio
import json
import hashlib
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

CACHE_FILE = "callback_cache.json"
callback_data_map = {}  # id -> тема или [тема, подтема]

# База знаний
knowledge_base = {
    "Жильё": {
        "Как безопасно арендовать квартиру": {
            "keywords": ["арендовать", "безопасно", "договор", "аренда"],
            "answer":"""
1. Ищем квартиру на ЦИАН, Авито или других сайтах.

2. Пишем владельцу или агенту. Сразу узнаём:
– Это собственник или посредник?
– Сколько стоит аренда, залог и услуги риэлтора (если он есть)?
3. Прикидываем: обычно нужно сразу заплатить аренду за 1 месяц + залог + услуги риэлтора (обычно это сумма за месяц × 3).

4.Идём смотреть квартиру. Проверяем, всё ли работает: свет, вода, техника.

5.Просим показать выписку из ЕГРН и паспорт. Убедитесь, что это реальный собственник.

6.Читаем договор. Важно, чтобы:
– тип помещения был «жилое»,
– была фраза, что долги по коммуналке отсутствуют,
– залог возвращается при выезде.

 7.Если всё ок — подписываем договор, оплачиваем, заселяемся.
"""
        },
        "Как оплатить коммуналку": {
            "keywords": ["залог", "вернуть", "депозит"],
            "answer": """
Что делаем:
1. Заглядываем в почтовый ящик — там должны лежать бумажки с надписями вроде «электричество», «вода», «газ».

2. Открываем мобильное приложение банка.

3. Сканируем QR-код с квитанции прямо в приложении.

4. Смотрим на счётчики в квартире. Записываем все цифры до красной запятой. Например, если на счётчике 3652.89 — пишем 3652.

5. Вводим эти цифры, нажимаем «Оплатить». Готово!
                
Платим с 15 по 25 число каждого месяца.
"""
        }
    },
    "Почта": {
        "Как отправить письмо или посылку": {
            "keywords": ["полис", "омс", "медицинский"],
            "answer": """
Письмо:
– Покупаем на почте конверт и марку.

– Пишем адрес получателя и свой.

– Кладём письмо в конверт и кидаем его в почтовый ящик на почте (обычно стоит у входа).

Посылка:
– Рассчитываем стоимость доставки тут: pochta.ru/parcels.

– Упаковываем вещи в коробку или специальный почтовый пакет (их можно купить на почте).

– Лучше всего — скачать приложение «Почта России» и заполнить данные там заранее.

– Приклеиваем адрес и берём с собой паспорт.

– Приходим на почту, говорим: «Хочу отправить посылку».

– Отдаём, оплачиваем, получаем чек и трек-номер для отслеживания.
"""
        },

        " Как забрать посылку": {
            "keywords": ["полис", "омс", "медицинский"],
            "answer": """
Если есть трек-номер:
– Заходим на сайт или в приложение «Почты России» и проверяем, где посылка.

– Как только она пришла — идём на почту с паспортом и трек-номером.

Если трек-номера нет:
– В почтовый ящик придёт бумажка — извещение.

– Берём извещение и паспорт, идём на почту и получаем посылку.

Если пришло сообщение на телефон:

– Просто идём на почту и говорим, что ждёте посылку.

– Сотрудник отправит вам код — называете его, и всё, посылка у вас. Паспорт даже не нужен!
"""
        }
    },
    "Медицина": {
        "Как записаться к врачу": {
            "keywords": ["полис", "омс", "медицинский"],
            "answer": """
Если идёте в частную клинику:

– Звоним в клинику — номер телефона найдёте на их сайте или на картах.
Можно сразу записаться к терапевту — он подскажет, к какому специалисту идти дальше.
Cразу спрашиваем стоимость.

– В день приёма берём паспорт и приходим в клинику.
– Подходим на ресепшен (регистратуру) и говорим, что у вас запись.

Если идёте в государственную поликлинику:
– Если вам до 18 лет — записываемся к педиатру, если старше — идём к терапевту.

– На приёме рассказываем, что и где болит. Жалуемся ему на все на свете чтобы дали направления для этих врачей.
Хотя бы попросите направление на общий анализ крови и мочи.

– После приёма вам либо сразу выдают направления, либо отправляют обратно в регистратуру, чтобы записали к нужным врачам.
            """
        }
    }
}

# --- Вспомогательные функции ---

def make_id(text: str) -> str:
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
        if isinstance(value, str):
            buttons.append(
                [InlineKeyboardButton(text=value.title(), callback_data=f"theme:{theme_id}")]
            )
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_subtopic_buttons(theme_id):
    theme = callback_data_map.get(theme_id)
    if not theme or not isinstance(theme, str):
        return InlineKeyboardMarkup(inline_keyboard=[])
    buttons = []
    for sub in knowledge_base.get(theme, {}):
        sub_id = make_id(theme + sub)
        buttons.append([InlineKeyboardButton(text=sub.title(), callback_data=f"sub:{sub_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_long_text(chat_id: int, text: str, reply_markup=None):
    MAX_LEN = 4000
    parts = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for part in parts:
        await bot.send_message(chat_id, part, reply_markup=reply_markup)
        await asyncio.sleep(0.1)

# --- Хендлеры ---

@dp.message(CommandStart())
async def start(message: types.Message):
    kb = create_theme_buttons()
    await message.answer("Привет! Выбери тему:", reply_markup=kb)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data or ""
    chat_id = callback.message.chat.id

    if data.startswith("theme:"):
        theme_id = data.split(":", 1)[1]
        theme = callback_data_map.get(theme_id)
        if not theme:
            return await callback.answer("Тема не найдена")
        kb = create_subtopic_buttons(theme_id)
        await callback.message.edit_text(f"Выбрана тема: {theme.title()}\nВыбери вопрос:", reply_markup=kb)

    elif data.startswith("sub:"):
        sub_id = data.split(":", 1)[1]
        value = callback_data_map.get(sub_id)
        if not value or not isinstance(value, list):
            return await callback.answer("Ошибка: вопрос не найден", show_alert=True)
        theme, sub = value
        answer = knowledge_base.get(theme, {}).get(sub, {}).get("answer", "Ответ не найден.")
        home_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
        ])
        await callback.message.delete()
        await send_long_text(chat_id, f"🧾 {sub.title()}:\n\n{answer}")
        await bot.send_message(chat_id, "Вы можете вернуться в меню:", reply_markup=home_kb)

    elif data == "back_to_menu":
        kb = create_theme_buttons()
        await callback.message.edit_text("Выбери тему:", reply_markup=kb)

    else:
        await callback.answer()

# --- AIOHTTP сервер для /ping ---

async def handle_ping(request):
    return web.Response(text="OK — I'm alive!")

# --- Инициализация ---

app = web.Application()
app.router.add_get("/", handle_ping)
app.router.add_get("/ping", handle_ping)

async def on_startup(app):
    load_cache()
    if not callback_data_map:
        build_cache()
    asyncio.create_task(dp.start_polling(bot))

app.on_startup.append(on_startup)

# --- Запуск ---

if __name__ == "__main__":
    web.run_app(app, port=PORT)
