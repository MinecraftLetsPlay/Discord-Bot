import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

def setup_logging():
    # Load configuration
    config = utils.load_config()
    log_directory = config.get("log_file_location")

    # Ensure the log directory exists
    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except PermissionError as e:
            print(f"Permission denied: {e}")
            sys.exit(1)

    # Get the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers to prevent duplicate logging
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Setup file handler
    timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
    log_file = os.path.join(log_directory, f'bot.log_{timestamp}.txt')
    
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    # Configure Discord logger
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)

    # Test logging
    root_logger.info('Logging system initialized')
    return root_logger