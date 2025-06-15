"""
Main Application Window

Central window for the Clever Cloud Desktop Manager application.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

from ..api.client import CleverCloudClient
from .dashboard import MainDashboard


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    logout_requested = Signal()
    
    def __init__(self, api_client: CleverCloudClient, app_manager=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.app_manager = app_manager
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Clever Cloud Desktop Manager")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self.setup_ui()
        self.setup_status_bar()
        
        self.logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup the main window UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main dashboard
        self.dashboard = MainDashboard(self.api_client)
        self.dashboard.logout_requested.connect(self.logout_requested.emit)
        self.dashboard.organization_changed.connect(self._on_organization_changed)
        self.dashboard.refresh_requested.connect(self._on_refresh_requested)
        
        layout.addWidget(self.dashboard)
    
    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connection status
        self.connection_label = QLabel("🟢 Connected to Clever Cloud")
        self.connection_label.setStyleSheet("color: #28a745; font-weight: bold;")
        self.status_bar.addWidget(self.connection_label)
        
        # Spacer
        self.status_bar.addPermanentWidget(QLabel(""))
        
        # Version info
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #6c757d;")
        self.status_bar.addPermanentWidget(version_label)
    
    def _on_organization_changed(self, org_id: str):
        """Handle organization change."""
        self.logger.info(f"Organization change requested: {org_id}")
        self.status_bar.showMessage(f"Switching to organization: {org_id}", 3000)
        
        # Use ApplicationManager to change organization
        if self.app_manager:
            self.app_manager.change_organization(org_id)
        else:
            self.logger.warning("No ApplicationManager available for organization change")
    
    def _on_refresh_requested(self):
        """Handle refresh request."""
        self.logger.info("Refresh requested")
        self.status_bar.showMessage("Refreshing data...", 2000)
        
        # Refresh dashboard data
        if hasattr(self.dashboard, 'refresh_data'):
            self.dashboard.refresh_data()
    
    def set_user_info(self, user_info: dict):
        """Set user information from ApplicationManager."""
        self.logger.info(f"MainWindow: Received user info: {user_info.get('name', 'Unknown')}")
        if hasattr(self.dashboard, 'header'):
            self.dashboard.header.set_user_info(user_info)
            self.logger.info("MainWindow: Set user info on dashboard header")
        else:
            self.logger.warning("MainWindow: Dashboard or header not available")
    
    def set_organizations(self, organizations: list):
        """Set organizations list from ApplicationManager."""
        self.logger.info(f"MainWindow: Received {len(organizations)} organizations")
        if hasattr(self.dashboard, 'header'):
            self.dashboard.header.set_organizations(organizations)
            self.logger.info("MainWindow: Set organizations on dashboard header")
        else:
            self.logger.warning("MainWindow: Dashboard or header not available")
    
    def set_current_organization(self, org_id: str):
        """Set current organization from ApplicationManager."""
        self.logger.info(f"MainWindow: Current organization set to: {org_id}")
        # This will be handled by the dashboard's organization change handler
        pass
    
    def set_connection_status(self, connected: bool, message: str = ""):
        """Set connection status in status bar."""
        if connected:
            self.connection_label.setText("🟢 Connected to Clever Cloud")
            self.connection_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.connection_label.setText(f"🔴 Disconnected: {message}")
            self.connection_label.setStyleSheet("color: #dc3545; font-weight: bold;")
    
    def show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def show_info_message(self, title: str, message: str):
        """Show info message dialog."""
        QMessageBox.information(self, title, message)
    
    def apply_theme(self, theme_name: str):
        """Apply theme to the window."""
        self.logger.debug(f"Applying theme: {theme_name}")
        # Theme application will be implemented later
        pass
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Main window closing")
        event.accept() 