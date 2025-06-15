"""
Application Settings Management

Handles all application configuration using QSettings for cross-platform
persistence and standardized settings storage.
"""

from typing import Any, Optional, Dict, List
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, QPoint
from PySide6.QtWidgets import QWidget

from ..models.config import ThemeMode, LogLevel


class AppSettings:
    """Application settings manager using QSettings."""
    
    def __init__(self):
        self.settings = QSettings()
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default settings if not already set."""
        if not self.settings.contains("app/first_run"):
            self._set_default_values()
    
    def _set_default_values(self) -> None:
        """Set default configuration values."""
        # Application
        self.settings.setValue("app/first_run", False)
        self.settings.setValue("app/theme", "auto")
        self.settings.setValue("app/language", "en")
        self.settings.setValue("app/log_level", "INFO")
        
        # Window
        self.settings.setValue("window/width", 1200)
        self.settings.setValue("window/height", 800)
        self.settings.setValue("window/maximized", False)
        self.settings.setValue("window/restore_geometry", True)
        
        # API
        self.settings.setValue("api/timeout", 30)
        self.settings.setValue("api/retry_count", 3)
        self.settings.setValue("api/cache_enabled", True)
        self.settings.setValue("api/cache_duration", 300)  # 5 minutes
        
        # Authentication
        self.settings.setValue("auth/remember_session", True)
        self.settings.setValue("auth/auto_refresh", True)
        
        # UI Preferences
        self.settings.setValue("ui/show_tooltips", True)
        self.settings.setValue("ui/animation_enabled", True)
        self.settings.setValue("ui/confirm_destructive", True)
        self.settings.setValue("ui/auto_refresh_interval", 30)  # seconds
        
        # Logging
        self.settings.setValue("logging/file_enabled", True)
        self.settings.setValue("logging/console_enabled", True)
        self.settings.setValue("logging/max_files", 10)
        self.settings.setValue("logging/max_size_mb", 10)
        
        # Network Groups
        self.settings.setValue("ng/auto_layout", True)
        self.settings.setValue("ng/show_connection_details", True)
        self.settings.setValue("ng/animation_speed", "normal")
        
        self.settings.sync()
    
    # Theme Management
    def get_theme(self) -> str:
        """Get current theme setting."""
        return self.settings.value("app/theme", "auto")
    
    def set_theme(self, theme: str) -> None:
        """Set theme preference."""
        self.settings.setValue("app/theme", theme)
        self.settings.sync()
    
    # Window Management
    def save_window_geometry(self, widget: QWidget) -> None:
        """Save window geometry and state."""
        self.settings.setValue("window/geometry", widget.saveGeometry())
        self.settings.setValue("window/state", widget.saveState() if hasattr(widget, 'saveState') else None)
        self.settings.sync()
    
    def restore_window_geometry(self, widget: QWidget) -> bool:
        """Restore window geometry and state."""
        if not self.settings.value("window/restore_geometry", True):
            return False
        
        geometry = self.settings.value("window/geometry")
        state = self.settings.value("window/state")
        
        if geometry:
            widget.restoreGeometry(geometry)
        
        if state and hasattr(widget, 'restoreState'):
            widget.restoreState(state)
        
        return bool(geometry)
    
    def get_window_size(self) -> QSize:
        """Get default window size."""
        width = self.settings.value("window/width", 1200)
        height = self.settings.value("window/height", 800)
        return QSize(width, height)
    
    def is_maximized(self) -> bool:
        """Check if window should start maximized."""
        return self.settings.value("window/maximized", False)
    
    # API Settings
    def get_api_timeout(self) -> int:
        """Get API request timeout in seconds."""
        return self.settings.value("api/timeout", 30)
    
    def set_api_timeout(self, timeout: int) -> None:
        """Set API request timeout."""
        self.settings.setValue("api/timeout", timeout)
        self.settings.sync()
    
    def get_retry_count(self) -> int:
        """Get API retry count."""
        return self.settings.value("api/retry_count", 3)
    
    def is_cache_enabled(self) -> bool:
        """Check if API caching is enabled."""
        return self.settings.value("api/cache_enabled", True)
    
    def get_cache_duration(self) -> int:
        """Get cache duration in seconds."""
        return self.settings.value("api/cache_duration", 300)
    
    # Authentication Settings
    def should_remember_session(self) -> bool:
        """Check if session should be remembered."""
        return self.settings.value("auth/remember_session", True)
    
    def set_remember_session(self, remember: bool) -> None:
        """Set session remember preference."""
        self.settings.setValue("auth/remember_session", remember)
        self.settings.sync()
    
    def should_auto_refresh(self) -> bool:
        """Check if tokens should auto-refresh."""
        return self.settings.value("auth/auto_refresh", True)
    
    # UI Preferences
    def show_tooltips(self) -> bool:
        """Check if tooltips should be shown."""
        return self.settings.value("ui/show_tooltips", True)
    
    def is_animation_enabled(self) -> bool:
        """Check if animations are enabled."""
        return self.settings.value("ui/animation_enabled", True)
    
    def confirm_destructive_actions(self) -> bool:
        """Check if destructive actions need confirmation."""
        return self.settings.value("ui/confirm_destructive", True)
    
    def get_auto_refresh_interval(self) -> int:
        """Get auto-refresh interval in seconds."""
        return self.settings.value("ui/auto_refresh_interval", 30)
    
    def set_auto_refresh_interval(self, interval: int) -> None:
        """Set auto-refresh interval."""
        self.settings.setValue("ui/auto_refresh_interval", interval)
        self.settings.sync()
    
    # Logging Settings
    def get_log_level(self) -> str:
        """Get logging level."""
        return self.settings.value("app/log_level", "INFO")
    
    def set_log_level(self, level: str) -> None:
        """Set logging level."""
        self.settings.setValue("app/log_level", level)
        self.settings.sync()
    
    def is_file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self.settings.value("logging/file_enabled", True)
    
    def is_console_logging_enabled(self) -> bool:
        """Check if console logging is enabled."""
        return self.settings.value("logging/console_enabled", True)
    
    def get_max_log_files(self) -> int:
        """Get maximum number of log files to keep."""
        return self.settings.value("logging/max_files", 10)
    
    def get_max_log_size_mb(self) -> int:
        """Get maximum log file size in MB."""
        return self.settings.value("logging/max_size_mb", 10)
    
    # Network Groups Settings
    def use_auto_layout(self) -> bool:
        """Check if auto-layout is enabled for network diagrams."""
        return self.settings.value("ng/auto_layout", True)
    
    def show_connection_details(self) -> bool:
        """Check if connection details should be shown."""
        return self.settings.value("ng/show_connection_details", True)
    
    def get_animation_speed(self) -> str:
        """Get animation speed preference."""
        return self.settings.value("ng/animation_speed", "normal")
    
    # Recent Items
    def add_recent_organization(self, org_id: str, org_name: str) -> None:
        """Add organization to recent items."""
        recent = self.get_recent_organizations()
        # Remove if already exists
        recent = [item for item in recent if item["id"] != org_id]
        # Add to front
        recent.insert(0, {"id": org_id, "name": org_name})
        # Keep only last 10
        recent = recent[:10]
        
        self.settings.setValue("recent/organizations", recent)
        self.settings.sync()
    
    def get_recent_organizations(self) -> List[Dict[str, str]]:
        """Get recent organizations."""
        return self.settings.value("recent/organizations", [])
    
    def add_recent_application(self, app_id: str, app_name: str) -> None:
        """Add application to recent items."""
        recent = self.get_recent_applications()
        # Remove if already exists
        recent = [item for item in recent if item["id"] != app_id]
        # Add to front
        recent.insert(0, {"id": app_id, "name": app_name})
        # Keep only last 20
        recent = recent[:20]
        
        self.settings.setValue("recent/applications", recent)
        self.settings.sync()
    
    def get_recent_applications(self) -> List[Dict[str, str]]:
        """Get recent applications."""
        return self.settings.value("recent/applications", [])
    
    # Generic settings
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.value(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.settings.setValue(key, value)
        self.settings.sync()
    
    def remove_value(self, key: str) -> None:
        """Remove a setting."""
        self.settings.remove(key)
        self.settings.sync()
    
    def clear_all(self) -> None:
        """Clear all settings."""
        self.settings.clear()
        self.settings.sync()
        self._set_default_values()
    
    def export_settings(self, file_path: Path) -> bool:
        """Export settings to file."""
        try:
            settings_dict = {}
            for key in self.settings.allKeys():
                settings_dict[key] = self.settings.value(key)
            
            import json
            with open(file_path, 'w') as f:
                json.dump(settings_dict, f, indent=2, default=str)
            
            return True
        except Exception:
            return False
    
    def import_settings(self, file_path: Path) -> bool:
        """Import settings from file."""
        try:
            import json
            with open(file_path, 'r') as f:
                settings_dict = json.load(f)
            
            for key, value in settings_dict.items():
                self.settings.setValue(key, value)
            
            self.settings.sync()
            return True
        except Exception:
            return False 