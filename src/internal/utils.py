import json
import os

# Get config from ./data/config.json
def load_config(path='internal/data/config.jsonc'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    with open(full_path, 'r') as file:
        return json.load(file)

# Get quiz data from ./data/quiz.jsonc
def load_quiz(path='internal/data/quiz.jsonc'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    try:
        with open(full_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading quiz file: {e}")
        return {}

# Get hangman words from ./data/hangman.jsonc
def load_hangman(path='internal/data/hangman.jsonc'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    try:
        with open(full_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading hangman file: {e}")
        return {}
