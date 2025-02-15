import os
import sys
import logging
from internal import utils

# Load config
config = utils.load_config()
log_directory = config.get("log_file_location", "/home/Dennis/Desktop/Storage/Logs")

# Ensure log directory exists
if not os.path.exists(log_directory):
    try:
        os.makedirs(log_directory)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        sys.exit(1)

# Setup logging
log_file = os.path.join(log_directory, 'log01.txt')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_file),
    logging.StreamHandler()
])

# Function to rotate logs
def rotate_logs():
    log_files = sorted([f for f in os.listdir(log_directory) if f.startswith('log') and f.endswith('.txt')])
    if len(log_files) >= 10:
        os.remove(os.path.join(log_directory, log_files[0]))
        for i, log_file in enumerate(log_files[1:], start=1):
            os.rename(os.path.join(log_directory, log_file), os.path.join(log_directory, f'log{i:02d}.txt'))

rotate_logs()