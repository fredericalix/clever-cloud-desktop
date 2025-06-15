"""
Application Configuration

Configuration setup, directory management, and utility functions.
"""

import os
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QStandardPaths


class AppDirectories(NamedTuple):
    """Application directory paths."""
    user_data_dir: Path
    user_config_dir: Path
    user_cache_dir: Path
    user_log_dir: Path


def get_app_dirs() -> AppDirectories:
    """Get application directories, creating them if needed."""
    
    # Get standard directories
    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    config_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
    cache_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation))
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log directory under data
    log_dir = data_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    return AppDirectories(
        user_data_dir=data_dir,
        user_config_dir=config_dir,
        user_cache_dir=cache_dir,
        user_log_dir=log_dir
    )


# Application constants
APP_NAME = "Clever Cloud Desktop"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "Clever Cloud"
ORGANIZATION_DOMAIN = "clever-cloud.com" 