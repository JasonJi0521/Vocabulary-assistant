from http.server import BaseHTTPRequestHandler
import json
import os
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from utils.notion_handler import add_to_notion, get_random_words
from utils.openai_handler import get_word_info

# Initialize with environment variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Initialize bot
bot = telegram.Bot(token=TOKEN)

# Helper function to process new words


async def process_new_word(word):
    try:
        # Get word information
        word_info, source = get_word_info(word)

        # Add to Notion
        success = add_to_notion(word, word_info)

        if success:
            source_message = ""
            if source == "dictionary":
                source_message = "\n\nNote: Used free dictionary API. Please update Chinese translation manually."
            elif source == "fallback":
                source_message = "\n\nNote: Added placeholder information. Please update manually."

            return True, f"Successfully added '{word}' to your vocabulary book!\n\n" + \
                f"Word Class: {word_info['word_class']}\n" + \
                f"Chinese: {word_info['cn_meaning']}\n" + \
                f"Explanation: {word_info['explanation']}{source_message}"
        else:
            return False, f"Failed to add '{word}' to your vocabulary book."

    except Exception as e:
        return False, f"Error processing word: {e}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # For webhook verification
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Webhook is active!".encode())

    async def process_update(self, update_data):
        # Create an Update object
        update = Update.de_json(update_data, bot)

        if not update or not update.message:
            return

        message = update.message
        chat_id = message.chat_id

        # Process commands
        if message.text:
            text = message.text

            # Handle /add command
            if text.startswith('/add '):
                word = text[5:].strip()
                if word:
                    success, response = await process_new_word(word)
                    await bot.send_message(chat_id=chat_id, text=response)
                else:
                    await bot.send_message(chat_id=chat_id, text="Please provide a word to add.")

            # Handle /send command
            elif text == '/send':
                words = get_random_words(5)
                if words:
                    message_text = "📚 *Your Vocabulary Review* 📚\n\n"
                    for i, word in enumerate(words, 1):
                        message_text += f"*{i}. {word['word']}* ({word['word_class']})\n"
                        message_text += f"🇨🇳 {word['cn_meaning']}\n"
                        message_text += f"🇬🇧 {word['explanation']}\n\n"
                    await bot.send_message(chat_id=chat_id, text=message_text, parse_mode='Markdown')
                else:
                    await bot.send_message(chat_id=chat_id, text="No words found in your vocabulary book.")

            # Handle /start and /help commands
            elif text == '/start' or text == '/help':
                await bot.send_message(
                    chat_id=chat_id,
                    text='Welcome to your Vocabulary Assistant! 📚\n\n'
                         'Use /add [word] to add a new word to your Notion vocabulary book.\n'
                         'Use /send to get 5 random words from your vocabulary collection.'
                )
            # Handle regular messages
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f'Do you want to add "{text}" to your vocabulary book? Use /add {text}'
                )

    def do_POST(self):
        # Get request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # Parse JSON
        update_data = json.loads(post_data.decode('utf-8'))

        # Process update asynchronously
        asyncio.run(self.process_update(update_data))

        # Send response
        self.send_response(200)
        self.end_headers()
