import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

# Load config
config = utils.load_config()
log_directory = config.get("log_file_location")

# Ensure log directory exists
if not os.path.exists(log_directory):
    try:
        os.makedirs(log_directory)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        sys.exit(1)

# Create a new log file with a timestamp
log_file = os.path.normpath(os.path.join(log_directory, f'bot.log'))

# Setup logging with TimedRotatingFileHandler
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=10, encoding="utf-8")
handler.suffix = "%d.%m.%Y_%H.%M.%S"

logging.basicConfig(
    level=logging.DEBUG,  # Set logging level to DEBUG
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        handler,
        logging.StreamHandler(sys.stdout),
    ]
)

# Set Discord logger to WARNING to prevent it from logging to "bot.log"
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)