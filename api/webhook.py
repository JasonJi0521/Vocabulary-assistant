from utils.vocabulary_processor import process_new_word, get_random_words
from flask import Flask, request
import os
import telegram
from telegram import Update
import asyncio
import sys

# Ensure utils/ folder is in the path for import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


# Setup Telegram bot
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)


@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text.strip()

    async def respond():
        if text.startswith("/add "):
            word = text[5:].strip()
            success, message = process_new_word(word)
            await bot.send_message(chat_id=chat_id, text=message)

        elif text == "/send":
            words = get_random_words(5)
            if words:
                msg = "📚 *Your Vocabulary Review* 📚\n\n"
                for i, word in enumerate(words, 1):
                    msg += f"*{i}. {word['word']}* ({word['word_class']})\n"
                    msg += f"🇨🇳 {word['cn_meaning']}\n"
                    msg += f"🇬🇧 {word['explanation']}\n\n"
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            else:
                await bot.send_message(chat_id=chat_id, text="No words found in your vocabulary book.")

        elif text in ["/start", "/help"]:
            await bot.send_message(chat_id=chat_id, text=(
                "Welcome to your Vocabulary Assistant! 📘\n"
                "- Use `/add [word]` to add a word.\n"
                "- Use `/send` to get a quiz of 5 random words."
            ))
        else:
            await bot.send_message(chat_id=chat_id, text=f"Want to add \"{text}\"? Try: /add {text}")

    try:
        asyncio.run(respond())
        return "OK"
    except Exception as e:
        print("❌ Error in webhook POST:", e)
        return "Error", 500
