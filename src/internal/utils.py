import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the absolute path of a file based on a relative path
def get_full_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, '..', relative_path)

# Load a JSON file and return its content
def load_json_file(path):
    full_path = get_full_path(path)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"❌ File not found at {full_path}.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"❌ Error decoding JSON in file {full_path}: {e}")
        return {}
    except Exception as e:
        logging.error(f"❌ Unexpected error loading file {full_path}: {e}")
        return {}

# Save data to a JSON file
def save_json_file(data, path):
    full_path = get_full_path(path)
    try:
        with open(full_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        logging.error(f"❌ Error saving file {full_path}: {e}")

# Load the bot configuration file
def load_config():
    return load_json_file('internal/data/config.json')

# Load quiz data
def load_quiz():
    return load_json_file('internal/data/quiz.json')

# Load hangman data
def load_hangman():
    return load_json_file('internal/data/hangman.json')

# Load scrabble data
def load_scrabble():
    return load_json_file('internal/data/scrabble_letters.json')

# Load reaction role data
def load_reaction_role_data():
    return load_json_file('internal/data/reactionrole.json')

# Save reaction role data
def save_reaction_role_data(data):
    save_json_file(data, 'internal/data/reactionrole.json')