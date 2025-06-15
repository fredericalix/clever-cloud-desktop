"""
Main Application Class

Core application management including main window, authentication,
and central coordination of all application components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSystemTrayIcon
from PySide6.QtCore import QTimer, QThread, Signal, QObject
from PySide6.QtGui import QIcon, QAction

from .settings import AppSettings
from .logging_config import configure_qt_logging, setup_crash_logging
from ..ui.main_window import MainWindow
from ..ui.splash_screen import SplashScreen
from ..ui.login_dialog import LoginDialog
from ..api.client import CleverCloudClient
from ..models.config import FeatureFlags


class CleverDesktopApp(QObject):
    """Main application controller."""
    
    # Signals
    authentication_changed = Signal(bool)  # True if authenticated
    organization_changed = Signal(str)  # Organization ID
    theme_changed = Signal(str)  # Theme name
    
    def __init__(self, data_dir: Path, config_dir: Path):
        super().__init__()
        
        self.data_dir = data_dir
        self.config_dir = config_dir
        self.settings = AppSettings()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.system_tray: Optional[QSystemTrayIcon] = None
        self.api_client: Optional[CleverCloudClient] = None
        
        # Application state
        self.is_authenticated = False
        self.current_organization = None
        self.shutting_down = False
        
        # Timers
        self.auto_refresh_timer = QTimer()
        self.session_check_timer = QTimer()
        
        self._setup_application()
    
    def _setup_application(self) -> None:
        """Setup application components."""
        self.logger.info("Initializing Clever Desktop application")
        
        # Configure Qt logging integration
        configure_qt_logging()
        
        # Setup crash logging
        setup_crash_logging(self.data_dir / "logs" / "crash.log")
        
        # Initialize API client
        self.api_client = CleverCloudClient(
            settings=self.settings,
            cache_dir=self.data_dir / "cache"
        )
        
        # Setup timers
        self._setup_timers()
        
        # Setup system tray if supported
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._setup_system_tray()
        
        self.logger.info("Application initialization complete")
    
    def _setup_timers(self) -> None:
        """Setup application timers."""
        # Auto-refresh timer
        refresh_interval = self.settings.get_auto_refresh_interval() * 1000  # Convert to ms
        self.auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        self.auto_refresh_timer.start(refresh_interval)
        
        # Session check timer (every minute)
        self.session_check_timer.timeout.connect(self._check_session)
        self.session_check_timer.start(60000)
    
    def _setup_system_tray(self) -> None:
        """Setup system tray icon and menu."""
        self.system_tray = QSystemTrayIcon(self)
        
        # Set icon (will be replaced with actual logo later)
        icon = QIcon(":/icons/clever-cloud-logo.png")
        self.system_tray.setIcon(icon)
        
        # Create context menu
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        
        # Show/Hide action
        show_action = QAction("Show Clever Desktop", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)
        
        hide_action = QAction("Hide to Tray", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)
        
        menu.addSeparator()
        
        # Quick actions
        refresh_action = QAction("Refresh Data", self)
        refresh_action.triggered.connect(self._refresh_all_data)
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)
        
        self.system_tray.setContextMenu(menu)
        self.system_tray.activated.connect(self._on_tray_activated)
        
        # Show tray icon
        self.system_tray.show()
        self.system_tray.showMessage(
            "Clever Desktop",
            "Application is running in the system tray",
            QSystemTrayIcon.Information,
            3000
        )
    
    def show_splash_screen(self) -> None:
        """Show splash screen during initialization."""
        if not self.splash_screen:
            self.splash_screen = SplashScreen()
        
        self.splash_screen.show()
        self.splash_screen.show_message("Loading Clever Desktop...")
        
        # Process events to update splash screen
        QApplication.processEvents()
    
    def hide_splash_screen(self) -> None:
        """Hide splash screen."""
        if self.splash_screen:
            self.splash_screen.hide()
            self.splash_screen = None
    
    def show(self) -> None:
        """Show main window."""
        if not self.main_window:
            self._create_main_window()
        
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # Hide splash screen if still showing
        self.hide_splash_screen()
    
    def hide(self) -> None:
        """Hide main window to system tray."""
        if self.main_window:
            self.main_window.hide()
            
            if self.system_tray:
                self.system_tray.showMessage(
                    "Clever Desktop",
                    "Application was minimized to the system tray",
                    QSystemTrayIcon.Information,
                    2000
                )
    
    def _create_main_window(self) -> None:
        """Create and configure main window."""
        self.logger.info("Creating main window")
        
        self.main_window = MainWindow(
            app=self,
            settings=self.settings,
            api_client=self.api_client
        )
        
        # Connect signals
        self.main_window.closing.connect(self._on_main_window_closing)
        self.authentication_changed.connect(self.main_window.on_authentication_changed)
        self.organization_changed.connect(self.main_window.on_organization_changed)
        self.theme_changed.connect(self.main_window.on_theme_changed)
        
        # Restore window geometry
        if not self.settings.restore_window_geometry(self.main_window):
            # Center on screen if no saved geometry
            self.main_window.resize(self.settings.get_window_size())
            self.main_window.center_on_screen()
        
        if self.settings.is_maximized():
            self.main_window.showMaximized()
    
    def authenticate(self) -> bool:
        """Handle user authentication."""
        self.logger.info("Starting authentication process")
        
        # Check if we have stored credentials
        if self.settings.should_remember_session() and self.api_client.has_stored_credentials():
            try:
                # Try to authenticate with stored credentials
                if self.api_client.authenticate_with_stored_credentials():
                    self.is_authenticated = True
                    self.authentication_changed.emit(True)
                    self.logger.info("Authentication successful with stored credentials")
                    return True
            except Exception as e:
                self.logger.warning(f"Failed to authenticate with stored credentials: {e}")
        
        # Show login dialog
        login_dialog = LoginDialog(self.main_window, self.api_client)
        if login_dialog.exec() == login_dialog.Accepted:
            self.is_authenticated = True
            self.authentication_changed.emit(True)
            self.logger.info("Authentication successful via login dialog")
            return True
        
        self.logger.info("Authentication cancelled or failed")
        return False
    
    def logout(self) -> None:
        """Handle user logout."""
        self.logger.info("Logging out user")
        
        if self.api_client:
            self.api_client.logout()
        
        self.is_authenticated = False
        self.current_organization = None
        
        self.authentication_changed.emit(False)
        self.organization_changed.emit("")
        
        # Show login dialog again
        self.authenticate()
    
    def quit(self) -> None:
        """Quit the application."""
        self.logger.info("Application quit requested")
        
        self.shutting_down = True
        
        # Stop timers
        self.auto_refresh_timer.stop()
        self.session_check_timer.stop()
        
        # Save window geometry
        if self.main_window:
            self.settings.save_window_geometry(self.main_window)
        
        # Clean shutdown
        if self.api_client:
            self.api_client.close()
        
        # Hide system tray
        if self.system_tray:
            self.system_tray.hide()
        
        # Quit Qt application
        QApplication.quit()
    
    def _on_main_window_closing(self) -> None:
        """Handle main window closing."""
        if self.system_tray and self.system_tray.isVisible():
            # Hide to system tray instead of quitting
            self.hide()
        else:
            # No system tray, quit application
            self.quit()
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle system tray activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.main_window and self.main_window.isVisible():
                self.hide()
            else:
                self.show()
    
    def _on_auto_refresh(self) -> None:
        """Handle auto-refresh timer."""
        if not self.is_authenticated or self.shutting_down:
            return
        
        self.logger.debug("Auto-refresh triggered")
        self._refresh_all_data()
    
    def _refresh_all_data(self) -> None:
        """Refresh all application data."""
        if not self.is_authenticated or not self.main_window:
            return
        
        try:
            self.main_window.refresh_data()
        except Exception as e:
            self.logger.error(f"Failed to refresh data: {e}")
    
    def _check_session(self) -> None:
        """Check session validity and refresh tokens if needed."""
        if not self.is_authenticated or not self.api_client:
            return
        
        try:
            if not self.api_client.is_session_valid():
                self.logger.warning("Session expired, attempting to refresh")
                
                if self.settings.should_auto_refresh():
                    if self.api_client.refresh_session():
                        self.logger.info("Session refreshed successfully")
                    else:
                        self.logger.error("Failed to refresh session, logging out")
                        self.logout()
                else:
                    self.logout()
        except Exception as e:
            self.logger.error(f"Session check failed: {e}")
            self.logout()
    
    def change_theme(self, theme: str) -> None:
        """Change application theme."""
        self.logger.info(f"Changing theme to: {theme}")
        
        # Update settings
        self.settings.set_theme(theme)
        
        # Apply theme to Qt application
        from ..main import apply_theme
        apply_theme(QApplication.instance(), theme)
        
        # Notify components
        self.theme_changed.emit(theme)
    
    def set_organization(self, org_id: str) -> None:
        """Set current organization."""
        if self.current_organization != org_id:
            self.logger.info(f"Switching to organization: {org_id}")
            self.current_organization = org_id
            self.organization_changed.emit(org_id)
    
    def show_error(self, title: str, message: str, details: str = "") -> None:
        """Show error dialog."""
        self.logger.error(f"{title}: {message}")
        
        if self.main_window:
            error_dialog = QMessageBox(self.main_window)
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle(title)
            error_dialog.setText(message)
            
            if details:
                error_dialog.setDetailedText(details)
            
            error_dialog.exec()
    
    def show_notification(self, title: str, message: str, duration: int = 5000) -> None:
        """Show system notification."""
        if self.system_tray:
            self.system_tray.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                duration
            )
    
    def handle_critical_error(self, error: Exception) -> None:
        """Handle critical application errors."""
        self.logger.critical(f"Critical error: {error}", exc_info=True)
        
        # Show error dialog
        self.show_error(
            "Critical Error",
            "A critical error occurred. The application may need to be restarted.",
            str(error)
        )
        
        # Optionally quit application
        if self.settings.get_value("crash_on_critical_error", False):
            self.quit() 