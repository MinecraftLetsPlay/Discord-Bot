import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None):
        # Generiere den initialen Dateinamen mit Zeitstempel
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        filename = f"{filename}-{timestamp}.txt"
        super().__init__(filename, when, interval, backupCount, encoding=encoding)

    def rotation_filename(self, default_name):
        # Generiere den neuen Dateinamen während der Rotation
        dir_name, base_name = os.path.split(default_name)
        timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        return os.path.join(dir_name, f"bot.log-{timestamp}.txt")

def setup_logging():
    # Lade die Konfiguration
    config = utils.load_config()
    log_directory = config.get("log_file_location")

    # Stelle sicher, dass das Log-Verzeichnis existiert
    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except PermissionError as e:
            print(f"Permission denied: {e}")
            sys.exit(1)

    # Hole den Root-Logger
    root_logger = logging.getLogger()
    
    # Entferne vorhandene Handler, um doppelte Logs zu vermeiden
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Erstelle den Formatter
    formatter = logging.Formatter('%(asctime)s - %(module)s : %(levelname)s - %(message)s')

    # Setup File Handler mit benutzerdefiniertem Dateinamen
    log_file = os.path.join(log_directory, 'bot.log')
    file_handler = CustomTimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Setup Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Füge die Handler dem Root-Logger hinzu
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    # Konfiguriere den Discord-Logger
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)

    return root_logger