"""
Application Settings

Settings management using QSettings for persistent configuration.
"""

import logging
from typing import Any, Optional

from PySide6.QtCore import QSettings

from .models.config import UIConfig, AuthConfig, ApiConfig, ThemeMode


class Settings:
    """Application settings manager using QSettings."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._settings = QSettings()
        
        # Initialize default sections
        self.ui = UIConfig()
        self.auth = AuthConfig()
        self.api = ApiConfig()
        
        # Load settings from storage
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from QSettings."""
        try:
            # UI Settings
            self.ui.theme_mode = ThemeMode(self._settings.value("ui/theme_mode", ThemeMode.AUTO.value))
            self.ui.auto_refresh_interval = int(self._settings.value("ui/auto_refresh_interval", 30))
            self.ui.show_system_tray = bool(self._settings.value("ui/show_system_tray", True))
            self.ui.minimize_to_tray = bool(self._settings.value("ui/minimize_to_tray", True))
            self.ui.start_minimized = bool(self._settings.value("ui/start_minimized", False))
            
            # Auth Settings
            self.auth.auto_refresh = bool(self._settings.value("auth/auto_refresh", True))
            self.auth.token_refresh_threshold = int(self._settings.value("auth/token_refresh_threshold", 300))
            
            # API Settings
            self.api.timeout = int(self._settings.value("api/timeout", 30))
            self.api.retry_count = int(self._settings.value("api/retry_count", 3))
            self.api.cache_enabled = bool(self._settings.value("api/cache_enabled", True))
            
            self.logger.debug("Settings loaded from storage")
            
        except Exception as e:
            self.logger.warning(f"Error loading settings, using defaults: {e}")
            # Keep default values if loading fails
    
    def save(self):
        """Save current settings to storage."""
        try:
            # UI Settings
            self._settings.setValue("ui/theme_mode", self.ui.theme_mode.value)
            self._settings.setValue("ui/auto_refresh_interval", self.ui.auto_refresh_interval)
            self._settings.setValue("ui/show_system_tray", self.ui.show_system_tray)
            self._settings.setValue("ui/minimize_to_tray", self.ui.minimize_to_tray)
            self._settings.setValue("ui/start_minimized", self.ui.start_minimized)
            
            # Auth Settings
            self._settings.setValue("auth/auto_refresh", self.auth.auto_refresh)
            self._settings.setValue("auth/token_refresh_threshold", self.auth.token_refresh_threshold)
            
            # API Settings
            self._settings.setValue("api/timeout", self.api.timeout)
            self._settings.setValue("api/retry_count", self.api.retry_count)
            self._settings.setValue("api/cache_enabled", self.api.cache_enabled)
            
            # Force sync to disk
            self._settings.sync()
            
            self.logger.debug("Settings saved to storage")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        return self._settings.value(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value by key."""
        self._settings.setValue(key, value)
        self._settings.sync()
    
    def reset(self):
        """Reset all settings to defaults."""
        self._settings.clear()
        self.ui = UIConfig()
        self.auth = AuthConfig()
        self.api = ApiConfig()
        self.save()
        self.logger.info("Settings reset to defaults")
    
    def get_organization_preference(self) -> Optional[str]:
        """Get the user's preferred organization."""
        return self.get("user/preferred_organization")
    
    def set_organization_preference(self, org_id: str):
        """Set the user's preferred organization."""
        self.set("user/preferred_organization", org_id)
    
    def get_window_geometry(self) -> Optional[bytes]:
        """Get saved window geometry."""
        return self._settings.value("window/geometry")
    
    def set_window_geometry(self, geometry: bytes):
        """Save window geometry."""
        self._settings.setValue("window/geometry", geometry)
        self._settings.sync()
    
    def get_window_state(self) -> Optional[bytes]:
        """Get saved window state."""
        return self._settings.value("window/state")
    
    def set_window_state(self, state: bytes):
        """Save window state."""
        self._settings.setValue("window/state", state)
        self._settings.sync() 