import os
import json
import asyncio
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from utils.vocabulary_processor import process_new_word, get_random_words

# Rebuild the application every request (stateless mode)


def build_bot_app():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Welcome to your Vocabulary Assistant! 📘\n"
            "- Use /add [word] to add a new word.\n"
            "- Use /send to review 5 random words."
        )

    async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /add [word]")
            return
        word = " ".join(context.args)
        success, msg = process_new_word(word)
        await update.message.reply_text(msg)

    async def send_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
        words = get_random_words(5)
        if not words:
            await update.message.reply_text("No words found.")
            return
        msg = "📚 *Your Vocabulary Review* 📚\n\n"
        for i, word in enumerate(words, 1):
            msg += f"*{i}. {word['word']}* ({word['word_class']})\n"
            msg += f"🇨🇳 {word['cn_meaning']}\n"
            msg += f"🇬🇧 {word['explanation']}\n\n"
        await update.message.reply_text(msg, parse_mode="Markdown")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("add", add_word))
    app.add_handler(CommandHandler("send", send_words))
    return app

# Vercel-compatible serverless webhook handler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"✅ Vocabulary bot webhook is up and running.")

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        raw_data = self.rfile.read(content_len)
        data = json.loads(raw_data.decode("utf-8"))

        update = Update.de_json(data, build_bot_app().bot)

        # Process one update, no persistent loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_app = build_bot_app()
        loop.run_until_complete(bot_app.process_update(update))
        loop.close()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
