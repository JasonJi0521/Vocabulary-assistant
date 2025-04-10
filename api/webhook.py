import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.vocabulary_processor import process_new_word, get_random_words
import asyncio

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# FastAPI app
app = FastAPI()

# Telegram Handlers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to your Vocabulary Assistant! 📘\n"
        "- Use /add [word] to add a word.\n"
        "- Use /send to get 5 review words."
    )


async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a word: /add [word]")
        return
    word = " ".join(context.args)
    success, message = process_new_word(word)
    await update.message.reply_text(message)


async def send_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = get_random_words(5)
    if not words:
        await update.message.reply_text("No words in your vocabulary book.")
        return
    msg = "📚 *Your Vocabulary Review* 📚\n\n"
    for i, word in enumerate(words, 1):
        msg += f"*{i}. {word['word']}* ({word['word_class']})\n"
        msg += f"🇨🇳 {word['cn_meaning']}\n"
        msg += f"🇬🇧 {word['explanation']}\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# Register Handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", start))
bot_app.add_handler(CommandHandler("add", add_word))
bot_app.add_handler(CommandHandler("send", send_words))


@app.post("/")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = Update.de_json(body, bot_app.bot)

    await bot_app.initialize()
    await bot_app.process_update(update)
    return {"ok": True}
