import os
import requests
import json
from notion_client import Client

# Initialize OpenAI API key from environment variable
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize Notion API
notion = Client(auth=os.environ.get("NOTION_TOKEN"))
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")


def get_word_info(word):
    """
    Use OpenAI API to get information about a word or phrase
    Returns dictionary with word_class, cn_meaning, and explanation
    Falls back to dictionary API if OpenAI fails
    """
    try:
        # First attempt with OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": """You are an assistant that helps with vocabulary. 
                    Format your response exactly according to the Notion database structure:
                    - word_class: Common word classes like n. / v. / adj. / phrase. If multiple, separate with slash like "n./v."
                    - cn_meaning: Brief, concise Chinese translation
                    - explanation: Brief English explanation followed by an example sentence, both together under 100 characters."""
                },
                {
                    "role": "user",
                    "content": f"Provide information for the word/phrase: '{word}'. Format your response as a JSON object with keys 'word_class', 'cn_meaning', and 'explanation'."
                }
            ],
            response_format={"type": "json_object"}
        )

        # Extract response content
        word_info = response.choices[0].message.content
        # Parse JSON response
        word_data = json.loads(word_info)
        return word_data, "openai"

    except Exception as e:
        print(f"OpenAI API Error: {e}")

        # Fall back to free dictionary API
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()

                # Extract word class
                word_class = data[0].get('meanings', [{}])[
                    0].get('partOfSpeech', 'unknown')

                # Format word class
                formatted_word_class = word_class
                if word_class == "noun":
                    formatted_word_class = "n."
                elif word_class == "verb":
                    formatted_word_class = "v."
                elif word_class == "adjective":
                    formatted_word_class = "adj."

                # Get definition and example
                definition = data[0].get('meanings', [{}])[0].get('definitions', [{}])[
                    0].get('definition', f'Definition for {word}')
                example = data[0].get('meanings', [{}])[0].get('definitions', [{}])[
                    0].get('example', f'Using {word} in a sentence.')

                # Add placeholder for Chinese translation
                chinese = "请手动添加中文翻译"  # "Please add Chinese translation manually"

                # Format explanation
                explanation = f"{definition} Example: {example}"
                if len(explanation) > 100:
                    explanation = explanation[:97] + "..."

                return {
                    "word_class": formatted_word_class,
                    "cn_meaning": chinese,
                    "explanation": explanation
                }, "dictionary"
            else:
                raise Exception(
                    f"Dictionary API returned status code {response.status_code}")

        except Exception as dict_error:
            print(f"Dictionary API Error: {dict_error}")

            # Last resort
            return {
                "word_class": "unknown",
                "cn_meaning": "请手动添加",  # "Please add manually"
                "explanation": f"The word '{word}' could not be processed. Please add definition manually."
            }, "fallback"


def add_to_notion(word, word_info):
    """
    Add the word and its information to Notion database
    """
    try:
        # Create a new page in the Notion database
        new_page = {
            "Word": {"title": [{"text": {"content": word}}]},
            "Word Class": {"rich_text": [{"text": {"content": word_info["word_class"]}}]},
            "CN Meaning": {"rich_text": [{"text": {"content": word_info["cn_meaning"]}}]},
            "Explanation": {"rich_text": [{"text": {"content": word_info["explanation"]}}]}
        }

        # Add the page to the database
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=new_page
        )

        return True

    except Exception as e:
        print(f"Error adding to Notion: {e}")
        return False


def process_new_word(word):
    """
    Process a new word/phrase:
    1. Get information using OpenAI
    2. Add to Notion database
    3. Return success status and message
    """
    try:
        # Get word information
        word_info, source = get_word_info(word)

        # Add to Notion
        success = add_to_notion(word, word_info)

        if success:
            source_message = ""
            if source == "dictionary":
                source_message = "\n\nNote: OpenAI API was unavailable. Used free dictionary API instead. Please update Chinese translation manually."
            elif source == "fallback":
                source_message = "\n\nNote: All APIs were unavailable. Added placeholder information. Please update manually."

            return True, f"Successfully added '{word}' to your vocabulary book!\n\n" + \
                f"Word Class: {word_info['word_class']}\n" + \
                f"Chinese: {word_info['cn_meaning']}\n" + \
                f"Explanation: {word_info['explanation']}{source_message}"
        else:
            return False, f"Failed to add '{word}' to your vocabulary book."

    except Exception as e:
        return False, f"Error processing word: {e}"


def get_random_words(count=5):
    """
    Get random words from the Notion database
    Returns a list of dictionaries with word information
    """
    try:
        # Query the database to get all entries
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID
        )

        import random
        # Get all words
        all_words = response.get("results", [])

        # Select random words if we have enough
        if len(all_words) <= count:
            selected_words = all_words
        else:
            selected_words = random.sample(all_words, count)

        # Format the word data
        words_data = []
        for entry in selected_words:
            props = entry["properties"]
            word_data = {
                "word": props["Word"]["title"][0]["text"]["content"] if props["Word"]["title"] else "Unknown",
                "word_class": props["Word Class"]["rich_text"][0]["text"]["content"] if props["Word Class"]["rich_text"] else "",
                "cn_meaning": props["CN Meaning"]["rich_text"][0]["text"]["content"] if props["CN Meaning"]["rich_text"] else "",
                "explanation": props["Explanation"]["rich_text"][0]["text"]["content"] if props["Explanation"]["rich_text"] else ""
            }
            words_data.append(word_data)

        return words_data

    except Exception as e:
        print(f"Error getting random words: {e}")
        return []
