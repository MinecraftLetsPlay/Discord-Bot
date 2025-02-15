import bot
import logging
import sys

# Configure logging to handle Unicode characters
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('bot.log', encoding='utf-8'),
    logging.StreamHandler(sys.stdout)
])

# Main entry point
if __name__ == '__main__':
    bot.run_discord_bot()
