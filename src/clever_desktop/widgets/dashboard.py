"""
Main Dashboard

Central dashboard interface with sidebar navigation and content management.
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QStackedWidget,
    QLabel, QPushButton, QFrame, QScrollArea, QComboBox, QSpacerItem,
    QSizePolicy, QToolButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette

from ..api.client import CleverCloudClient


class NavigationSidebar(QWidget):
    """Sidebar navigation with page selection."""
    
    page_requested = Signal(str)  # page_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.button_group = QButtonGroup(self)
        
        self.setFixedWidth(280)  # Increased width
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)  # Reduced padding
        
        # Logo/Title
        title_label = QLabel("🚀 Clever Cloud")
        title_font = QFont()
        title_font.setPointSize(14)  # Slightly smaller
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setObjectName("sidebarTitle")
        header_layout.addWidget(title_label)
        
        layout.addWidget(header)
        
        # Navigation buttons
        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(15, 15, 15, 15)  # Better padding
        nav_layout.setSpacing(8)  # Increased spacing
        
        # Navigation items
        nav_items = [
            ("dashboard", "📊 Dashboard", True),
            ("applications", "🚀 Applications", False),
            ("addons", "🗃️ Add-ons", False),
            ("network", "🌐 Network Groups", False),
            ("logs", "📋 Logs", False),
            ("billing", "💰 Billing", False),
        ]
        
        for page_id, label, is_default in nav_items:
            btn = self.create_nav_button(page_id, label)
            if is_default:
                btn.setChecked(True)
            nav_layout.addWidget(btn)
        
        # Spacer
        nav_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Settings button
        settings_btn = self.create_nav_button("settings", "⚙️ Settings")
        nav_layout.addWidget(settings_btn)
        
        layout.addWidget(nav_frame)
    
    def create_nav_button(self, page_id: str, text: str) -> QPushButton:
        """Create a navigation button."""
        btn = QPushButton(text)
        btn.setObjectName("navButton")
        btn.setCheckable(True)
        btn.setMinimumHeight(40)
        btn.clicked.connect(lambda: self.page_requested.emit(page_id))
        
        self.button_group.addButton(btn)
        return btn
    
    def setup_styles(self):
        """Setup sidebar styles."""
        self.setStyleSheet("""
        NavigationSidebar {
            background-color: #f8f9fa;
            border-right: 1px solid #e9ecef;
        }
        
        #sidebarHeader {
            background-color: #007ACC;
            border: none;
        }
        
        #sidebarTitle {
            color: white;
            font-weight: bold;
        }
        
        #navButton {
            text-align: left;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            background-color: transparent;
            color: #495057;
            font-size: 15px;
            font-weight: 500;
        }
        
        #navButton:hover {
            background-color: #e9ecef;
            color: #212529;
        }
        
        #navButton:checked {
            background-color: #007ACC;
            color: white;
            font-weight: 600;
        }
        """)


class DashboardHeader(QWidget):
    """Dashboard header with user info and organization selector."""
    
    logout_requested = Signal()
    organization_changed = Signal(str)  # org_id
    refresh_requested = Signal()
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.user_info = {}
        self.organizations = []
        self.current_org_id = None
        
        self.setup_ui()
        self.setup_styles()
        
        # Show loading state initially
        self.org_combo.addItem("🔄 Loading organizations...")
        self.org_combo.setEnabled(False)
    
    def setup_ui(self):
        """Setup the header UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 6, 20, 6)  # Much more compact
        
        # Organization selector - much smaller
        org_label = QLabel("Org:")
        org_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 12px;")
        layout.addWidget(org_label)
        
        self.org_combo = QComboBox()
        self.org_combo.setMinimumWidth(150)  # Much smaller
        self.org_combo.setMaximumWidth(180)
        self.org_combo.currentTextChanged.connect(self._on_org_changed)
        layout.addWidget(self.org_combo)
        
        # Spacer
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # User info
        self.user_label = QLabel("🔄 Loading user...")
        self.user_label.setStyleSheet("color: #666; font-weight: 500;")
        layout.addWidget(self.user_label)
        
        # Refresh button (smaller)
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh data")
        self.refresh_btn.setMaximumWidth(28)
        self.refresh_btn.setMaximumHeight(28)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.refresh_btn)
        
        # Logout button (smaller)
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setMaximumHeight(28)
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_btn)
    
    def set_user_info(self, user_info: Dict[str, Any]):
        """Set user information."""
        self.user_info = user_info
        user_name = user_info.get('name', 'Unknown User')
        user_email = user_info.get('email', '')
        self.user_label.setText(f"👤 {user_name} ({user_email})")
        self.logger.info(f"DashboardHeader: Set user info for {user_name}")
    
    def set_organizations(self, organizations: list):
        """Set available organizations."""
        self.organizations = organizations
        self.org_combo.clear()
        self.org_combo.setEnabled(True)  # Enable the combo box
        
        self.logger.info(f"DashboardHeader: Setting {len(organizations)} organizations")
        
        for org in organizations:
            org_name = org.get('name', 'Unknown Organization')
            org_id = org.get('id', '')
            self.org_combo.addItem(org_name, org_id)
            self.logger.info(f"DashboardHeader: Added organization: {org_name} ({org_id})")
        
        self.logger.info(f"DashboardHeader: Organization combo now has {self.org_combo.count()} items")
        
        # If no current organization is set and we have organizations, select the first one
        if not self.current_org_id and organizations:
            self.current_org_id = organizations[0].get('id')
            self.org_combo.setCurrentIndex(0)
            self.logger.info(f"DashboardHeader: Auto-selected first organization: {self.current_org_id}")
    
    def _on_org_changed(self, org_name: str):
        """Handle organization change."""
        org_id = self.org_combo.currentData()
        if org_id:
            self.organization_changed.emit(org_id)
    
    def setup_styles(self):
        """Setup header styles."""
        self.setStyleSheet("""
        DashboardHeader {
            background-color: white;
            border-bottom: 1px solid #e9ecef;
            max-height: 40px;
        }
        
        QLabel {
            color: #495057;
            font-size: 12px;
        }
        
        QPushButton {
            padding: 4px 8px;
            border: 1px solid #007ACC;
            border-radius: 4px;
            background-color: white;
            color: #007ACC;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #007ACC;
            color: white;
        }
        
        QComboBox {
            padding: 4px 8px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
            font-size: 12px;
        }
        """)


class MainDashboard(QWidget):
    """Main dashboard with sidebar navigation and content area."""
    
    # Signals
    logout_requested = Signal()
    organization_changed = Signal(str)
    refresh_requested = Signal()
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.load_initial_data()
        
        self.logger.info("Main dashboard initialized")
    
    def setup_ui(self):
        """Setup the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = DashboardHeader(self.api_client)
        self.header.logout_requested.connect(self.logout_requested.emit)
        self.header.organization_changed.connect(self._on_organization_changed)
        self.header.refresh_requested.connect(self.refresh_requested.emit)
        layout.addWidget(self.header)
        
        # Main content area
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar
        self.sidebar = NavigationSidebar()
        self.sidebar.page_requested.connect(self._on_page_requested)
        main_splitter.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QStackedWidget()
        main_splitter.addWidget(self.content_area)
        
        # Set splitter proportions
        main_splitter.setSizes([280, 1000])  # Adjusted for new sidebar width
        main_splitter.setCollapsible(0, False)
        
        layout.addWidget(main_splitter)
        
        # Initialize pages
        self._setup_pages()
    
    def _setup_pages(self):
        """Setup content pages."""
        from .applications_page import ApplicationsPage
        from .dashboard_page import DashboardPage
        from .addons_page import AddonsPage
        
        # Dashboard page
        self.dashboard_page = DashboardPage(self.api_client)
        self.content_area.addWidget(self.dashboard_page)
        
        # Applications page
        self.applications_page = ApplicationsPage(self.api_client)
        self.content_area.addWidget(self.applications_page)
        
        # Add-ons page
        self.addons_page = AddonsPage(self.api_client)
        self.content_area.addWidget(self.addons_page)
        
        # Placeholder pages for other sections
        for page_name in ["network", "logs", "billing", "settings"]:
            placeholder = self._create_placeholder_page(page_name.title())
            self.content_area.addWidget(placeholder)
        
        # Show dashboard by default
        self.content_area.setCurrentWidget(self.dashboard_page)
    
    def _create_placeholder_page(self, title: str) -> QWidget:
        """Create a placeholder page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(f"🚧 {title} Page\nComing Soon!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #6c757d;
                padding: 50px;
            }
        """)
        layout.addWidget(label)
        
        return page
    
    def _on_page_requested(self, page_name: str):
        """Handle page navigation."""
        page_mapping = {
            "dashboard": 0,
            "applications": 1,
            "addons": 2,
            "network": 3,
            "logs": 4,
            "billing": 5,
            "settings": 6,
        }
        
        page_index = page_mapping.get(page_name, 0)
        self.content_area.setCurrentIndex(page_index)
        
        self.logger.info(f"Navigated to page: {page_name}")
    
    def _on_organization_changed(self, org_id: str):
        """Handle organization change and update all pages."""
        self.logger.info(f"Organization changed to: {org_id}")
        
        # Update all pages with new organization
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.set_organization(org_id)
        if hasattr(self, 'applications_page'):
            self.applications_page.set_organization(org_id)
        if hasattr(self, 'addons_page'):
            self.addons_page.set_organization(org_id)
        
        # Emit signal for external listeners
        self.organization_changed.emit(org_id)
    
    def load_initial_data(self):
        """Load initial dashboard data using QTimer to handle async."""
        # Organizations and user info will be provided by ApplicationManager
        # No need to load them here anymore
        self.logger.info("Dashboard initialized - waiting for data from ApplicationManager")
    
    def _load_data_async(self):
        """Load data asynchronously."""
        # This method is no longer needed since data comes from ApplicationManager
        # But keeping it for potential future use
        self.logger.info("Dashboard data loading handled by ApplicationManager")
    
    def refresh_data(self):
        """Refresh dashboard data."""
        self.logger.info("Refreshing dashboard data...")
        # Data refresh will be handled by ApplicationManager
        # Just refresh the current pages
        if hasattr(self, 'dashboard_page'):
            self.dashboard_page.refresh_stats()
        if hasattr(self, 'applications_page'):
            self.applications_page.refresh_applications()
        if hasattr(self, 'addons_page'):
            self.addons_page.refresh_addons() 