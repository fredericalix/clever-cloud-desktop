"""
Add-ons Management Page

Comprehensive add-ons management interface with listing, creation, and configuration.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel, 
    QPushButton, QLineEdit, QComboBox, QGridLayout, QSpacerItem, 
    QSizePolicy, QMenu, QMessageBox, QDialog, QFormLayout, QSpinBox,
    QTextEdit, QTabWidget, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QThread, QObject
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction, QPalette

from ..api.client import CleverCloudClient


class AddonCard(QFrame):
    """Individual add-on card widget."""
    
    # Signals
    action_requested = Signal(str, str)  # action, addon_id
    
    def __init__(self, addon_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.addon_data = addon_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the add-on card UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            AddonCard {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                margin: 4px;
            }
            AddonCard:hover {
                border-color: #2563eb;
                background-color: #f8fafc;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with name and status
        header_layout = QHBoxLayout()
        
        # Add-on name and provider
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        
        name_label = QLabel(self.addon_data.get('name', 'Unknown'))
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #1f2937;
        """)
        name_layout.addWidget(name_label)
        
        provider_label = QLabel(f"Provider: {self.addon_data.get('provider', {}).get('name', 'Unknown')}")
        provider_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
        """)
        name_layout.addWidget(provider_label)
        
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        # Status indicator
        status = self.addon_data.get('status', 'unknown').lower()
        status_color = {
            'running': '#10b981',
            'stopped': '#ef4444', 
            'starting': '#f59e0b',
            'stopping': '#f59e0b',
            'unknown': '#6b7280'
        }.get(status, '#6b7280')
        
        status_label = QLabel(status.title())
        status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        status_label.setFixedHeight(24)
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # Add-on details
        details_layout = QGridLayout()
        details_layout.setSpacing(4)
        
        # Plan information
        plan = self.addon_data.get('plan', {})
        plan_label = QLabel("Plan:")
        plan_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        plan_value = QLabel(plan.get('name', 'Unknown'))
        plan_value.setStyleSheet("font-size: 11px; color: #374151;")
        details_layout.addWidget(plan_label, 0, 0)
        details_layout.addWidget(plan_value, 0, 1)
        
        # Region
        region_label = QLabel("Region:")
        region_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        region_value = QLabel(self.addon_data.get('region', 'Unknown'))
        region_value.setStyleSheet("font-size: 11px; color: #374151;")
        details_layout.addWidget(region_label, 1, 0)
        details_layout.addWidget(region_value, 1, 1)
        
        # Creation date
        created_at = self.addon_data.get('creationDate')
        if created_at:
            try:
                # Parse ISO date
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y-%m-%d')
            except:
                date_str = 'Unknown'
        else:
            date_str = 'Unknown'
            
        created_label = QLabel("Created:")
        created_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        created_value = QLabel(date_str)
        created_value.setStyleSheet("font-size: 11px; color: #374151;")
        details_layout.addWidget(created_label, 0, 2)
        details_layout.addWidget(created_value, 0, 3)
        
        # ID (shortened)
        addon_id = self.addon_data.get('id', '')
        short_id = addon_id[:8] + '...' if len(addon_id) > 8 else addon_id
        id_label = QLabel("ID:")
        id_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        id_value = QLabel(short_id)
        id_value.setStyleSheet("font-size: 11px; color: #374151; font-family: monospace;")
        details_layout.addWidget(id_label, 1, 2)
        details_layout.addWidget(id_value, 1, 3)
        
        layout.addLayout(details_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # Quick actions based on status
        if status == 'running':
            restart_btn = QPushButton("Restart")
            restart_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f59e0b;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d97706;
                }
            """)
            restart_btn.clicked.connect(lambda: self.action_requested.emit('restart', self.addon_data['id']))
            actions_layout.addWidget(restart_btn)
        
        # More actions menu
        more_btn = QPushButton("⋯")
        more_btn.setFixedSize(28, 28)
        more_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        
        # Create context menu
        menu = QMenu(self)
        
        # Environment variables
        env_action = QAction("Environment Variables", self)
        env_action.triggered.connect(lambda: self.action_requested.emit('environment', self.addon_data['id']))
        menu.addAction(env_action)
        
        # Configuration
        config_action = QAction("Configuration", self)
        config_action.triggered.connect(lambda: self.action_requested.emit('configure', self.addon_data['id']))
        menu.addAction(config_action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction("Delete Add-on", self)
        delete_action.triggered.connect(lambda: self.action_requested.emit('delete', self.addon_data['id']))
        menu.addAction(delete_action)
        
        more_btn.setMenu(menu)
        actions_layout.addWidget(more_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def update_addon_data(self, addon_data: Dict[str, Any]):
        """Update the add-on data and refresh display."""
        self.addon_data = addon_data
        # Recreate UI with new data
        # Clear layout
        layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Recreate UI
        self.setup_ui()


class AddonCreationDialog(QDialog):
    """Dialog for creating new add-ons."""
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.providers = []
        self.selected_provider = None
        self.setup_ui()
        self.load_providers()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Create New Add-on")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Create New Add-on")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Add-on name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter add-on name")
        form_layout.addRow("Name:", self.name_input)
        
        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        form_layout.addRow("Provider:", self.provider_combo)
        
        # Plan selection
        self.plan_combo = QComboBox()
        form_layout.addRow("Plan:", self.plan_combo)
        
        # Region selection
        self.region_combo = QComboBox()
        form_layout.addRow("Region:", self.region_combo)
        
        layout.addLayout(form_layout)
        
        # Provider description
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(100)
        self.description_text.setReadOnly(True)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_text)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Add-on")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.create_btn.clicked.connect(self.create_addon)
        self.create_btn.setEnabled(False)
        buttons_layout.addWidget(self.create_btn)
        
        layout.addLayout(buttons_layout)
        
        # Enable create button when form is valid
        self.name_input.textChanged.connect(self.validate_form)
        self.provider_combo.currentTextChanged.connect(self.validate_form)
    
    def load_providers(self):
        """Load available add-on providers."""
        # TODO: Load from API
        # For now, use common providers
        providers = [
            {
                'id': 'postgresql-addon',
                'name': 'PostgreSQL',
                'shortDesc': 'PostgreSQL database service',
                'plans': [
                    {'id': 'dev', 'name': 'DEV', 'price': 0},
                    {'id': 'small', 'name': 'Small', 'price': 7},
                    {'id': 'medium', 'name': 'Medium', 'price': 20}
                ],
                'regions': ['par', 'mtl', 'sgp']
            },
            {
                'id': 'mysql-addon',
                'name': 'MySQL',
                'shortDesc': 'MySQL database service',
                'plans': [
                    {'id': 'dev', 'name': 'DEV', 'price': 0},
                    {'id': 'small', 'name': 'Small', 'price': 7}
                ],
                'regions': ['par', 'mtl']
            },
            {
                'id': 'redis-addon',
                'name': 'Redis',
                'shortDesc': 'Redis in-memory data store',
                'plans': [
                    {'id': 'dev', 'name': 'DEV', 'price': 0},
                    {'id': 'small', 'name': 'Small', 'price': 10}
                ],
                'regions': ['par', 'mtl', 'sgp']
            }
        ]
        
        self.providers = providers
        self.provider_combo.clear()
        self.provider_combo.addItem("Select a provider...")
        
        for provider in providers:
            self.provider_combo.addItem(provider['name'], provider)
    
    def on_provider_changed(self):
        """Handle provider selection change."""
        current_data = self.provider_combo.currentData()
        if current_data:
            self.selected_provider = current_data
            
            # Update description
            self.description_text.setPlainText(current_data['shortDesc'])
            
            # Update plans
            self.plan_combo.clear()
            for plan in current_data['plans']:
                price_text = "Free" if plan['price'] == 0 else f"€{plan['price']}/month"
                self.plan_combo.addItem(f"{plan['name']} ({price_text})", plan)
            
            # Update regions
            self.region_combo.clear()
            for region in current_data['regions']:
                region_name = {
                    'par': 'Paris (par)',
                    'mtl': 'Montreal (mtl)',
                    'sgp': 'Singapore (sgp)'
                }.get(region, region)
                self.region_combo.addItem(region_name, region)
        else:
            self.selected_provider = None
            self.description_text.clear()
            self.plan_combo.clear()
            self.region_combo.clear()
    
    def validate_form(self):
        """Validate form and enable/disable create button."""
        is_valid = (
            bool(self.name_input.text().strip()) and
            self.selected_provider is not None and
            self.plan_combo.currentData() is not None
        )
        self.create_btn.setEnabled(is_valid)
    
    def create_addon(self):
        """Create the add-on."""
        if not self.selected_provider:
            return
        
        name = self.name_input.text().strip()
        plan = self.plan_combo.currentData()
        region = self.region_combo.currentData()
        
        # TODO: Implement actual add-on creation via API
        QMessageBox.information(
            self,
            "Add-on Creation",
            f"Add-on '{name}' would be created with:\n"
            f"Provider: {self.selected_provider['name']}\n"
            f"Plan: {plan['name']}\n"
            f"Region: {region}\n\n"
            f"(Implementation pending)"
        )
        
        self.accept()


class AddonsPage(QWidget):
    """Main add-ons management page."""
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Data
        self.current_org_id = None  # Will be set when organization is selected
        self.addons = []
        self.filtered_addons = []
        
        self.setup_ui()
        self.setup_refresh_timer()
        
        self.logger.info("Add-ons page initialized")
    
    def setup_ui(self):
        """Setup the add-ons page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Add-ons")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #212529;
        """)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Manage your databases and services")
        subtitle_label.setStyleSheet("""
            font-size: 13px;
            color: #6c757d;
            margin-left: 15px;
        """)
        header_layout.addWidget(subtitle_label)
        
        header_layout.addStretch()
        
        # Create add-on button
        create_btn = QPushButton("Create Add-on")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        create_btn.clicked.connect(self.create_addon)
        header_layout.addWidget(create_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_addons)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filters and search
        filters_layout = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search add-ons...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self.filter_addons)
        filters_layout.addWidget(self.search_input)
        
        # Provider filter
        self.provider_filter = QComboBox()
        self.provider_filter.addItem("All Providers")
        self.provider_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                min-width: 120px;
            }
        """)
        self.provider_filter.currentTextChanged.connect(self.filter_addons)
        filters_layout.addWidget(self.provider_filter)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Running", "Stopped", "Starting", "Stopping"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                min-width: 100px;
            }
        """)
        self.status_filter.currentTextChanged.connect(self.filter_addons)
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Add-ons grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.addons_widget = QWidget()
        self.addons_layout = QGridLayout(self.addons_widget)
        self.addons_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.addons_widget)
        layout.addWidget(self.scroll_area)
        
        # Empty state
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel("🗃️")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        empty_layout.addWidget(empty_icon)
        
        empty_title = QLabel("No Add-ons Found")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #6b7280; margin-bottom: 5px;")
        empty_layout.addWidget(empty_title)
        
        empty_desc = QLabel("Create your first add-on to get started with databases and services.")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setStyleSheet("font-size: 14px; color: #9ca3af; margin-bottom: 20px;")
        empty_layout.addWidget(empty_desc)
        
        empty_create_btn = QPushButton("Create Add-on")
        empty_create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        empty_create_btn.clicked.connect(self.create_addon)
        empty_layout.addWidget(empty_create_btn)
        
        layout.addWidget(self.empty_state)
        self.empty_state.hide()
    
    def setup_refresh_timer(self):
        """Setup auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_addons)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_addons(self):
        """Refresh add-ons list using real API data."""
        self.logger.info(f"Refreshing add-ons for org: {self.current_org_id}")
        
        # Use QTimer to schedule async data loading
        QTimer.singleShot(100, self._refresh_addons_async)
    
    def _refresh_addons_async(self):
        """Refresh add-ons using a separate thread."""
        
        class AddonsLoader(QObject):
            data_loaded = Signal(list)  # addons
            error_occurred = Signal(str)
            
            def __init__(self, api_client, org_id, logger):
                super().__init__()
                self.api_client = api_client
                self.org_id = org_id
                self.logger = logger
            
            def load_data(self):
                """Load add-ons in thread."""
                import asyncio
                
                async def fetch_addons():
                    try:
                        self.logger.info(f"Loading add-ons from API for org: {self.org_id}")
                        
                        # Get add-ons from API for current organization
                        if self.org_id:
                            addons = await self.api_client.get_addons(self.org_id)
                        else:
                            # Fallback to all add-ons if no org selected
                            addons = await self.api_client.get_addons()
                        
                        self.logger.info(f"Loaded {len(addons)} add-ons from API")
                        return addons
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load add-ons: {e}")
                        raise e
                
                try:
                    # Run async code in this thread
                    addons = asyncio.run(fetch_addons())
                    self.data_loaded.emit(addons)
                except Exception as e:
                    self.error_occurred.emit(str(e))
        
        # Create thread and loader
        if hasattr(self, 'addons_thread') and self.addons_thread.isRunning():
            self.addons_thread.quit()
            self.addons_thread.wait()
        
        self.addons_thread = QThread()
        self.addons_loader = AddonsLoader(self.api_client, self.current_org_id, self.logger)
        self.addons_loader.moveToThread(self.addons_thread)
        
        # Connect signals
        self.addons_loader.data_loaded.connect(self._on_addons_loaded)
        self.addons_loader.error_occurred.connect(self._on_addons_error)
        self.addons_thread.started.connect(self.addons_loader.load_data)
        
        # Start thread
        self.addons_thread.start()
        self.logger.info("Started add-ons loading thread")
    
    def _on_addons_loaded(self, addons: list):
        """Handle successful add-ons loading."""
        self.logger.info(f"Add-ons loading completed: {len(addons)} add-ons")
        
        # Store add-ons
        self.addons = addons
        
        # Update provider filter and display
        self.update_provider_filter()
        self.filter_addons()
        
        # Cleanup thread
        self.addons_thread.quit()
        self.addons_thread.wait()
    
    def _on_addons_error(self, error: str):
        """Handle add-ons loading error."""
        self.logger.error(f"Add-ons loading failed: {error}")
        
        # Show empty state with error
        self.addons = []
        self.update_addons_display()
        
        # Cleanup thread
        self.addons_thread.quit()
        self.addons_thread.wait()
    
    def set_organization(self, org_id: str):
        """Set the current organization and refresh add-ons."""
        self.current_org_id = org_id
        self.logger.info(f"Add-ons page: Organization changed to {org_id}")
        # Refresh add-ons with new organization
        self.refresh_addons()
    
    def update_provider_filter(self):
        """Update provider filter options."""
        current_providers = set()
        for addon in self.addons:
            provider_name = addon.get('provider', {}).get('name', 'Unknown')
            current_providers.add(provider_name)
        
        # Update combo box
        current_selection = self.provider_filter.currentText()
        self.provider_filter.clear()
        self.provider_filter.addItem("All Providers")
        
        for provider in sorted(current_providers):
            self.provider_filter.addItem(provider)
        
        # Restore selection if possible
        index = self.provider_filter.findText(current_selection)
        if index >= 0:
            self.provider_filter.setCurrentIndex(index)
    
    def filter_addons(self):
        """Filter add-ons based on search and filters."""
        search_text = self.search_input.text().lower()
        provider_filter = self.provider_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        self.filtered_addons = []
        
        for addon in self.addons:
            # Search filter
            if search_text:
                addon_name = addon.get('name', '').lower()
                provider_name = addon.get('provider', {}).get('name', '').lower()
                if search_text not in addon_name and search_text not in provider_name:
                    continue
            
            # Provider filter
            if provider_filter != "All Providers":
                if addon.get('provider', {}).get('name') != provider_filter:
                    continue
            
            # Status filter
            if status_filter != "All Status":
                if addon.get('status', '').title() != status_filter:
                    continue
            
            self.filtered_addons.append(addon)
        
        self.update_addons_display()
    
    def update_addons_display(self):
        """Update the add-ons display."""
        # Clear existing cards
        while self.addons_layout.count():
            child = self.addons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.filtered_addons:
            self.scroll_area.hide()
            self.empty_state.show()
            return
        
        self.empty_state.hide()
        self.scroll_area.show()
        
        # Add add-on cards in grid layout
        columns = 2  # 2 cards per row
        for i, addon in enumerate(self.filtered_addons):
            row = i // columns
            col = i % columns
            
            card = AddonCard(addon)
            card.action_requested.connect(self.handle_addon_action)
            self.addons_layout.addWidget(card, row, col)
        
        # Add stretch to fill remaining space
        self.addons_layout.setRowStretch(len(self.filtered_addons) // columns + 1, 1)
    
    def handle_addon_action(self, action: str, addon_id: str):
        """Handle add-on actions."""
        self.logger.info(f"Add-on action requested: {action} for {addon_id}")
        
        if action == 'restart':
            self.restart_addon(addon_id)
        elif action == 'environment':
            self.show_addon_environment(addon_id)
        elif action == 'configure':
            self.configure_addon(addon_id)
        elif action == 'delete':
            self.delete_addon(addon_id)
    
    def create_addon(self):
        """Show create add-on dialog."""
        dialog = AddonCreationDialog(self.api_client, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_addons()
    
    def restart_addon(self, addon_id: str):
        """Restart an add-on."""
        reply = QMessageBox.question(
            self,
            "Restart Add-on",
            "Are you sure you want to restart this add-on?\n\nThis may cause temporary downtime.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement actual restart
            QMessageBox.information(self, "Restart Add-on", "Add-on restart initiated.")
    
    def show_addon_environment(self, addon_id: str):
        """Show add-on environment variables."""
        # TODO: Implement environment variables dialog
        QMessageBox.information(self, "Environment Variables", f"Environment variables for {addon_id}\n(Implementation pending)")
    
    def configure_addon(self, addon_id: str):
        """Configure add-on settings."""
        # TODO: Implement configuration dialog
        QMessageBox.information(self, "Configure Add-on", f"Configuration for {addon_id}\n(Implementation pending)")
    
    def delete_addon(self, addon_id: str):
        """Delete an add-on."""
        reply = QMessageBox.warning(
            self,
            "Delete Add-on",
            "Are you sure you want to delete this add-on?\n\n⚠️ This action cannot be undone and will permanently delete all data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement actual deletion
            QMessageBox.information(self, "Delete Add-on", "Add-on deletion initiated.")
    
    def showEvent(self, event):
        """Handle page show event."""
        super().showEvent(event)
        # Refresh add-ons when page is shown
        if hasattr(self, 'api_client'):
            self.refresh_addons() 