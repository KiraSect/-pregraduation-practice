import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura

from dotenv import load_dotenv
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)


load_dotenv(Path(__file__).with_name(".env"))

TELEGRAM_TOKEN = Path
GROQ_API_KEY = Path

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MAX_TEXT_LENGTH = 12000

SYSTEM_PROMPT = """
Ты помогаешь кратко пересказывать статьи.

Правила:
- ровно 5 пунктов
- каждый пункт с новой строки
- коротко и понятно
- без вступления
- сохраняй важные даты, цифры и имена
- отвечай только на русском языке
"""


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)

    return all([
        parsed.scheme,
        parsed.netloc
    ])


def extract_text_from_url(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; SummaryBot/1.0)"
                )
            }
        )

        response.raise_for_status()

        text = trafilatura.extract(
            response.text
        )

        return text or ""

    except Exception as e:
        logger.error(
            f"Ошибка извлечения текста: {e}"
        )
        return ""


def summarize_text(text: str) -> str:
    text = text[:MAX_TEXT_LENGTH]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Привет.\n\n"
        "Пришли ссылку на статью, "
        "и я сделаю краткое содержание."
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_text = update.message.text.strip()

    if not is_valid_url(user_text):
        await update.message.reply_text(
            "Пожалуйста, пришли корректную ссылку."
        )
        return

    await update.message.reply_text(
        "Скачиваю статью..."
    )

    article_text = extract_text_from_url(
        user_text
    )

    if not article_text:
        await update.message.reply_text(
            "Не удалось извлечь текст из статьи."
        )
        return

    if len(article_text) < 200:
        await update.message.reply_text(
            "Текст слишком короткий для пересказа."
        )
        return

    await update.message.reply_text(
        "Делаю краткое содержание..."
    )

    try:
        summary = summarize_text(
            article_text
        )

        await update.message.reply_text(
            f"Краткое содержание:\n\n{summary}"
        )

    except Exception as e:
        logger.error(
            f"Ошибка LLM: {e}"
        )

        await update.message.reply_text(
            "Ошибка при обращении к LLM."
        )

def main():
    if not TELEGRAM_TOKEN:
        print(
            "Ошибка: TELEGRAM_TOKEN "
            "не найден в .env"
        )
        return

    if not GROQ_API_KEY:
        print(
            "Ошибка: GROQ_API_KEY "
            "не найден в .env"
        )
        return

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print(
        "Бот запущен. "
        "Нажми CTRL+C для остановки."
    )

    app.run_polling()


if __name__ == "__main__":
    main()