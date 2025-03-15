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

# Generate initial log file name with timestamp
timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
log_file = os.path.join(log_directory, f'bot_{timestamp}.log')

# Setup logging with TimedRotatingFileHandler
handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=10,
    encoding="utf-8"
)

# Configure the handler
handler.suffix = "%d.%m.%Y_%H.%M.%S"
handler.namer = lambda name: name.replace(".log.", "_") + ".txt"

# Basic logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        handler,
        logging.StreamHandler(sys.stdout)
    ]
)

# Set Discord logger to WARNING
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)