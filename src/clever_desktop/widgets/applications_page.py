"""
Applications Management Page

Page for managing Clever Cloud applications with list view, details, and actions.
"""

import logging
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QGroupBox, QProgressBar, QMenu, QMessageBox,
    QSplitter, QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QPalette, QAction, QPixmap

from ..api.client import CleverCloudClient


class ApplicationCard(QFrame):
    """Application card widget for grid view."""
    
    # Signals
    application_selected = Signal(dict)  # application_data
    action_requested = Signal(str, dict)  # action, application_data
    
    def __init__(self, app_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with name and status
        header_layout = QHBoxLayout()
        
        # App name
        name = self.app_data.get('name', 'Unknown App')
        self.name_label = QLabel(name)
        self.name_label.setObjectName("appName")
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        # Status indicator
        state = self.app_data.get('state', 'UNKNOWN')
        status_color = self.get_status_color(state)
        self.status_label = QLabel(state)
        self.status_label.setObjectName("appStatus")
        self.status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # App type and zone
        app_type = self.app_data.get('instance', {}).get('type', 'Unknown')
        zone = self.app_data.get('zone', 'Unknown')
        
        info_label = QLabel(f"📦 {app_type} • 🌍 {zone}")
        info_label.setObjectName("appInfo")
        layout.addWidget(info_label)
        
        # Description or ID
        app_id = self.app_data.get('id', '')
        desc_label = QLabel(f"ID: {app_id[:12]}...")
        desc_label.setObjectName("appDescription")
        layout.addWidget(desc_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        # View details button
        self.details_btn = QPushButton("Details")
        self.details_btn.setObjectName("detailsButton")
        self.details_btn.clicked.connect(lambda: self.application_selected.emit(self.app_data))
        buttons_layout.addWidget(self.details_btn)
        
        # Quick actions menu
        self.actions_btn = QPushButton("Actions ▼")
        self.actions_btn.setObjectName("actionsButton")
        self.setup_actions_menu()
        buttons_layout.addWidget(self.actions_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_status_color(self, state: str) -> str:
        """Get color for application state."""
        colors = {
            'RUNNING': '#28a745',
            'STOPPED': '#dc3545',
            'DEPLOYING': '#007ACC',
            'RESTARTING': '#ffc107',
            'UNKNOWN': '#6c757d'
        }
        return colors.get(state, '#6c757d')
    
    def setup_actions_menu(self):
        """Setup the actions menu."""
        menu = QMenu(self)
        
        # Common actions based on state
        state = self.app_data.get('state', 'UNKNOWN')
        
        if state == 'RUNNING':
            restart_action = QAction("🔄 Restart", self)
            restart_action.triggered.connect(lambda: self.action_requested.emit('restart', self.app_data))
            menu.addAction(restart_action)
            
            stop_action = QAction("⏹️ Stop", self)
            stop_action.triggered.connect(lambda: self.action_requested.emit('stop', self.app_data))
            menu.addAction(stop_action)
        
        elif state == 'STOPPED':
            start_action = QAction("▶️ Start", self)
            start_action.triggered.connect(lambda: self.action_requested.emit('start', self.app_data))
            menu.addAction(start_action)
        
        menu.addSeparator()
        
        # Always available actions
        logs_action = QAction("📋 View Logs", self)
        logs_action.triggered.connect(lambda: self.action_requested.emit('logs', self.app_data))
        menu.addAction(logs_action)
        
        env_action = QAction("⚙️ Environment", self)
        env_action.triggered.connect(lambda: self.action_requested.emit('environment', self.app_data))
        menu.addAction(env_action)
        
        deploy_action = QAction("🚀 Deploy", self)
        deploy_action.triggered.connect(lambda: self.action_requested.emit('deploy', self.app_data))
        menu.addAction(deploy_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self.action_requested.emit('delete', self.app_data))
        menu.addAction(delete_action)
        
        self.actions_btn.setMenu(menu)
    
    def setup_styles(self):
        """Setup card styles."""
        self.setStyleSheet("""
        ApplicationCard {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
        }
        
        ApplicationCard:hover {
            border-color: #007ACC;
        }
        
        #appName {
            font-size: 16px;
            font-weight: bold;
            color: #212529;
        }
        
        #appInfo {
            color: #6c757d;
            font-size: 14px;
        }
        
        #appDescription {
            color: #6c757d;
            font-size: 12px;
        }
        
        #detailsButton, #actionsButton {
            padding: 6px 12px;
            border: 1px solid #007ACC;
            border-radius: 4px;
            background-color: white;
            color: #007ACC;
            font-size: 12px;
        }
        
        #detailsButton:hover, #actionsButton:hover {
            background-color: #007ACC;
            color: white;
        }
        """)


class ApplicationDetailsPanel(QWidget):
    """Application details panel."""
    
    # Signals
    action_requested = Signal(str, dict)  # action, application_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_app = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the details panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.header_label = QLabel("Select an application to view details")
        self.header_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #212529;
            padding: 10px 0;
        """)
        layout.addWidget(self.header_label)
        
        # Tabs for different information
        self.tabs = QTabWidget()
        
        # Overview tab
        self.overview_tab = QWidget()
        self.setup_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Environment tab
        self.env_tab = QWidget()
        self.setup_environment_tab()
        self.tabs.addTab(self.env_tab, "Environment")
        
        # Logs tab
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "Logs")
        
        layout.addWidget(self.tabs)
        
        # Initially hide tabs
        self.tabs.hide()
    
    def setup_overview_tab(self):
        """Setup the overview tab."""
        layout = QVBoxLayout(self.overview_tab)
        
        # Application info
        self.info_group = QGroupBox("Application Information")
        info_layout = QGridLayout(self.info_group)
        
        # Labels for info display
        self.info_labels = {}
        info_fields = [
            ("Name", "name"),
            ("ID", "id"),
            ("State", "state"),
            ("Type", "instance_type"),
            ("Zone", "zone"),
            ("Created", "created_at"),
            ("Last Deploy", "last_deploy")
        ]
        
        for i, (label, field) in enumerate(info_fields):
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel("-")
            
            info_layout.addWidget(label_widget, i, 0)
            info_layout.addWidget(value_widget, i, 1)
            
            self.info_labels[field] = value_widget
        
        layout.addWidget(self.info_group)
        
        # Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.action_buttons = {}
        actions = [
            ("start", "▶️ Start", "#28a745"),
            ("stop", "⏹️ Stop", "#dc3545"),
            ("restart", "🔄 Restart", "#007ACC"),
            ("deploy", "🚀 Deploy", "#007ACC")
        ]
        
        for action_id, text, color in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 15px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            btn.clicked.connect(lambda checked, aid=action_id: self._on_action_clicked(aid))
            actions_layout.addWidget(btn)
            self.action_buttons[action_id] = btn
        
        layout.addWidget(actions_group)
        layout.addStretch()
    
    def setup_environment_tab(self):
        """Setup the environment variables tab."""
        layout = QVBoxLayout(self.env_tab)
        
        # Environment variables display
        self.env_text = QTextEdit()
        self.env_text.setReadOnly(True)
        self.env_text.setPlainText("Environment variables will be displayed here...")
        layout.addWidget(self.env_text)
    
    def setup_logs_tab(self):
        """Setup the logs tab."""
        layout = QVBoxLayout(self.logs_tab)
        
        # Logs display
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setPlainText("Application logs will be displayed here...")
        layout.addWidget(self.logs_text)
        
        # Refresh logs button
        refresh_btn = QPushButton("🔄 Refresh Logs")
        refresh_btn.clicked.connect(self._refresh_logs)
        layout.addWidget(refresh_btn)
    
    def set_application(self, app_data: Dict[str, Any]):
        """Set the current application."""
        self.current_app = app_data
        self.update_display()
        self.tabs.show()
    
    def update_display(self):
        """Update the display with current application data."""
        if not self.current_app:
            return
        
        # Update header
        app_name = self.current_app.get('name', 'Unknown App')
        self.header_label.setText(f"Application: {app_name}")
        
        # Update info labels
        self.info_labels['name'].setText(self.current_app.get('name', '-'))
        self.info_labels['id'].setText(self.current_app.get('id', '-'))
        self.info_labels['state'].setText(self.current_app.get('state', '-'))
        self.info_labels['instance_type'].setText(
            self.current_app.get('instance', {}).get('type', '-')
        )
        self.info_labels['zone'].setText(self.current_app.get('zone', '-'))
        
        # Format dates if available
        created_at = self.current_app.get('creationDate')
        if created_at:
            self.info_labels['created_at'].setText(created_at[:10])  # Just date part
        
        # Update action buttons based on state
        state = self.current_app.get('state', 'UNKNOWN')
        self._update_action_buttons(state)
    
    def _update_action_buttons(self, state: str):
        """Update action buttons based on application state."""
        # Enable/disable buttons based on state
        if state == 'RUNNING':
            self.action_buttons['start'].setEnabled(False)
            self.action_buttons['stop'].setEnabled(True)
            self.action_buttons['restart'].setEnabled(True)
        elif state == 'STOPPED':
            self.action_buttons['start'].setEnabled(True)
            self.action_buttons['stop'].setEnabled(False)
            self.action_buttons['restart'].setEnabled(False)
        else:
            # Unknown state - enable all
            for btn in self.action_buttons.values():
                btn.setEnabled(True)
    
    def _on_action_clicked(self, action_id: str):
        """Handle action button click."""
        if self.current_app:
            self.action_requested.emit(action_id, self.current_app)
    
    def _refresh_logs(self):
        """Refresh application logs."""
        if self.current_app:
            self.action_requested.emit('refresh_logs', self.current_app)


class ApplicationsPage(QWidget):
    """Applications management page."""
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Data
        self.current_org_id = None  # Will be set when organization is selected
        self.applications = []
        
        self.setup_ui()
        self.setup_refresh_timer()
        
        self.logger.info("Applications page initialized")
    
    def setup_ui(self):
        """Setup the applications page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(30, 20, 30, 10)
        
        # Title
        title_label = QLabel("Applications")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #212529;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search applications...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.filter_applications)
        header_layout.addWidget(self.search_input)
        
        # View toggle (could add table/grid view toggle here)
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_applications)
        header_layout.addWidget(self.refresh_btn)
        
        # Create new app button
        self.create_btn = QPushButton("➕ New Application")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.create_btn.clicked.connect(self.create_application)
        header_layout.addWidget(self.create_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Applications list/grid
        self.apps_scroll = QScrollArea()
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setMinimumWidth(400)
        
        self.apps_container = QWidget()
        self.apps_layout = QVBoxLayout(self.apps_container)
        self.apps_layout.setContentsMargins(20, 10, 20, 20)
        self.apps_layout.setSpacing(15)
        
        # Loading label
        self.loading_label = QLabel("Loading applications...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 50px;")
        self.apps_layout.addWidget(self.loading_label)
        
        self.apps_scroll.setWidget(self.apps_container)
        splitter.addWidget(self.apps_scroll)
        
        # Details panel
        self.details_panel = ApplicationDetailsPanel()
        self.details_panel.action_requested.connect(self.handle_application_action)
        splitter.addWidget(self.details_panel)
        
        # Set splitter proportions
        splitter.setSizes([500, 400])
        
        layout.addWidget(splitter)
        
        # Load applications
        self.refresh_applications()
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_applications)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def refresh_applications(self):
        """Refresh applications list using QTimer to handle async."""
        # Use QTimer to schedule async data loading
        QTimer.singleShot(100, self._refresh_applications_async)
    
    def _refresh_applications_async(self):
        """Refresh applications using a separate thread."""
        from PySide6.QtCore import QThread, QObject, Signal
        
        class ApplicationsLoader(QObject):
            data_loaded = Signal(list)  # applications
            error_occurred = Signal(str)
            
            def __init__(self, api_client, org_id, logger):
                super().__init__()
                self.api_client = api_client
                self.org_id = org_id
                self.logger = logger
            
            def load_data(self):
                """Load applications in thread."""
                import asyncio
                
                async def fetch_applications():
                    try:
                        self.logger.info(f"Loading applications from API for org: {self.org_id}")
                        
                        # Get applications from API for current organization
                        if self.org_id:
                            applications = await self.api_client.get_applications(self.org_id)
                        else:
                            # Fallback to all applications if no org selected
                            applications = await self.api_client.get_applications()
                        
                        self.logger.info(f"Loaded {len(applications)} applications from API")
                        return applications
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load applications: {e}")
                        raise e
                
                try:
                    # Run async code in this thread
                    applications = asyncio.run(fetch_applications())
                    self.data_loaded.emit(applications)
                except Exception as e:
                    self.error_occurred.emit(str(e))
        
        # Show loading
        self.loading_label.setText("Loading applications...")
        self.loading_label.show()
        
        # Create thread and loader
        if hasattr(self, 'apps_thread') and self.apps_thread.isRunning():
            self.apps_thread.quit()
            self.apps_thread.wait()
        
        self.apps_thread = QThread()
        self.apps_loader = ApplicationsLoader(self.api_client, self.current_org_id, self.logger)
        self.apps_loader.moveToThread(self.apps_thread)
        
        # Connect signals
        self.apps_loader.data_loaded.connect(self._on_applications_loaded)
        self.apps_loader.error_occurred.connect(self._on_applications_error)
        self.apps_thread.started.connect(self.apps_loader.load_data)
        
        # Start thread
        self.apps_thread.start()
        self.logger.info("Started applications loading thread")
    
    def _on_applications_loaded(self, applications: list):
        """Handle successful applications loading."""
        self.logger.info(f"Applications loading completed: {len(applications)} applications")
        
        # Store applications
        self.applications = applications
        
        # Update display
        self.update_applications_display()
        
        # Cleanup thread
        self.apps_thread.quit()
        self.apps_thread.wait()
    
    def _on_applications_error(self, error: str):
        """Handle applications loading error."""
        self.logger.error(f"Applications loading failed: {error}")
        self.loading_label.setText(f"Error loading applications: {error}")
        
        # Cleanup thread
        self.apps_thread.quit()
        self.apps_thread.wait()
    
    def update_applications_display(self):
        """Update the applications display."""
        # Clear existing cards
        for i in reversed(range(self.apps_layout.count())):
            child = self.apps_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.applications:
            no_apps_label = QLabel("No applications found")
            no_apps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_apps_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 50px;")
            self.apps_layout.addWidget(no_apps_label)
            return
        
        # Add application cards
        for app in self.applications:
            card = ApplicationCard(app)
            card.application_selected.connect(self.details_panel.set_application)
            card.action_requested.connect(self.handle_application_action)
            self.apps_layout.addWidget(card)
        
        # Add stretch to push cards to top
        self.apps_layout.addStretch()
    
    def filter_applications(self, search_text: str):
        """Filter applications based on search text."""
        # This would filter the displayed applications
        # For now, just a placeholder
        pass
    
    def create_application(self):
        """Create a new application."""
        # This would open a create application dialog
        QMessageBox.information(self, "Create Application", "Create application dialog will be implemented here.")
    
    def handle_application_action(self, action: str, app_data: Dict[str, Any]):
        """Handle application actions."""
        app_name = app_data.get('name', 'Unknown')
        app_id = app_data.get('id', '')
        
        self.logger.info(f"Action '{action}' requested for application '{app_name}'")
        
        if action == 'start':
            self.start_application(app_id, app_name)
        elif action == 'stop':
            self.stop_application(app_id, app_name)
        elif action == 'restart':
            self.restart_application(app_id, app_name)
        elif action == 'deploy':
            self.deploy_application(app_id, app_name)
        elif action == 'logs':
            self.view_logs(app_id, app_name)
        elif action == 'environment':
            self.manage_environment(app_id, app_name)
        elif action == 'delete':
            self.delete_application(app_id, app_name)
        elif action == 'refresh_logs':
            self.refresh_logs(app_id, app_name)
    
    async def start_application(self, app_id: str, app_name: str):
        """Start an application."""
        try:
            await self.api_client.start_application(app_id)
            QMessageBox.information(self, "Success", f"Application '{app_name}' started successfully.")
            self.refresh_applications()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start application: {e}")
    
    async def stop_application(self, app_id: str, app_name: str):
        """Stop an application."""
        try:
            await self.api_client.stop_application(app_id)
            QMessageBox.information(self, "Success", f"Application '{app_name}' stopped successfully.")
            self.refresh_applications()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop application: {e}")
    
    async def restart_application(self, app_id: str, app_name: str):
        """Restart an application."""
        try:
            await self.api_client.restart_application(app_id)
            QMessageBox.information(self, "Success", f"Application '{app_name}' restarted successfully.")
            self.refresh_applications()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restart application: {e}")
    
    def deploy_application(self, app_id: str, app_name: str):
        """Deploy an application."""
        QMessageBox.information(self, "Deploy", f"Deploy dialog for '{app_name}' will be implemented here.")
    
    def view_logs(self, app_id: str, app_name: str):
        """View application logs."""
        QMessageBox.information(self, "Logs", f"Logs viewer for '{app_name}' will be implemented here.")
    
    def manage_environment(self, app_id: str, app_name: str):
        """Manage environment variables."""
        QMessageBox.information(self, "Environment", f"Environment manager for '{app_name}' will be implemented here.")
    
    def delete_application(self, app_id: str, app_name: str):
        """Delete an application."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete application '{app_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Delete", f"Delete functionality for '{app_name}' will be implemented here.")
    
    def refresh_logs(self, app_id: str, app_name: str):
        """Refresh application logs."""
        QMessageBox.information(self, "Refresh Logs", f"Refreshing logs for '{app_name}'...")
    
    def set_organization(self, org_id: str):
        """Set the current organization and refresh applications."""
        self.current_org_id = org_id
        self.logger.info(f"Applications page: Organization changed to {org_id}")
        # Refresh applications with new organization
        self.refresh_applications()
    
    def showEvent(self, event):
        """Handle page show event."""
        super().showEvent(event)
        # Refresh applications when page is shown
        self.refresh_applications() 