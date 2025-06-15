"""
Dashboard Overview Page

Main dashboard page showing overview statistics and quick actions.
"""

import logging
from typing import Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, QGroupBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPalette

from ..api.client import CleverCloudClient


class StatCard(QFrame):
    """Statistics card widget."""
    
    def __init__(self, title: str, value: str, icon: str = "", color: str = "#007ACC", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)  # More generous padding
        layout.setSpacing(10)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setStyleSheet("font-size: 24px;")
            header_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setObjectName("cardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setObjectName("cardValue")
        layout.addWidget(self.value_label)
    
    def update_value(self, new_value: str):
        """Update the card value."""
        self.value = new_value
        self.value_label.setText(new_value)
    
    def setup_styles(self):
        """Setup card styles."""
        self.setStyleSheet(f"""
        StatCard {{
            background-color: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            border-left: 5px solid {self.color};
            min-height: 100px;
        }}
        
        StatCard:hover {{
            border-color: {self.color};
            background-color: #f8f9fa;
        }}
        
        #cardTitle {{
            color: #6c757d;
            font-size: 14px;
            font-weight: 600;
        }}
        
        #cardValue {{
            color: #212529;
            font-size: 32px;
            font-weight: bold;
        }}
        """)


class QuickActionCard(QFrame):
    """Quick action card widget."""
    
    action_clicked = Signal(str)  # action_id
    
    def __init__(self, action_id: str, title: str, description: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.action_id = action_id
        self.title = title
        self.description = description
        self.icon = icon
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the card UI."""
        layout = QHBoxLayout(self)  # Horizontal layout for compact design
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setStyleSheet("font-size: 20px;")
            icon_label.setFixedSize(32, 32)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setObjectName("actionTitle")
        content_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setObjectName("actionDescription")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        layout.addLayout(content_layout)
        
        # Action button
        self.action_btn = QPushButton("Start")
        self.action_btn.setObjectName("actionButton")
        self.action_btn.setFixedSize(60, 32)
        self.action_btn.clicked.connect(lambda: self.action_clicked.emit(self.action_id))
        layout.addWidget(self.action_btn)
    
    def setup_styles(self):
        """Setup card styles."""
        self.setStyleSheet("""
        QuickActionCard {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            min-height: 60px;
        }
        
        QuickActionCard:hover {
            border-color: #007ACC;
            background-color: #f8f9fa;
        }
        
        #actionTitle {
            color: #212529;
            font-size: 14px;
            font-weight: bold;
        }
        
        #actionDescription {
            color: #6c757d;
            font-size: 12px;
            line-height: 1.3;
        }
        
        #actionButton {
            background-color: #007ACC;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        
        #actionButton:hover {
            background-color: #005a9e;
        }
        """)


class RecentActivityWidget(QGroupBox):
    """Recent activity widget."""
    
    def __init__(self, parent=None):
        super().__init__("Recent Activity", parent)
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(200)
        layout.addWidget(self.activity_list)
        
        # Add some sample activities
        self.add_activity("🚀", "Application 'my-app' deployed successfully", "2 minutes ago")
        self.add_activity("⚠️", "High memory usage detected on 'api-service'", "15 minutes ago")
        self.add_activity("✅", "SSL certificate renewed for 'example.com'", "1 hour ago")
        self.add_activity("��", "Monthly billing report generated", "3 hours ago")
    
    def add_activity(self, icon: str, message: str, time: str):
        """Add an activity item."""
        item = QListWidgetItem()
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(10, 5, 10, 5)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        item_layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #212529; font-size: 14px;")
        item_layout.addWidget(message_label)
        
        item_layout.addStretch()
        
        # Time
        time_label = QLabel(time)
        time_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        item_layout.addWidget(time_label)
        
        item.setSizeHint(item_widget.sizeHint())
        self.activity_list.addItem(item)
        self.activity_list.setItemWidget(item, item_widget)
    
    def setup_styles(self):
        """Setup widget styles."""
        self.setStyleSheet("""
        QGroupBox {
            font-size: 16px;
            font-weight: bold;
            color: #212529;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            background-color: white;
        }
        
        QListWidget {
            border: none;
            background-color: transparent;
        }
        
        QListWidget::item {
            border-bottom: 1px solid #f8f9fa;
            padding: 5px 0;
        }
        
        QListWidget::item:hover {
            background-color: #f8f9fa;
        }
        """)


class DashboardPage(QWidget):
    """Main dashboard overview page."""
    
    # Signals
    quick_action_requested = Signal(str)  # action_id
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Data
        self.current_org_id = None  # Will be set when organization is selected
        self.stats_data = {
            'applications': 0,
            'addons': 0,
            'organizations': 0,
            'running_apps': 0
        }
        
        self.setup_ui()
        self.setup_refresh_timer()
        
        self.logger.info("Dashboard page initialized")
    
    def setup_ui(self):
        """Setup the dashboard UI."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 10)  # Much tighter margins
        content_layout.setSpacing(15)  # Reduced spacing
        
        # Page header - more compact
        header_layout = QHBoxLayout()
        
        # Title and subtitle in same line
        title_label = QLabel("Dashboard")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #212529;
        """)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Monitor your Clever Cloud resources")
        subtitle_label.setStyleSheet("""
            font-size: 13px;
            color: #6c757d;
            margin-left: 15px;
        """)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # Statistics cards - horizontal layout for better space usage
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)  # Tighter spacing
        
        self.stats_cards = {
            'applications': StatCard("Applications", "0", "🚀", "#007ACC"),
            'running_apps': StatCard("Running", "0", "✅", "#28a745"),
            'addons': StatCard("Add-ons", "0", "🗃️", "#ffc107"),
            'organizations': StatCard("Organizations", "0", "🏢", "#6f42c1")
        }
        
        # Add cards horizontally
        for card in self.stats_cards.values():
            stats_layout.addWidget(card)
        
        content_layout.addLayout(stats_layout)
        
        # Main content area with two columns
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(15)  # Reduced spacing
        
        # Left column - Quick actions
        left_column = QVBoxLayout()
        
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #212529;
            margin-bottom: 8px;
        """)
        left_column.addWidget(actions_title)
        
        # Quick action cards - vertical layout in left column
        quick_actions = [
            ("deploy_app", "Deploy New Application", "Create and deploy a new application to Clever Cloud", "🚀"),
            ("create_addon", "Add Database", "Set up a new database or add-on for your applications", "🗃️"),
            ("view_logs", "View Application Logs", "Monitor your application logs in real-time", "📋"),
            ("manage_domains", "Manage Domains", "Configure custom domains and SSL certificates", "🌐")
        ]
        
        for action_id, title, description, icon in quick_actions:
            action_card = QuickActionCard(action_id, title, description, icon)
            action_card.action_clicked.connect(self.quick_action_requested.emit)
            left_column.addWidget(action_card)
        
        left_column.addStretch()
        
        # Right column - Recent activity
        right_column = QVBoxLayout()
        
        self.activity_widget = RecentActivityWidget()
        right_column.addWidget(self.activity_widget)
        
        # Add columns to main content
        main_content_layout.addLayout(left_column, 1)  # 50% width
        main_content_layout.addLayout(right_column, 1)  # 50% width
        
        content_layout.addLayout(main_content_layout)
        
        scroll.setWidget(content_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_stats(self):
        """Refresh dashboard statistics using QTimer to handle async."""
        # Use QTimer to schedule async data loading
        QTimer.singleShot(100, self._refresh_stats_async)
    
    def _refresh_stats_async(self):
        """Refresh dashboard statistics asynchronously."""
        import asyncio
        
        async def refresh_data():
            try:
                self.logger.info(f"Refreshing dashboard statistics for org: {self.current_org_id}")
                
                # Get applications for current organization
                if self.current_org_id:
                    applications = await self.api_client.get_applications(self.current_org_id)
                    addons = await self.api_client.get_addons(self.current_org_id)
                else:
                    # Fallback to all applications if no org selected
                    applications = await self.api_client.get_applications()
                    addons = await self.api_client.get_addons()
                
                self.stats_data['applications'] = len(applications)
                
                # Count running applications
                running_count = sum(1 for app in applications if app.get('state') == 'RUNNING')
                self.stats_data['running_apps'] = running_count
                
                # Get add-ons for current organization
                self.stats_data['addons'] = len(addons)
                
                # Get organizations (always show total)
                organizations = await self.api_client.get_organizations()
                self.stats_data['organizations'] = len(organizations)
                
                # Update UI
                self.update_stats_display()
                
                self.logger.info("Dashboard statistics updated")
                
            except Exception as e:
                self.logger.error(f"Failed to refresh dashboard stats: {e}")
        
        # Create task for async operation
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the coroutine
                asyncio.create_task(refresh_data())
            else:
                # Run in new loop
                asyncio.run(refresh_data())
        except Exception as e:
            self.logger.error(f"Failed to schedule stats refresh: {e}")
    
    def update_stats_display(self):
        """Update the statistics display."""
        self.stats_cards['applications'].update_value(str(self.stats_data['applications']))
        self.stats_cards['running_apps'].update_value(str(self.stats_data['running_apps']))
        self.stats_cards['addons'].update_value(str(self.stats_data['addons']))
        self.stats_cards['organizations'].update_value(str(self.stats_data['organizations']))
    
    def set_organization(self, org_id: str):
        """Set the current organization and refresh data."""
        self.current_org_id = org_id
        self.logger.info(f"Dashboard page: Organization changed to {org_id}")
        # Refresh stats with new organization
        self.refresh_stats()
    
    def showEvent(self, event):
        """Handle page show event."""
        super().showEvent(event)
        # Refresh stats when page is shown
        if hasattr(self, 'api_client'):
            self.refresh_stats() 