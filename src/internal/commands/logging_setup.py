import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

# ----------------------------------------------------------------
# Module: Logging Setup
# Description: Sets up logging with daily rotation and custom filenames
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# Helpers for logging setup
# ----------------------------------------------------------------
# Create Timestamps for log files
class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None):
        # Generate initial filename with timestamp
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        filename = f"{filename}-{timestamp}.txt"
        super().__init__(filename, when, interval, backupCount, encoding=encoding)

    def rotation_filename(self, default_name):
        # Generate new filename during rotation
        dir_name, base_name = os.path.split(default_name)
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        return os.path.join(dir_name, f"bot.log-{timestamp}.txt")
    
    def doRollover(self):
        from internal.commands.system_commands import rotate_logs
        super().doRollover()
        rotate_logs()  # Delete old log files after rollover

# ----------------------------------------------------------------
# Main function to setup logging
# ----------------------------------------------------------------
def setup_logging():
    # Load configuration
    config = utils.load_config()
    debug_mode = config.get("DebugModeActivated", False)
    log_directory = config.get("log_file_location")

    # Fallback, if Log_file_location is not set or invalid
    if not isinstance(log_directory, str) or not log_directory:
        log_directory = "logs"

    # Ensure log directory exists
    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except PermissionError as e:
            print(f"Permission denied: {e}")
            sys.exit(1)

    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove existing handlers to prevent duplicate logging
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(module)s : %(levelname)s - %(message)s')

    # Setup file handler with custom filename
    log_file = os.path.join(log_directory, 'bot.log')
    file_handler = CustomTimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

    # Configure Discord logger
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)

    return root_logger