import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.vocabulary_processor import process_new_word, get_random_words

# Define bot handlers


async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a word to add. Usage: /add [word]")
        return

    word = " ".join(context.args)
    success, message = process_new_word(word)
    await update.message.reply_text(message)


async def send_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = get_random_words(5)
    if not words:
        await update.message.reply_text("No words found in your vocabulary book.")
        return

    message_text = "📚 *Your Vocabulary Review* 📚\n\n"
    for i, word in enumerate(words, 1):
        message_text += f"*{i}. {word['word']}* ({word['word_class']})\n"
        message_text += f"🇨🇳 {word['cn_meaning']}\n"
        message_text += f"🇬🇧 {word['explanation']}\n\n"

    await update.message.reply_text(message_text, parse_mode="Markdown")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to your Vocabulary Assistant! 📘\n"
        "- Use /add [word] to add a new word.\n"
        "- Use /send to review 5 random words."
    )

# Create the bot application


def handler(request):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    # e.g. https://your-vercel-url.vercel.app
    webhook_url = os.environ.get("WEBHOOK_URL")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("add", add_word))
    app.add_handler(CommandHandler("send", send_words))

    return app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=webhook_url,
        request=request
    )
