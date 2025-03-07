import json
import os

# Get config from ./data/config.json
def load_config(path='internal/data/config.json'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    with open(full_path, 'r') as file:
        return json.load(file)

# Get quiz data from ./data/quiz.jsonc
def load_quiz(path='internal/data/quiz.json'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    try:
        with open(full_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"❌ Error loading quiz file: {e}")
        return {}

# Get hangman data from ./data/hangman.json
def load_hangman(path='internal/data/hangman.json'):
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_path, path)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"❌ Error loading hangman file: {e}")
        return {}

# Get reaction role data from ./data/reactionrole.json
def load_reaction_role_data():
    with open('src/internal/data/reactionrole.json', 'r') as f:
        return json.load(f)

# Save reaction role data to ./data/reactionrole.json
def save_reaction_role_data(data):
    with open('src/internal/data/reactionrole.json', 'w') as f:
        json.dump(data, f, indent=4)