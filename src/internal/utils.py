import json

def load_config(path='src/config/config.json'):
    with open(path, 'r') as file:
        return json.load(file)
