import json
import os

# Get config from config.json
def load_config(path='config/config.json'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    with open(full_path, 'r') as file:
        return json.load(file)

# Get quiz data from quiz.json
def load_quiz(path='config/quiz.json'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    try:
        with open(full_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading quiz file: {e}")
        return {}