import random

def get_response(message: str) -> str:
    p_message = message.lower()
    
    if p_message == '!help':
        return 'Possible Commands: [System]: !shutdown, !restart [Public]: !Roll, !test.'
    
    if p_message == '!test':
        return 'Hello! I am online and ready...'
    
    if p_message == '!roll':
        return str(random.randint(1, 6))
    