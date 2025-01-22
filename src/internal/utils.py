import json
import os

def load_config(path='config/config.json'): 
    base_path = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    full_path = os.path.join(base_path, '..', path)         # Go one folder back and append the relative path
    with open(full_path, 'r') as file:
        return json.load(file)
