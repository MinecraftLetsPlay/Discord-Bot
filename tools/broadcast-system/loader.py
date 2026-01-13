import json
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (searches current dir and parent dirs)
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('broadcast.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

class BroadcastLoader:
    # Load server and channel configurations for broadcasting
    
    def __init__(self, config_path: Optional[str] = None):
        # Initialize loader with config path
        if config_path is None:
            # Auto-detect: go up from broadcast-system to project root
            # Path: .../Discord-Bot/tools/broadcast-system/loader.py
            # Need: .../Discord-Bot/src/internal/data
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # Go up 2 levels: broadcast-system -> tools -> Discord-Bot
            config_path = str(project_root / "src" / "internal" / "data")
        
        self.config_path = Path(config_path)
        self.servers_dir = self.config_path / "servers"
        
        if not self.servers_dir.exists():
            raise FileNotFoundError(f"Servers directory not found at {self.servers_dir}")
        
        log.info(f"BroadcastLoader initialized with path: {self.config_path}")
    
    def load_server_configs(self) -> List[Tuple[int, Dict]]:
        # Load all server configurations that have broadcasting enabled
        servers_with_broadcast = []
        
        try:
            # Iterate through all {guild_id}.json files in servers directory
            for config_file in self.servers_dir.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        server_config = json.load(f)
                    
                    # Extract guild_id from filename: {guild_id}.json
                    guild_id = int(config_file.stem)
                    
                    # Check if announcements are enabled
                    announcements = server_config.get("announcements", {})
                    
                    if isinstance(announcements, dict) and announcements.get("enabled", False):
                        channel_id = announcements.get("channel_id")
                        
                        if channel_id:
                            servers_with_broadcast.append((guild_id, {
                                "guild_id": guild_id,
                                "channel_id": int(channel_id) if isinstance(channel_id, str) else channel_id,
                                "config": server_config
                            }))
                            log.debug(f"Found broadcast config for guild {guild_id}")
                        else:
                            log.warning(f"Guild {guild_id}: announcements enabled but no channel_id specified")
                
                except (json.JSONDecodeError, ValueError) as e:
                    log.warning(f"Invalid config file {config_file}: {e}")
                    continue
                except Exception as e:
                    log.error(f"Error processing {config_file}: {e}")
                    continue
        
        except Exception as e:
            log.error(f"Error loading server configs: {e}")
        
        log.info(f"Loaded {len(servers_with_broadcast)} servers with broadcast enabled")
        return servers_with_broadcast
    
    def get_broadcast_targets(self) -> List[Dict]:
        # Get list of broadcast targets (guild_id and channel_id)
        servers = self.load_server_configs()
        targets = [
            {
                "guild_id": guild_id,
                "channel_id": data["channel_id"]
            }
            for guild_id, data in servers
        ]
        
        log.info(f"Found {len(targets)} servers with broadcast channels configured")
        return targets
    
    def load_message_from_file(self, filename: str) -> str:
        # Load broadcast message from announcements directory
        # Supports both direct filename or path
        
        # Construct path to announcements directory
        # Path: .../Discord-Bot/tools/broadcast-system/announcements/
        current_dir = Path(__file__).parent
        announcements_dir = current_dir / "announcements"
        
        # Try direct path first (if filename contains path)
        filepath = Path(filename)
        if filepath.is_absolute() and filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if not content:
                    log.error(f"File is empty: {filepath}")
                    raise ValueError("File is empty")
                
                log.info(f"Loaded message from {filepath} ({len(content)} chars)")
                return content
            
            except FileNotFoundError:
                log.error(f"File not found: {filepath}")
                raise
            except Exception as e:
                log.error(f"Failed to load message from file: {e}")
                raise
        
        # Otherwise, search in announcements directory
        filepath = announcements_dir / filename
        
        if not announcements_dir.exists():
            error_msg = f"Announcements directory not found: {announcements_dir}"
            log.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not filepath.exists():
            available_files = list(announcements_dir.glob("*"))
            error_msg = f"File not found: {filepath}\n"
            
            if available_files:
                error_msg += f"Available files in {announcements_dir}:\n"
                for file in available_files:
                    error_msg += f"  • {file.name}\n"
            else:
                error_msg += f"No files found in {announcements_dir}"
            
            log.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                error_msg = f"File is empty: {filepath}"
                log.error(error_msg)
                raise ValueError(error_msg)
            
            log.info(f"Loaded message from {filepath} ({len(content)} chars)")
            return content
        
        except ValueError as e:
            log.error(f"Invalid file content: {e}")
            raise
        except Exception as e:
            log.error(f"Failed to load message from file {filepath}: {e}")
            raise
    
    def validate_config_structure(self) -> bool:
        # Validate the structure of server configuration files
        try:
            if not self.servers_dir.exists():
                log.error(f"Servers directory does not exist: {self.servers_dir}")
                return False
            
            if not self.servers_dir.is_dir():
                log.error(f"Path is not a directory: {self.servers_dir}")
                return False
            
            json_files = list(self.servers_dir.glob("*.json"))
            log.info(f"Found {len(json_files)} server config files")
            
            return True
        
        except Exception as e:
            log.error(f"Error validating config structure: {e}")
            return False


# Quick test
if __name__ == "__main__":
    try:
        loader = BroadcastLoader()
        
        print("\n✅ Loader initialized successfully")
        
        # Validate structure
        if loader.validate_config_structure():
            print("✅ Config structure validated")
        else:
            print("❌ Config structure validation failed")
        
        # Get targets
        targets = loader.get_broadcast_targets()
        print(f"✅ Found {len(targets)} broadcast targets")
        
        for i, target in enumerate(targets[:5], 1):
            print(f"   {i}. Guild {target['guild_id']} → Channel {target['channel_id']}")
        
        if len(targets) > 5:
            print(f"   ... and {len(targets) - 5} more")
    
    except Exception as e:
        print(f"❌ Error: {e}")
