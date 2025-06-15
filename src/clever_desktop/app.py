"""
Main Application

Core application class that manages the overall application state,
authentication, settings, and coordinates between different components.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtGui import QIcon, QAction

from .config import get_app_dirs
from .settings import Settings
from .models.config import ThemeMode
from .api.client import CleverCloudClient
from .widgets.main_window import MainWindow
from .widgets.login_dialog import LoginDialog
from .widgets.splash_screen import SplashScreen
from .resources import get_app_icon, get_tray_icon


class ApplicationManager(QObject):
    """Main application manager that coordinates all components."""
    
    # Signals
    authentication_changed = Signal(bool)  # authenticated
    user_changed = Signal(dict)            # user_info
    organization_changed = Signal(str)      # org_id
    organizations_loaded = Signal(list)     # organizations list
    theme_changed = Signal(str)            # theme_name
    connection_status_changed = Signal(bool, str)  # connected, message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Get application directories
        self.app_dirs = get_app_dirs()
        
        # Initialize settings
        self.settings = Settings()
        
        # Initialize API client
        self.api_client = CleverCloudClient(
            settings=self.settings,
            cache_dir=self.app_dirs.user_cache_dir
        )
        
        # Application state
        self.is_authenticated = False
        self.current_user: Optional[Dict[str, Any]] = None
        self.current_organization: Optional[str] = None
        self.organizations: list = []
        
        # UI components
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.system_tray: Optional[QSystemTrayIcon] = None
        
        # Auto-refresh timer for data
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh_data)
        
        # Connect API client signals
        self.api_client.auth.authentication_success.connect(self._on_authentication_success)
        self.api_client.auth.authentication_failed.connect(self._on_authentication_failed)
        self.api_client.auth.logout_completed.connect(self._on_logout_completed)
        self.api_client.auth.token_refreshed.connect(self._on_token_refreshed)
        
        self.logger.info("Application manager initialized")
    
    async def initialize(self) -> bool:
        """Initialize the application and check for existing authentication."""
        try:
            self.logger.info("Initializing application...")
            
            # Show splash screen
            self.splash_screen = SplashScreen()
            self.splash_screen.show()
            self.splash_screen.update_progress(20, "Checking authentication...")
            
            # Process events to show splash
            QApplication.processEvents()
            
            # Check for stored authentication
            self.splash_screen.update_progress(40, "Loading saved credentials...")
            has_auth = await self.api_client.authenticate_with_stored_credentials()
            
            if has_auth:
                self.logger.info("Authenticated with stored credentials")
                self.splash_screen.update_progress(60, "Loading user data...")
                await self._load_user_data()
                self.splash_screen.update_progress(80, "Initializing interface...")
                self._setup_main_window()
                self.splash_screen.update_progress(100, "Ready!")
                
                # Close splash and show main window
                QTimer.singleShot(500, self._show_main_window)
                return True
            else:
                self.logger.info("No stored authentication found")
                self.splash_screen.update_progress(100, "Starting authentication...")
                QTimer.singleShot(1000, self._show_login)
                return False
                
        except Exception as e:
            self.logger.error(f"Application initialization failed: {e}")
            self._show_error("Initialization Error", f"Failed to initialize application: {e}")
            return False
    
    def _setup_main_window(self):
        """Setup the main application window."""
        self.main_window = MainWindow(self.api_client, self)
        
        # Connect main window signals
        self.main_window.logout_requested.connect(self._logout)
        
        # Connect ApplicationManager signals to main window
        self.user_changed.connect(self.main_window.set_user_info)
        self.organizations_loaded.connect(self.main_window.set_organizations)
        self.organization_changed.connect(self.main_window.set_current_organization)
        
        # Apply current theme
        self._apply_theme()
        
        # Setup system tray
        self._setup_system_tray()
        
        # Start auto-refresh timer
        if self.settings.ui.auto_refresh_interval > 0:
            self.refresh_timer.start(self.settings.ui.auto_refresh_interval * 1000)
    
    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.system_tray = QSystemTrayIcon()
        
        # Set icon
        icon = get_tray_icon()
        self.system_tray.setIcon(icon)
        self.system_tray.setToolTip("Clever Cloud Desktop")
        
        # Create context menu
        menu = QMenu()
        
        show_action = QAction("Show Clever Desktop", self)
        show_action.triggered.connect(self._show_main_window)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        refresh_action = QAction("Refresh Data", self)
        refresh_action.triggered.connect(self._refresh_data)
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._logout)
        menu.addAction(logout_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        self.system_tray.setContextMenu(menu)
        self.system_tray.activated.connect(self._on_system_tray_activated)
        self.system_tray.show()
    
    def _show_login(self):
        """Show login dialog."""
        self.logger.info("Showing login dialog")
        
        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen = None
        
        login_dialog = LoginDialog(self.api_client)
        login_dialog.authentication_success.connect(self._on_login_success)
        
        if login_dialog.exec() == LoginDialog.DialogCode.Rejected:
            # User cancelled login
            QApplication.quit()
    
    def _on_login_success(self, user_info: Dict[str, Any]):
        """Handle successful login."""
        self.logger.info("Login successful, setting up main window")
        
        # Setup and show main window first
        self._setup_main_window()
        self._show_main_window()
        
        # Load user data using QTimer to avoid blocking
        QTimer.singleShot(100, self._load_user_data_sync)
    
    def _load_user_data_sync(self):
        """Load user data using a separate thread."""
        self.logger.info("Starting to load user data...")
        
        # Use QThread to load data without blocking UI
        from PySide6.QtCore import QThread, QObject, Signal
        
        class DataLoader(QObject):
            data_loaded = Signal(dict, list)  # user_info, organizations
            error_occurred = Signal(str)
            
            def __init__(self, api_client, logger):
                super().__init__()
                self.api_client = api_client
                self.logger = logger
            
            def load_data(self):
                """Load data in thread."""
                import asyncio
                
                async def fetch_data():
                    try:
                        self.logger.info("Loading user info from API...")
                        user_info = await self.api_client.get_user_info()
                        self.logger.info(f"Loaded user info: {user_info.get('name', 'Unknown')}")
                        
                        self.logger.info("Loading organizations from API...")
                        organizations = await self.api_client.get_organizations()
                        self.logger.info(f"Loaded {len(organizations)} organizations: {[org.get('name', 'Unknown') for org in organizations]}")
                        
                        return user_info, organizations
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load data: {e}")
                        raise e
                
                try:
                    # Run async code in this thread
                    user_info, organizations = asyncio.run(fetch_data())
                    self.data_loaded.emit(user_info, organizations)
                except Exception as e:
                    self.error_occurred.emit(str(e))
        
        # Create thread and loader
        self.data_thread = QThread()
        self.data_loader = DataLoader(self.api_client, self.logger)
        self.data_loader.moveToThread(self.data_thread)
        
        # Connect signals
        self.data_loader.data_loaded.connect(self._on_data_loaded)
        self.data_loader.error_occurred.connect(self._on_data_error)
        self.data_thread.started.connect(self.data_loader.load_data)
        
        # Start thread
        self.data_thread.start()
        self.logger.info("Started data loading thread")
    
    def _on_data_loaded(self, user_info: dict, organizations: list):
        """Handle successful data loading."""
        self.logger.info("Data loading completed successfully")
        
        # Store data
        self.current_user = user_info
        self.organizations = organizations
        self.is_authenticated = True
        
        # Set default organization if not set
        if not self.current_organization and organizations:
            self.current_organization = organizations[0].get('id')
            self.logger.info(f"Set default organization: {self.current_organization}")
        
        # Emit signals
        self.authentication_changed.emit(True)
        self.user_changed.emit(user_info)
        self.logger.info("Emitted user_changed signal")
        
        if self.current_organization:
            self.organization_changed.emit(self.current_organization)
            self.logger.info(f"Emitted organization_changed signal: {self.current_organization}")
        
        self.organizations_loaded.emit(organizations)
        self.logger.info(f"Emitted organizations_loaded signal with {len(organizations)} organizations")
        
        # Cleanup thread
        self.data_thread.quit()
        self.data_thread.wait()
        
        self.logger.info(f"User data loaded for: {user_info.get('name', 'Unknown')}")
    
    def _on_data_error(self, error: str):
        """Handle data loading error."""
        self.logger.error(f"Data loading failed: {error}")
        self.connection_status_changed.emit(False, f"Failed to load user data: {error}")
        
        # Cleanup thread
        self.data_thread.quit()
        self.data_thread.wait()
    
    def _show_main_window(self):
        """Show the main application window."""
        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen = None
        
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    async def _load_user_data(self):
        """Load user data and organizations."""
        try:
            # Get user info
            user_info = await self.api_client.get_user_info()
            self.current_user = user_info
            self.is_authenticated = True
            self.logger.info(f"Loaded user info: {user_info.get('name', 'Unknown')}")
            
            # Get organizations
            organizations = await self.api_client.get_organizations()
            self.organizations = organizations
            self.logger.info(f"Loaded {len(organizations)} organizations: {[org.get('name', 'Unknown') for org in organizations]}")
            
            # Set default organization if not set
            if not self.current_organization and organizations:
                self.current_organization = organizations[0].get('id')
                self.logger.info(f"Set default organization: {self.current_organization}")
            
            # Emit signals from main thread using QTimer
            def emit_signals():
                self.authentication_changed.emit(True)
                self.user_changed.emit(user_info)
                self.logger.info("Emitted user_changed signal")
                
                if self.current_organization:
                    self.organization_changed.emit(self.current_organization)
                    self.logger.info(f"Emitted organization_changed signal: {self.current_organization}")
                
                self.organizations_loaded.emit(organizations)
                self.logger.info(f"Emitted organizations_loaded signal with {len(organizations)} organizations")
            
            # Schedule signal emission in main thread
            QTimer.singleShot(0, emit_signals)
            
            self.logger.info(f"User data loaded for: {user_info.get('name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to load user data: {e}")
            # Emit error signal from main thread
            QTimer.singleShot(0, lambda: self.connection_status_changed.emit(False, f"Failed to load user data: {e}"))
    
    def _on_authentication_success(self, user_info: Dict[str, Any]):
        """Handle authentication success signal."""
        self.current_user = user_info
        self.is_authenticated = True
        self.authentication_changed.emit(True)
        self.user_changed.emit(user_info)
        
        # Load additional data
        self._run_async_task(self._load_user_data())
    
    def _on_authentication_failed(self, error: str):
        """Handle authentication failure signal."""
        self.logger.error(f"Authentication failed: {error}")
        self.is_authenticated = False
        self.current_user = None
        self.authentication_changed.emit(False)
        self.connection_status_changed.emit(False, f"Authentication failed: {error}")
    
    def _on_logout_completed(self):
        """Handle logout completion."""
        self.logger.info("Logout completed")
        self.is_authenticated = False
        self.current_user = None
        self.current_organization = None
        self.organizations = []
        
        # Stop auto-refresh
        self.refresh_timer.stop()
        
        # Emit signals
        self.authentication_changed.emit(False)
        self.connection_status_changed.emit(False, "Logged out")
        
        # Close main window and show login
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        self._show_login()
    
    def _on_token_refreshed(self):
        """Handle token refresh."""
        self.logger.info("Authentication token refreshed")
        self.connection_status_changed.emit(True, "Token refreshed")
    
    async def _logout(self):
        """Logout user."""
        self.logger.info("Logging out user")
        await self.api_client.logout()
    
    def change_organization(self, org_id: str):
        """Change current organization."""
        if org_id != self.current_organization:
            self.logger.info(f"Changing organization to: {org_id}")
            self.current_organization = org_id
            self.organization_changed.emit(org_id)
            
            # Refresh data for new organization
            self._refresh_data()
    
    def _refresh_data(self):
        """Refresh application data."""
        if self.is_authenticated:
            self.logger.info("Refreshing application data")
            self.connection_status_changed.emit(True, "Refreshing data...")
            self._run_async_task(self._load_user_data())
    
    def _auto_refresh_data(self):
        """Auto-refresh data based on timer."""
        if self.is_authenticated and self.main_window and self.main_window.isVisible():
            self._refresh_data()
    
    def _apply_theme(self):
        """Apply current theme to application."""
        theme_mode = self.settings.ui.theme_mode
        
        if theme_mode == ThemeMode.AUTO:
            # TODO: Detect system theme
            theme_name = "dark"  # Default for now
        else:
            theme_name = theme_mode.value
        
        self.theme_changed.emit(theme_name)
        
        if self.main_window:
            self.main_window.apply_theme(theme_name)
    
    def _on_system_tray_activated(self, reason):
        """Handle system tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.main_window:
                if self.main_window.isVisible():
                    self.main_window.hide()
                else:
                    self._show_main_window()
    
    def _run_async_task(self, coro):
        """Run async task using QTimer to schedule it properly."""
        def run_task():
            try:
                # Check if there's an active event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Schedule the coroutine in the existing loop
                    asyncio.create_task(coro)
                except RuntimeError:
                    # No running loop, create a new one in a thread
                    def run_in_thread():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(coro)
                        except Exception as e:
                            self.logger.error(f"Error in async task: {e}")
                        finally:
                            loop.close()
                    
                    import threading
                    thread = threading.Thread(target=run_in_thread, daemon=True)
                    thread.start()
            except Exception as e:
                self.logger.error(f"Error scheduling async task: {e}")
        
        # Use QTimer to schedule the task
        QTimer.singleShot(0, run_task)
    
    def _show_error(self, title: str, message: str):
        """Show error message to user."""
        QMessageBox.critical(None, title, message)
    
    # Public API
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        return self.current_user
    
    def get_current_organization(self) -> Optional[str]:
        """Get current organization ID."""
        return self.current_organization
    
    def get_organizations(self) -> list:
        """Get available organizations."""
        return self.organizations
    
    def is_user_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.is_authenticated
    
    async def shutdown(self):
        """Cleanup application on shutdown."""
        self.logger.info("Shutting down application")
        
        # Stop timers
        self.refresh_timer.stop()
        
        # Hide system tray
        if self.system_tray:
            self.system_tray.hide()
        
        # Close API client
        await self.api_client.close()
        
        self.logger.info("Application shutdown complete") 