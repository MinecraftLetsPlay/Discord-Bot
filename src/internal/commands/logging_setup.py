import logging
import os
import sys
import zoneinfo
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

# Copyright (c) 2025 Dennis Plischke.
# All rights reserved.

# ----------------------------------------------------------------
# Module: Logging_setup.py
# Description: Sets up logging with daily rotation and stable filenames
# ----------------------------------------------------------------


# Local timezone
LOCAL_TZ = zoneinfo.ZoneInfo("Europe/Berlin")

# Get current local time
def now_local():
    return datetime.now(LOCAL_TZ)

# A custom TimedRotatingFileHandler that uses local time and stable filenames
class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None):
        # base filename without timestamp
        self.base_filename = filename
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # create first file
        timestamp = now_local().strftime("%d.%m.%Y_%H.%M.%S")
        current_file = f"{self.base_filename}-{timestamp}.txt"

        super().__init__(current_file, when, interval, backupCount, encoding=encoding, utc=False)
        
    # Override to use local time
    def rotation_filename(self, default_name):
        dir_name = os.path.dirname(self.base_filename)
        timestamp = now_local().strftime("%d.%m.%Y_%H.%M.%S")
        return os.path.join(dir_name, f"bot.log-{timestamp}.txt")

    # Do log rotation
    def doRollover(self):
        from internal.commands.system_commands import rotate_logs
        super().doRollover()
        rotate_logs()


# ----------------------------------------------------------------
# Main logging setup
# ----------------------------------------------------------------

# Setup logging configuration
def setup_logging():
    # Load configuration
    config = utils.load_config()
    debug_mode = config.get("DebugModeActivated", False)
    log_directory = config.get("log_file_location")

    if not isinstance(log_directory, str) or not log_directory:
        log_directory = "logs"

    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except PermissionError as e:
            print(f"Permission denied: {e}")
            sys.exit(1)

    # Root logger
    root_logger = logging.getLogger()

    # Remove old handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(module)s : %(levelname)s - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    log_file_base = os.path.join(log_directory, "bot.log")
    file_handler = CustomTimedRotatingFileHandler(
        log_file_base,
        when="midnight",
        interval=1,
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Register both handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

    # Discord logger (less noise)
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)

    return root_logger
