"""
Configuration Models

Data models and enums for application configuration,
providing type safety and validation for settings.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path


class ThemeMode(Enum):
    """Theme mode options."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class LogLevel(Enum):
    """Logging level options."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ApiRegion(Enum):
    """Clever Cloud regions."""
    PAR = "par"  # Paris
    MTL = "mtl"  # Montreal
    RBAIX = "rbaix"  # Roubaix
    WSW = "wsw"  # Warsaw
    SGP = "sgp"  # Singapore


class ApplicationState(Enum):
    """Application deployment states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    RESTARTING = "restarting"
    DEPLOYING = "deploying"
    UNKNOWN = "unknown"


class AddonProvider(Enum):
    """Addon provider types."""
    POSTGRESQL = "postgresql-addon"
    MYSQL = "mysql-addon"
    REDIS = "redis-addon"
    MONGODB = "mongodb-addon"
    ELASTICSEARCH = "es-addon"
    PULSAR = "pulsar-addon"
    MATERIA_KV = "materia-kv-addon"
    JENKINS = "jenkins-addon"
    KEYCLOAK = "keycloak-addon"
    METABASE = "metabase-addon"
    CELLAR = "cellar-addon"
    FS_BUCKET = "fs-bucket-addon"


@dataclass
class WindowConfig:
    """Window configuration."""
    width: int = 1200
    height: int = 800
    x: Optional[int] = None
    y: Optional[int] = None
    maximized: bool = False
    fullscreen: bool = False
    restore_geometry: bool = True


@dataclass
class ApiConfig:
    """API configuration."""
    timeout: int = 30
    retry_count: int = 3
    cache_enabled: bool = True
    cache_duration: int = 300  # seconds
    parallel_requests: int = 5
    rate_limit_enabled: bool = True


@dataclass
class AuthConfig:
    """Authentication configuration."""
    remember_session: bool = True
    auto_refresh: bool = True
    token_refresh_threshold: int = 300  # seconds before expiry
    session_timeout: int = 3600  # seconds


@dataclass
class UIConfig:
    """UI configuration."""
    theme: ThemeMode = ThemeMode.AUTO
    language: str = "en"
    show_tooltips: bool = True
    animation_enabled: bool = True
    confirm_destructive: bool = True
    auto_refresh_interval: int = 30
    startup_page: str = "dashboard"
    sidebar_width: int = 250
    show_status_bar: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    file_enabled: bool = True
    console_enabled: bool = True
    max_files: int = 10
    max_size_mb: int = 10
    format_template: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


@dataclass
class NetworkGroupsConfig:
    """Network Groups specific configuration."""
    auto_layout: bool = True
    show_connection_details: bool = True
    animation_speed: str = "normal"  # slow, normal, fast
    default_layout: str = "hierarchical"  # hierarchical, circular, grid
    show_external_peers: bool = True
    highlight_active_connections: bool = True


@dataclass
class GitConfig:
    """Git integration configuration."""
    default_branch: str = "main"
    auto_push: bool = False
    commit_message_template: str = "Deploy from Clever Desktop"
    show_git_status: bool = True
    fetch_on_startup: bool = True


@dataclass
class NotificationConfig:
    """Notification configuration."""
    desktop_notifications: bool = True
    sound_enabled: bool = False
    deployment_notifications: bool = True
    error_notifications: bool = True
    update_notifications: bool = True
    notification_duration: int = 5000  # milliseconds


@dataclass
class SecurityConfig:
    """Security configuration."""
    store_credentials: bool = True
    credential_timeout: int = 3600
    require_auth_for_actions: bool = True
    auto_lock_timeout: int = 0  # 0 = disabled
    clear_clipboard: bool = True
    clipboard_timeout: int = 30


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    cache_size_mb: int = 100
    max_concurrent_operations: int = 10
    background_sync_enabled: bool = True
    background_sync_interval: int = 300
    lazy_loading_enabled: bool = True
    image_cache_enabled: bool = True


@dataclass
class RecentItem:
    """Recent item reference."""
    id: str
    name: str
    type: str  # organization, application, addon, etc.
    last_accessed: str  # ISO timestamp
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Complete application configuration."""
    window: WindowConfig = field(default_factory=WindowConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    network_groups: NetworkGroupsConfig = field(default_factory=NetworkGroupsConfig)
    git: GitConfig = field(default_factory=GitConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Recent items
    recent_organizations: List[RecentItem] = field(default_factory=list)
    recent_applications: List[RecentItem] = field(default_factory=list)
    recent_addons: List[RecentItem] = field(default_factory=list)
    
    # Feature flags
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary."""
        # This would need proper deserialization logic
        # For now, return default config
        return cls()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate window config
        if self.window.width < 800:
            issues.append("Window width must be at least 800px")
        if self.window.height < 600:
            issues.append("Window height must be at least 600px")
        
        # Validate API config
        if self.api.timeout < 1:
            issues.append("API timeout must be at least 1 second")
        if self.api.retry_count < 0:
            issues.append("API retry count cannot be negative")
        
        # Validate auth config
        if self.auth.token_refresh_threshold < 60:
            issues.append("Token refresh threshold should be at least 60 seconds")
        
        # Validate logging config
        if self.logging.max_files < 1:
            issues.append("Must keep at least 1 log file")
        if self.logging.max_size_mb < 1:
            issues.append("Log file size must be at least 1MB")
        
        # Validate performance config
        if self.performance.cache_size_mb < 10:
            issues.append("Cache size should be at least 10MB")
        
        return issues
    
    def apply_feature_flag(self, flag: str, enabled: bool) -> None:
        """Apply a feature flag."""
        self.feature_flags[flag] = enabled
    
    def is_feature_enabled(self, flag: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled."""
        return self.feature_flags.get(flag, default)


# Predefined feature flags
class FeatureFlags:
    """Feature flag constants."""
    NETWORK_GROUPS_BETA = "network_groups_beta"
    GIT_INTEGRATION = "git_integration"
    ADVANCED_MONITORING = "advanced_monitoring"
    DARK_MODE = "dark_mode"
    NOTIFICATIONS = "notifications"
    AUTO_UPDATES = "auto_updates"
    CRASH_REPORTING = "crash_reporting"
    ANALYTICS = "analytics"
    COLLABORATION = "collaboration"
    MARKETPLACE = "marketplace"


# Default feature flags state
DEFAULT_FEATURE_FLAGS = {
    FeatureFlags.NETWORK_GROUPS_BETA: True,
    FeatureFlags.GIT_INTEGRATION: True,
    FeatureFlags.ADVANCED_MONITORING: True,
    FeatureFlags.DARK_MODE: True,
    FeatureFlags.NOTIFICATIONS: True,
    FeatureFlags.AUTO_UPDATES: True,
    FeatureFlags.CRASH_REPORTING: False,  # Privacy by default
    FeatureFlags.ANALYTICS: False,  # Privacy by default
    FeatureFlags.COLLABORATION: False,  # Not implemented yet
    FeatureFlags.MARKETPLACE: False,  # Not implemented yet
} 