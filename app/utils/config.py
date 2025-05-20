"""
Configuration utilities for the Sporty application.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_CONFIG_FILE = os.path.expanduser("~/.sporty/config.json")
CONFIG_DIR = os.path.expanduser("~/.sporty")

def ensure_config_dir() -> None:
    """Ensure that the configuration directory exists."""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from the config file.
    
    Args:
        config_file: Path to the config file
        
    Returns:
        Dict containing the configuration
    """
    config_file = config_file or DEFAULT_CONFIG_FILE
    
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_file}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_file}")
        return {}
        
def save_config(config: Dict[str, Any], config_file: Optional[str] = None) -> None:
    """
    Save configuration to the config file.
    
    Args:
        config: Configuration to save
        config_file: Path to the config file
    """
    config_file = config_file or DEFAULT_CONFIG_FILE
    
    # Ensure the directory exists
    ensure_config_dir()
    
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save config file: {e}")
        
def get_api_key() -> Optional[str]:
    """
    Get the API key from the config file or environment variable.
    
    Returns:
        API key if available, None otherwise
    """
    # First, try environment variable
    api_key = os.environ.get("SPORTY_API_KEY")
    if api_key:
        return api_key
        
    # Then, try config file
    config = load_config()
    return config.get("api_key")
    
def set_api_key(api_key: str) -> None:
    """
    Set the API key in the config file.
    
    Args:
        api_key: API key to save
    """
    config = load_config()
    config["api_key"] = api_key
    save_config(config)