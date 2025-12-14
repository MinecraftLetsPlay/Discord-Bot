import json
import os
import logging
import threading
import tempfile
from typing import Optional

# Copyright (c) 2025 Dennis Plischke.
# All rights reserved.

# ----------------------------------------------------------------
# Module: Utils.py
# Description: File loding and read / write operations
# ----------------------------------------------------------------

logging.basicConfig(level=logging.INFO)

# Simple in-process locks for each file
_file_locks = {}
def _get_lock(path: str) -> threading.Lock:
    return _file_locks.setdefault(path, threading.Lock())

# Ensure directory exists
def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    
# Helpers to resolve data paths
BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
def _abs_path(*parts):
    return os.path.join(BASE_DATA_DIR, *parts)

# Atomic write function using locks
def _atomic_write(file_path: str, data: dict):
    lock = _get_lock(file_path)
    with lock:
        _ensure_dir(os.path.dirname(file_path))
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(file_path), prefix=".tmp_", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            raise

# Atomic read function using locks
def _atomic_read(file_path: str) -> dict:
    lock = _get_lock(file_path)
    with lock:
        if not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError:
            logging.error(f"❌ Invalid JSON in {file_path}")
            return {}
        except Exception as e:
            logging.error(f"❌ Error reading {file_path}: {e}")
            return {}

# For scrabble data files
def load_json_file(rel_path: str) -> dict:
    try:
        if rel_path.startswith("internal/"):
            parts = rel_path.split("/")[2:]  # strip 'internal/data/...'
            path = _abs_path(*parts)
        else:
            parts = rel_path.split("/")
            path = _abs_path(*parts)
        return _atomic_read(path) or {}
    except Exception as e:
        logging.error(f"❌ Error loading json file '{rel_path}': {e}")
        return {}
    
    
# --------------------------
# Authorization helpers
# --------------------------

# Global authorization uses global config
def is_authorized_global(user):
    try:
        cfg = load_config()
        whitelist = cfg.get("whitelist", []) or []
        return str(user.id) in whitelist
    except Exception as e:
        logging.error(f"❌ Error checking global authorization: {e}")
        return False

# Server-specific authorization uses per-server config and auto trusts guild.owner
def is_authorized_server(user, guild_id: int):
    try:
        import discord
        
        server_config = load_server_config(guild_id)
        whitelist = server_config.get("whitelist", []) or []

        # If whitelist is not empty, honor it
        if whitelist:
            return str(user.id) in whitelist

        # Whitelist empty -> auto-trust only the guild owner (persisted)
        if isinstance(user, discord.Member):
            try:
                if user.guild is not None and user.id == user.guild.owner_id:
                    whitelist.append(str(user.id))
                    server_config["whitelist"] = whitelist
                    save_server_config(guild_id, server_config)
                    logging.info(f"Auto-added guild owner {user.id} to whitelist for guild {guild_id}.")
                    return True
            except Exception as e:
                logging.warning(f"Could not evaluate member as guild owner for guild {guild_id}: {e}")

        # No match in server whitelist and not guild owner -> deny
        return False
        
    except Exception as e:
        logging.error(f"❌ Error checking server authorization for {guild_id}: {e}")
        return False

# --------------------------
# Global config
# --------------------------

# Function to load global config with the atomic read function
def load_config() -> dict:
    return _atomic_read(_abs_path("config.json"))

# Helper to save JSON file at given relative path
def save_json_file(data: dict, rel_path: str):
    path = _abs_path(*rel_path.split("/")[2:]) if rel_path.startswith("internal/") else _abs_path(rel_path)
    _atomic_write(path, data)

# Helper to set config value
def set_config_value(key: str, value):
    path = _abs_path("config.json")
    cfg = _atomic_read(path)
    cfg[key] = value
    _atomic_write(path, cfg)

# Helper to get config value with optional guild override
def get_config_value(key: str, guild_id: Optional[int] = None, default=None):
    if guild_id is not None:
        srv = load_server_config(guild_id)
        if key in srv:
            return srv[key]
    cfg = load_config()
    return cfg.get(key, default)

# ---------------------------------
# Server configs (per-guild files)
# ---------------------------------

# Configure new files for servers with standard default values
def _default_server_config() -> dict:
    return {
        "whitelist": [],
        "LoggingActivated": True,
        "logging_config": {
            "log_all_by_default": True,
            "enabled_channels": [],
            "disabled_channels": []
        },
        "music_channel_id": ""
    }

# Create server config file if it does not exist
def create_server_config(guild_id: int) -> dict:
    servers_dir = _abs_path("servers")
    _ensure_dir(servers_dir)
    path = os.path.join(servers_dir, f"{guild_id}.json")
    default = _default_server_config()
    _atomic_write(path, default)
    return default

# Function to load server config with the atomic read function
def load_server_config(guild_id: int) -> dict:
    servers_dir = _abs_path("servers")
    _ensure_dir(servers_dir)
    path = os.path.join(servers_dir, f"{guild_id}.json")
    if not os.path.exists(path):
        return create_server_config(guild_id)
    data = _atomic_read(path)
    if not data:
        # file exists but empty/invalid -> overwrite with defaults
        return create_server_config(guild_id)
    return data

# Function to save server config with the atomic write function
def save_server_config(guild_id: int, data: dict):
    servers_dir = _abs_path("servers")
    _ensure_dir(servers_dir)
    path = os.path.join(servers_dir, f"{guild_id}.json")
    _atomic_write(path, data)

# --------------------------
# Reaction roles helpers
# --------------------------
def load_reaction_role_data():
    return _atomic_read(_abs_path("reactionrole.json"))

def save_reaction_role_data(data):
    _atomic_write(_abs_path("reactionrole.json"), data)
    
# --------------------------
# Logging helpers
# --------------------------

# Function to determine if a channel is logged
def is_channel_logged(guild_id: int, channel_id: int) -> bool:
    try:
        srv = load_server_config(guild_id)
        logging_config = srv.get("logging_config", {})
        log_all = logging_config.get("log_all_by_default", True)
        enabled = logging_config.get("enabled_channels", []) or []
        disabled = logging_config.get("disabled_channels", []) or []

        cid = str(channel_id)

        # Normalize entries (accept both ints and strings)
        enabled_set = {str(x) for x in enabled}
        disabled_set = {str(x) for x in disabled}

        if cid in disabled_set:
            return False
        if enabled_set and cid in enabled_set:
            return True
        return bool(log_all)
    except Exception as e:
        logging.error(f"❌ Error evaluating channel logging for guild {guild_id}: {e}")
        return True  # safe default: log

# --------------------------
# Minigames data helpers
# --------------------------

# Hangman, Quiz, Scrabble data loaders

def load_hangman() -> dict:
    return _atomic_read(_abs_path("hangman.json")) or {}

def load_quiz() -> dict:
    return _atomic_read(_abs_path("quiz.json")) or {}

def load_scrabble(language):
    file_mapping = {
        'En': 'internal/data/scrabble_letters_en.json',
        'De': 'internal/data/scrabble_letters_de.json'
    }

    if language not in file_mapping:
        logging.error(f"❌ Unsupported language '{language}' for Scrabble data.")
        return {}

    return load_json_file(file_mapping[language])