import logging
import os
import sys
from datetime import datetime
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

# Function to rotate logs
def rotate_logs():
    log_files = sorted([f for f in os.listdir(log_directory) if f.startswith('log') and f.endswith('.txt')])
    if len(log_files) >= 10:
        os.remove(os.path.join(log_directory, log_files[0]))
        for i, log_file in enumerate(log_files[1:], start=1):
            os.rename(os.path.join(log_directory, log_file), os.path.join(log_directory, f'log{i:02d}.txt'))

rotate_logs()

# Create a new log file with a timestamp
timestamp = datetime.now().strftime("%d.%m.%Y %H.%M.%S")
log_file = os.path.normpath(os.path.join(log_directory, f'log_{timestamp}.txt'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)

# Set Discord logger to WARNING to prevent it from logging to "bot.log"
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)