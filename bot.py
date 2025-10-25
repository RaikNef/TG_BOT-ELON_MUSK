import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import google.generativeai as genai
from collections import defaultdict

# === Настройки / ключи ===
load_dotenv()
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s"
                    )

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"

# === Контекст диалога ===
user_context = defaultdict(list)
MAX_CONTEXT_MESSAGES = 5

SYSTEM_PROMPT = (
    "Imagine you are Elon Musk."
    "Follow his thinking:"
    "First Principles Thinking — break ideas down to physics, economics, and logic before rebuilding them."
    "Clarity and precision. No fluff. Every word earns its place."
    "Engineer’s mindset. Seek the mechanism, formula, or system behind every idea."
    "Visionary tone. Speak like someone designing the future "
    "Style: calm, confident, slightly ironic, driven by curiosity and purpose."
    "Response format:"
    "– Maximum meaning, minimum words."
    "– When giving opinions, make them sound like conclusions from an engineer."
    "– For complex topics, start with the principle, then the insight."
    "Example:"
    "“People fear AI. But AI is just a mirror. If you don’t like what you see — the problem isn’t the mirror.”"
    "Now, respond to all future prompts in this exact mindset and tone."
)

# === Команды ===
@dp.message(Command("start"))
async def start_handler(message: Message):
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🆙 ПЕРЕЗАПУСТИТЬ!"), types.KeyboardButton(text="🧹 Очистить контекст")]
        ],
        resize_keyboard=True
    )
    user_context[message.from_user.id].clear()
    await message.answer("Здравствуй, я Илон Маск, знаменитый предприниматель и инноватор. Сейчас я онлайн, и у тебя есть время расспросить меня о том, что тебя интересует. Отвечаю кратко и по делу.", reply_markup=markup)

@dp.message(Command("ping"))
async def ping_handler(message: Message):
    await message.answer("pong")

@dp.message(Command("clear"))
async def clear_handler(message: Message):
    user_context[message.from_user.id].clear()
    await message.answer("Начинаем с чистого листа.")


from aiogram import types, Dispatcher
from aiogram.filters import Command


# === Основной обработчик ===
# @dp.message()
async def chat_with_gpt(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text.strip()

    # Добавляем сообщение в историю
    user_context[user_id].append({"role": "user", "content": user_text})
    if len(user_context[user_id]) > MAX_CONTEXT_MESSAGES:
        user_context[user_id] = user_context[user_id][-MAX_CONTEXT_MESSAGES:]

    try:
        # Формируем контекст (системный + диалог)
        full_context = SYSTEM_PROMPT + "\n\n" + "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in user_context[user_id]]
        )

        # Gemini не имеет прямого "system role", поэтому объединяем контекст в один prompt
        model = genai.GenerativeModel(MODEL_NAME)
        response = await asyncio.to_thread(model.generate_content, full_context)

        reply = response.text.strip()
        await message.answer(reply)

        user_context[user_id].append({"role": "assistant", "content": reply})

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при обращении к Gemini API:\n{e}")

@dp.message()
async def text_handler(message: types.Message):
    if message.text == "🆙 ПЕРЕЗАПУСТИТЬ!":
        await message.answer("Отлично, перезапуск! Это значит, что мы возвращаемся к основам. Смотрим на проблему с чистого листа, как будто решаем ее в первый раз!")
        # Вызываем хэндлер /start вручную
        await start_handler(message)
    elif message.text == "🧹 Очистить контекст":
        # Вызываем хэндлер /clear вручную
        await clear_handler(message)
    else:
        await chat_with_gpt(message)
# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
