import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

class CustomRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None):
        # Generiere initialen Dateinamen mit Zeitstempel
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        filename = f'{filename}_{timestamp}.txt'
        super().__init__(filename, when, interval, backupCount, encoding=encoding)

    def rotation_filename(self, default_name):
        # Generiere neuen Dateinamen bei Rotation
        dir_name, base_name = os.path.split(default_name)
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        return os.path.join(dir_name, f'bot.log_{timestamp}.txt')

# Rest der Konfiguration
config = utils.load_config()
log_directory = config.get("log_file_location")

# Ensure log directory exists
if not os.path.exists(log_directory):
    try:
        os.makedirs(log_directory)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        sys.exit(1)

# Setup logging with CustomRotatingFileHandler
log_file = os.path.join(log_directory, 'bot.log')
handler = CustomRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=10,
    encoding="utf-8"
)

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