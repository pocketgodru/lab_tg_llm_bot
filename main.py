import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from mistralai import Mistral
from dotenv import load_dotenv
from aiogram.utils.text_decorations import markdown_decoration
# В начале файла, после импортов:
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация клиента Mistral
client = Mistral(api_key=MISTRAL_API_KEY)

# Хранилище контекста диалога (в памяти)
user_context = {}

# Функция для экранирования спецсимволов MarkdownV2
def escape_markdown_v2(text: str) -> str:
    """
    Экранирует все зарезервированные символы MarkdownV2 для Telegram Bot API.
    Порядок важен: сначала экранируем обратные слэши, потом остальные символы.
    """
    # Сначала экранируем обратные слэши, чтобы не сломать уже добавленные
    text = text.replace('\\', '\\\\')
    
    # Символы, требующие экранирования в MarkdownV2
    # Порядок: . и ! должны быть в конце, так как они могут встречаться в URL
    escape_chars = r'_*[]()~`>#+\-=|{}.!'
    
    # Экранируем каждый спецсимвол
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я AI-ассистент на базе Mistral. Задай мне любой вопрос.")
    # Сброс контекста при старте
    user_context[message.from_user.id] = []

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Просто напиши текст, и я отвечу, используя языковую модель Mistral.")

@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    user_input = message.text

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Системный промпт: просим использовать MarkdownV2 синтаксис
        messages = [
            {"role": "system", "content": "Ты полезный ассистент в Telegram. Форматируй ответы, НЕ ИСПОЛЬЗУЯ Markdown. Избегай лишних спецсимволов."}
        ]
        
        if user_id in user_context:
            messages.extend(user_context[user_id][-6:])
        
        messages.append({"role": "user", "content": user_input})

        response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=10_024,
        )

        ai_response = response.choices[0].message.content

        # Сохранение контекста
        if user_id not in user_context:
            user_context[user_id] = []
        user_context[user_id].append({"role": "user", "content": user_input})
        user_context[user_id].append({"role": "assistant", "content": ai_response})

        # Экранируем ответ перед отправкой
        safe_response = markdown_decoration.quote(ai_response)
        print(safe_response)
        # Отправляем с parse_mode="MarkdownV2"
        await message.answer(safe_response, parse_mode="MarkdownV2")

    except Exception as e:
        logging.error(f"Ошибка API: {e}")
        # Фолбэк: отправляем простой текст без форматирования
        await message.answer("Произошла ошибка при обращении к AI.", parse_mode=None)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")