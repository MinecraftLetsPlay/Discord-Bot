import logging
import os
import sys
import zoneinfo
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from internal import utils

# Copyright (c) 2026 Dennis Plischke.
# All rights reserved.

# ================================================================
# Module: Logging_setup.py
# Description: Sets up logging with daily rotation and stable filenames
# Error handling for file operations included
# ================================================================

# Local timezone
try:
    LOCAL_TZ = zoneinfo.ZoneInfo("Europe/Berlin")
except Exception as e:
    print(f"⚠️ Failed to set timezone, using UTC: {e}")
    LOCAL_TZ = None

# Get current local time
def now_local():
    try:
        if LOCAL_TZ:
            return datetime.now(LOCAL_TZ)
        else:
            return datetime.utcnow()
    except Exception as e:
        print(f"⚠️ Error getting local time: {e}")
        return datetime.utcnow()

# Custom Timed Rotating File Handler with error handling
class CustomTimedRotatingFileHandler(logging.FileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None):
        self.base_filename = filename
        self.when = when
        self.interval = interval
        self.backupCount = backupCount
        self.last_rollover = None
        
        # Create directory
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Cannot create log directory: {e}")
        except OSError as e:
            raise OSError(f"Error creating log directory: {e}")
        
        # Create initial log file
        try:
            timestamp = now_local().strftime("%d.%m.%Y_%H-%M-%S")
            current_file = f"{self.base_filename}-{timestamp}.txt"
            super().__init__(current_file, encoding=encoding)
            self.last_rollover = now_local().date()
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid filename format: {e}")
        except IOError as e:
            raise IOError(f"Cannot create log file: {e}")
    
    # Override emit to handle rollover
    def emit(self, record):
        try:
            # Check if we need to rollover
            current_date = now_local().date()
            if self.last_rollover and current_date != self.last_rollover:
                self.doRollover()
                self.last_rollover = current_date
            
            super().emit(record)
        except Exception as e:
            # Fallback: print to stderr if logging fails
            print(f"⚠️ Logging error: {e}", file=sys.stderr)
            try:
                self.handleError(record)
            except Exception:
                pass
    
    # Rollover log file
    def doRollover(self):
        try:
            # Close current stream
            if self.stream:
                self.stream.close()
            
            # Create new file with new timestamp
            timestamp = now_local().strftime("%d.%m.%Y_%H:%M:%S")
            new_file = f"{self.base_filename}-{timestamp}.txt"
            
            self.baseFilename = new_file
            self.stream = self._open()
            
            # Cleanup old log files
            self._cleanup_old_logs()
            
        except IOError as e:
            print(f"⚠️ Error during log rollover: {e}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ Unexpected error during rollover: {e}", file=sys.stderr)
    
    # Delete old log files exceeding backupCount
    def _cleanup_old_logs(self):
        try:
            log_dir = os.path.dirname(self.base_filename)
            log_basename = os.path.basename(self.base_filename)
            
            if not os.path.exists(log_dir):
                return
            
            # List all matching log files
            log_files = [
                f for f in os.listdir(log_dir)
                if f.startswith(log_basename) and f.endswith('.txt')
            ]
            
            # Sort by modification time (oldest first)
            log_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(log_dir, f))
            )
            
            # Remove oldest files if exceeding backupCount
            if len(log_files) > self.backupCount:
                for old_file in log_files[:-self.backupCount]:
                    try:
                        os.remove(os.path.join(log_dir, old_file))
                    except OSError as e:
                        print(f"⚠️ Could not delete old log file {old_file}: {e}", file=sys.stderr)
        
        except Exception as e:
            print(f"⚠️ Error during log cleanup: {e}", file=sys.stderr)


# ----------------------------------------------------------------
# Main Logging Setup
# ----------------------------------------------------------------

# Setup logging function
def setup_logging():
    try:
        # Load configuration
        try:
            config = utils.load_config()
            debug_mode = config.get("DebugModeActivated", False)
            log_directory = config.get("log_file_location", "logs")
        except Exception as e:
            print(f"⚠️ Failed to load config, using defaults: {e}")
            debug_mode = False
            log_directory = "logs"
        
        # Validate log directory
        if not isinstance(log_directory, str) or not log_directory.strip():
            log_directory = "logs"
        
        # Create log directory if needed
        try:
            if not os.path.exists(log_directory):
                os.makedirs(log_directory, exist_ok=True)
        except PermissionError:
            print(f"❌ Permission denied creating log directory: {log_directory}")
            print("⚠️ Falling back to current directory for logs")
            log_directory = "."
        except OSError as e:
            print(f"❌ Error creating log directory: {e}")
            print("⚠️ Falling back to current directory for logs")
            log_directory = "."
        
        # Get root logger
        root_logger = logging.getLogger()
        
        # Remove old handlers
        for handler in root_logger.handlers[:]:
            try:
                root_logger.removeHandler(handler)
            except Exception as e:
                print(f"⚠️ Error removing handler: {e}")
        
        # Create formatter
        try:
            formatter = logging.Formatter(
                '%(asctime)s - %(module)s : %(levelname)s - %(message)s',
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        except Exception as e:
            print(f"⚠️ Error creating formatter, using default: {e}")
            formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        # File handler
        try:
            log_file_base = os.path.join(log_directory, "bot.log")
            file_handler = CustomTimedRotatingFileHandler(
                log_file_base,
                when="midnight",
                interval=1,
                backupCount=14,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
            root_logger.addHandler(file_handler)
        except PermissionError:
            print(f"❌ Permission denied creating log file in {log_directory}")
        except Exception as e:
            print(f"⚠️ Failed to setup file handler: {e}")
        
        # Console handler
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
            root_logger.addHandler(console_handler)
        except Exception as e:
            print(f"⚠️ Failed to setup console handler: {e}")
        
        # Set root logger level
        try:
            root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)  # Dynamic logging
        except Exception as e:
            print(f"⚠️ Error setting root logger level: {e}")
        
        # Discord logger (reduce noise)
        try:
            discord_logger = logging.getLogger('discord')
            discord_logger.setLevel(logging.WARNING)
        except Exception as e:
            print(f"⚠️ Error configuring discord logger: {e}")
        
        return root_logger
    
    except Exception as e:
        print(f"❌ Critical error in setup_logging: {e}", file=sys.stderr)
        # Fallback: return basic logger
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger()
