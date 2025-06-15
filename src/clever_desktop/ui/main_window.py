"""
Main Window

Primary application window with modern UI design, menu system,
and central widget management for all application features.
"""

import logging
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QLabel, QProgressBar,
    QStackedWidget, QFrame, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont, QFontMetrics

if TYPE_CHECKING:
    from ..core.app import CleverDesktopApp
    from ..core.settings import AppSettings
    from ..api.client import CleverCloudClient

from .sidebar import Sidebar
from .dashboard import Dashboard
from .applications_panel import ApplicationsPanel
from .addons_panel import AddonsPanel
from .network_groups_panel import NetworkGroupsPanel
from .logs_panel import LogsPanel
from .settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    closing = Signal()
    
    def __init__(self, app: 'CleverDesktopApp', settings: 'AppSettings', api_client: 'CleverCloudClient'):
        super().__init__()
        
        self.app = app
        self.settings = settings
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # UI Components
        self.sidebar: Optional[Sidebar] = None
        self.central_stack: Optional[QStackedWidget] = None
        self.status_label: Optional[QLabel] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        # Panels
        self.dashboard: Optional[Dashboard] = None
        self.applications_panel: Optional[ApplicationsPanel] = None
        self.addons_panel: Optional[AddonsPanel] = None
        self.network_groups_panel: Optional[NetworkGroupsPanel] = None
        self.logs_panel: Optional[LogsPanel] = None
        self.settings_panel: Optional[SettingsPanel] = None
        
        # Status
        self.current_organization = ""
        self.connection_status = "Disconnected"
        
        self._setup_ui()
        self._setup_connections()
        self._setup_shortcuts()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        self.setWindowTitle("Clever Cloud Desktop Manager")
        self.setMinimumSize(1000, 700)
        
        # Set window icon (will be updated with actual logo)
        # self.setWindowIcon(QIcon(":/icons/clever-cloud-logo.png"))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for sidebar and main content
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Setup sidebar
        self._setup_sidebar()
        splitter.addWidget(self.sidebar)
        
        # Setup main content area
        self._setup_main_content()
        splitter.addWidget(self.central_stack)
        
        # Set splitter proportions (sidebar: 250px, main content: remaining)
        splitter.setSizes([250, 950])
        splitter.setCollapsible(0, True)  # Sidebar can be collapsed
        splitter.setCollapsible(1, False)  # Main content cannot be collapsed
        
        # Setup menu bar
        self._setup_menu_bar()
        
        # Setup status bar
        self._setup_status_bar()
        
        # Setup toolbar
        self._setup_toolbar()
        
        # Apply initial theme
        self._apply_theme()
    
    def _setup_sidebar(self) -> None:
        """Setup sidebar navigation."""
        self.sidebar = Sidebar(self)
        self.sidebar.page_changed.connect(self._on_page_changed)
    
    def _setup_main_content(self) -> None:
        """Setup main content area."""
        self.central_stack = QStackedWidget()
        
        # Create panels
        self._create_panels()
        
        # Add panels to stack
        self.central_stack.addWidget(self.dashboard)
        self.central_stack.addWidget(self.applications_panel)
        self.central_stack.addWidget(self.addons_panel)
        self.central_stack.addWidget(self.network_groups_panel)
        self.central_stack.addWidget(self.logs_panel)
        self.central_stack.addWidget(self.settings_panel)
        
        # Show dashboard by default
        self.central_stack.setCurrentWidget(self.dashboard)
    
    def _create_panels(self) -> None:
        """Create all application panels."""
        self.dashboard = Dashboard(self, self.api_client)
        self.applications_panel = ApplicationsPanel(self, self.api_client)
        self.addons_panel = AddonsPanel(self, self.api_client)
        self.network_groups_panel = NetworkGroupsPanel(self, self.api_client)
        self.logs_panel = LogsPanel(self, self.api_client)
        self.settings_panel = SettingsPanel(self, self.settings)
    
    def _setup_menu_bar(self) -> None:
        """Setup application menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # Organization submenu
        org_menu = file_menu.addMenu("Organization")
        org_menu.addAction("Switch Organization...", self._switch_organization)
        org_menu.addSeparator()
        org_menu.addAction("Refresh Organizations", self._refresh_organizations)
        
        file_menu.addSeparator()
        file_menu.addAction("Preferences...", self._show_preferences, "Ctrl+,")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.app.quit, "Ctrl+Q")
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("Refresh", self._refresh_current_page, "F5")
        edit_menu.addAction("Refresh All", self.refresh_data, "Ctrl+F5")
        edit_menu.addSeparator()
        edit_menu.addAction("Clear Cache", self._clear_cache)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Dashboard", lambda: self._show_page("dashboard"), "Ctrl+1")
        view_menu.addAction("Applications", lambda: self._show_page("applications"), "Ctrl+2")
        view_menu.addAction("Add-ons", lambda: self._show_page("addons"), "Ctrl+3")
        view_menu.addAction("Network Groups", lambda: self._show_page("network_groups"), "Ctrl+4")
        view_menu.addAction("Logs", lambda: self._show_page("logs"), "Ctrl+5")
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        theme_menu.addAction("Light", lambda: self.app.change_theme("light"))
        theme_menu.addAction("Dark", lambda: self.app.change_theme("dark"))
        theme_menu.addAction("Auto", lambda: self.app.change_theme("auto"))
        
        view_menu.addSeparator()
        view_menu.addAction("Toggle Sidebar", self._toggle_sidebar, "Ctrl+B")
        view_menu.addAction("Toggle Status Bar", self._toggle_status_bar)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction("Deploy Application...", self._deploy_application, "Ctrl+D")
        tools_menu.addAction("Create Add-on...", self._create_addon)
        tools_menu.addAction("Create Network Group...", self._create_network_group)
        tools_menu.addSeparator()
        tools_menu.addAction("Export Configuration...", self._export_config)
        tools_menu.addAction("Import Configuration...", self._import_config)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Documentation", self._open_documentation, "F1")
        help_menu.addAction("Keyboard Shortcuts", self._show_shortcuts, "Ctrl+?")
        help_menu.addSeparator()
        help_menu.addAction("Check for Updates...", self._check_updates)
        help_menu.addAction("Report Issue...", self._report_issue)
        help_menu.addSeparator()
        help_menu.addAction("About Clever Desktop", self._show_about)
    
    def _setup_status_bar(self) -> None:
        """Setup status bar."""
        status_bar = self.statusBar()
        
        # Connection status
        self.status_label = QLabel("Disconnected")
        status_bar.addWidget(self.status_label)
        
        # Spacer
        status_bar.addWidget(QLabel(), 1)  # Stretch
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        status_bar.addWidget(self.progress_bar)
        
        # Organization info
        self.org_label = QLabel("No organization")
        status_bar.addPermanentWidget(self.org_label)
        
        # User info
        self.user_label = QLabel("Not logged in")
        status_bar.addPermanentWidget(self.user_label)
    
    def _setup_toolbar(self) -> None:
        """Setup main toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Quick actions
        toolbar.addAction(QIcon(), "Refresh", self.refresh_data)
        toolbar.addSeparator()
        toolbar.addAction(QIcon(), "New Application", self._create_application)
        toolbar.addAction(QIcon(), "New Add-on", self._create_addon)
        toolbar.addSeparator()
        toolbar.addAction(QIcon(), "Settings", self._show_preferences)
    
    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Connect panel signals if needed
        pass
    
    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Additional shortcuts not covered by menu
        pass
    
    def _apply_theme(self) -> None:
        """Apply current theme to the window."""
        theme = self.settings.get_theme()
        
        # Apply custom styling based on theme
        if theme == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self) -> None:
        """Apply dark theme specific styling."""
        # Custom dark theme styling can be added here
        pass
    
    def _apply_light_theme(self) -> None:
        """Apply light theme specific styling."""
        # Custom light theme styling can be added here
        pass
    
    def center_on_screen(self) -> None:
        """Center window on screen."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        
        self.move(x, y)
    
    # Event handlers
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.closing.emit()
        event.ignore()  # Let the app handle closing
    
    def _on_page_changed(self, page_name: str) -> None:
        """Handle sidebar page change."""
        self._show_page(page_name)
    
    def _show_page(self, page_name: str) -> None:
        """Show specific page."""
        page_map = {
            "dashboard": self.dashboard,
            "applications": self.applications_panel,
            "addons": self.addons_panel,
            "network_groups": self.network_groups_panel,
            "logs": self.logs_panel,
            "settings": self.settings_panel,
        }
        
        if page_name in page_map:
            self.central_stack.setCurrentWidget(page_map[page_name])
            self.sidebar.set_active_page(page_name)
            self.logger.debug(f"Switched to page: {page_name}")
    
    # Public methods
    def refresh_data(self) -> None:
        """Refresh all data."""
        self.logger.info("Refreshing all data")
        
        # Show progress
        self.show_progress("Refreshing data...")
        
        try:
            # Refresh current panel
            current_widget = self.central_stack.currentWidget()
            if hasattr(current_widget, 'refresh'):
                current_widget.refresh()
                
        except Exception as e:
            self.logger.error(f"Failed to refresh data: {e}")
            self.show_status_message(f"Refresh failed: {e}", 5000)
        finally:
            self.hide_progress()
    
    def show_progress(self, message: str = "", maximum: int = 0) -> None:
        """Show progress bar with message."""
        if message:
            self.show_status_message(message)
        
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
    
    def update_progress(self, value: int, message: str = "") -> None:
        """Update progress bar."""
        self.progress_bar.setValue(value)
        if message:
            self.show_status_message(message)
    
    def hide_progress(self) -> None:
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
        self.show_status_message("Ready")
    
    def show_status_message(self, message: str, timeout: int = 0) -> None:
        """Show status message."""
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.status_label.setText(self.connection_status))
    
    # Signal handlers from app
    def on_authentication_changed(self, authenticated: bool) -> None:
        """Handle authentication state change."""
        if authenticated:
            self.connection_status = "Connected"
            self.user_label.setText("Logged in")  # Will be updated with actual user info
        else:
            self.connection_status = "Disconnected"
            self.user_label.setText("Not logged in")
        
        self.status_label.setText(self.connection_status)
    
    def on_organization_changed(self, org_id: str) -> None:
        """Handle organization change."""
        self.current_organization = org_id
        if org_id:
            self.org_label.setText(f"Org: {org_id}")  # Will be updated with actual org name
        else:
            self.org_label.setText("No organization")
    
    def on_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self._apply_theme()
    
    # Menu action handlers
    def _switch_organization(self) -> None:
        """Switch organization."""
        # TODO: Implement organization switcher dialog
        self.logger.info("Switch organization requested")
    
    def _refresh_organizations(self) -> None:
        """Refresh organization list."""
        self.logger.info("Refresh organizations requested")
    
    def _show_preferences(self) -> None:
        """Show preferences/settings."""
        self._show_page("settings")
    
    def _refresh_current_page(self) -> None:
        """Refresh current page."""
        current_widget = self.central_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    def _clear_cache(self) -> None:
        """Clear application cache."""
        self.logger.info("Clear cache requested")
        # TODO: Implement cache clearing
    
    def _toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.sidebar.setVisible(not self.sidebar.isVisible())
    
    def _toggle_status_bar(self) -> None:
        """Toggle status bar visibility."""
        status_bar = self.statusBar()
        status_bar.setVisible(not status_bar.isVisible())
    
    def _deploy_application(self) -> None:
        """Deploy application."""
        self.logger.info("Deploy application requested")
        # TODO: Implement deployment dialog
    
    def _create_application(self) -> None:
        """Create new application."""
        self.logger.info("Create application requested")
        # TODO: Implement application creation wizard
    
    def _create_addon(self) -> None:
        """Create new add-on."""
        self.logger.info("Create add-on requested")
        # TODO: Implement add-on creation wizard
    
    def _create_network_group(self) -> None:
        """Create new network group."""
        self.logger.info("Create network group requested")
        # TODO: Implement network group creation wizard
    
    def _export_config(self) -> None:
        """Export configuration."""
        self.logger.info("Export configuration requested")
        # TODO: Implement configuration export
    
    def _import_config(self) -> None:
        """Import configuration."""
        self.logger.info("Import configuration requested")
        # TODO: Implement configuration import
    
    def _open_documentation(self) -> None:
        """Open documentation."""
        import webbrowser
        webbrowser.open("https://www.clever-cloud.com/doc/")
    
    def _show_shortcuts(self) -> None:
        """Show keyboard shortcuts."""
        self.logger.info("Show shortcuts requested")
        # TODO: Implement shortcuts dialog
    
    def _check_updates(self) -> None:
        """Check for updates."""
        self.logger.info("Check updates requested")
        # TODO: Implement update checker
    
    def _report_issue(self) -> None:
        """Report issue."""
        import webbrowser
        webbrowser.open("https://github.com/CleverCloud/clever-tools/issues")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        from PySide6.QtWidgets import QMessageBox
        
        about_text = """
        <h3>Clever Cloud Desktop Manager</h3>
        <p>Version 1.0.0</p>
        <p>A modern desktop application for managing Clever Cloud resources.</p>
        <p>Built with PySide6 and Python.</p>
        <p><a href="https://www.clever-cloud.com">www.clever-cloud.com</a></p>
        """
        
        QMessageBox.about(self, "About Clever Desktop", about_text) 