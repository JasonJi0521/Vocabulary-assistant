from flask import Flask, request
import os
import telegram
from telegram import Update
import asyncio
from utils.notion_handler import add_to_notion, get_random_words
from utils.openai_handler import get_word_info

# Setup
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

# Async function to handle new words


async def process_new_word(word):
    try:
        word_info, source = get_word_info(word)
        success = add_to_notion(word, word_info)

        if success:
            source_message = ""
            if source == "dictionary":
                source_message = "\n\nNote: Used free dictionary API. Please update Chinese translation manually."
            elif source == "fallback":
                source_message = "\n\nNote: Added placeholder information. Please update manually."

            return f"✅ '{word}' added!\n{word_info['word_class']} | {word_info['cn_meaning']}\n{word_info['explanation']}{source_message}"
        else:
            return f"❌ Failed to add '{word}' to your vocabulary book."
    except Exception as e:
        return f"⚠️ Error: {e}"

# Webhook endpoint


@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text.strip()

    async def respond():
        if text.startswith("/add "):
            word = text[5:]
            message = await process_new_word(word)
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

    asyncio.run(respond())
    return "OK"
