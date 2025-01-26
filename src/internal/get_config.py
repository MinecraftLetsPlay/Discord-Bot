import json
import os

# Get config from config.json
def load_config(path='config/config.json'):
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, '..', path)
    with open(full_path, 'r') as file:
        return json.load(file)
