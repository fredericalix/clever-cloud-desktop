"""
Network Groups Management Page

Comprehensive Network Groups management interface with visual topology,
creation wizard, and member management.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel, 
    QPushButton, QLineEdit, QComboBox, QGridLayout, QSpacerItem, 
    QSizePolicy, QMenu, QMessageBox, QDialog, QFormLayout, QSpinBox,
    QTextEdit, QTabWidget, QGroupBox, QCheckBox, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsLineItem, QGraphicsTextItem, QSplitter, QTreeWidget,
    QTreeWidgetItem, QToolButton, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QThread, QObject, QPointF, QRectF
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QAction, QPalette, QPen, QBrush,
    QLinearGradient, QRadialGradient
)

from clever_desktop.api.client import CleverCloudClient


class NetworkGroupCard(QFrame):
    """Individual Network Group card widget."""
    
    # Signals
    action_requested = Signal(str, str)  # action, ng_id
    view_topology_requested = Signal(str)  # ng_id
    
    def __init__(self, ng_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.ng_data = ng_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the Network Group card UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            NetworkGroupCard {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                margin: 4px;
            }
            NetworkGroupCard:hover {
                border-color: #10b981;
                background-color: #f0fdf4;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with name and status
        header_layout = QHBoxLayout()
        
        # Network Group name and description
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        
        name_label = QLabel(self.ng_data.get('name', 'Unknown'))
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #1f2937;
        """)
        name_layout.addWidget(name_label)
        
        description = self.ng_data.get('description') or 'No description'
        if len(description) > 50:
            description = description[:47] + "..."
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
        """)
        name_layout.addWidget(desc_label)
        
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        # Status indicator
        status = self.ng_data.get('status', 'active').lower()
        status_color = {
            'active': '#10b981',
            'inactive': '#ef4444', 
            'pending': '#f59e0b',
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
        
        # Network Group details
        details_layout = QGridLayout()
        details_layout.setSpacing(4)
        
        # Member count
        members = self.ng_data.get('members', [])
        member_count = len(members) if isinstance(members, list) else 0
        
        members_label = QLabel("Members:")
        members_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        members_value = QLabel(f"{member_count} resources")
        members_value.setStyleSheet("font-size: 11px; color: #374151;")
        details_layout.addWidget(members_label, 0, 0)
        details_layout.addWidget(members_value, 0, 1)
        
        # External peers
        external_peers = self.ng_data.get('externalPeers', [])
        peers_count = len(external_peers) if isinstance(external_peers, list) else 0
        
        peers_label = QLabel("External Peers:")
        peers_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        peers_value = QLabel(f"{peers_count} peers")
        peers_value.setStyleSheet("font-size: 11px; color: #374151;")
        details_layout.addWidget(peers_label, 1, 0)
        details_layout.addWidget(peers_value, 1, 1)
        
        # Creation date
        created_at = self.ng_data.get('creationDate')
        if created_at:
            try:
                # Handle Unix timestamp (seconds or milliseconds)
                if isinstance(created_at, (int, float)):
                    if created_at > 1e10:  # Milliseconds
                        created_at = created_at / 1000
                    date_obj = datetime.fromtimestamp(created_at)
                else:
                    # Parse ISO date
                    date_obj = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
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
        ng_id = self.ng_data.get('id', '')
        short_id = ng_id[:8] + '...' if len(ng_id) > 8 else ng_id
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
        
        # View Topology button
        topology_btn = QPushButton("🌐 View Topology")
        topology_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        topology_btn.clicked.connect(lambda: self.view_topology_requested.emit(self.ng_data['id']))
        actions_layout.addWidget(topology_btn)
        
        # Manage Members button
        members_btn = QPushButton("👥 Members")
        members_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        members_btn.clicked.connect(lambda: self.action_requested.emit('members', self.ng_data['id']))
        actions_layout.addWidget(members_btn)
        
        actions_layout.addStretch()
        
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
        
        # Add External Peer
        peer_action = QAction("🔗 Add External Peer", self)
        peer_action.triggered.connect(lambda: self.action_requested.emit('add_peer', self.ng_data['id']))
        menu.addAction(peer_action)
        
        # Configure
        config_action = QAction("⚙️ Configure", self)
        config_action.triggered.connect(lambda: self.action_requested.emit('configure', self.ng_data['id']))
        menu.addAction(config_action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self.action_requested.emit('delete', self.ng_data['id']))
        menu.addAction(delete_action)
        
        more_btn.setMenu(menu)
        actions_layout.addWidget(more_btn)
        
        layout.addLayout(actions_layout)
    
    def update_ng_data(self, ng_data: Dict[str, Any]):
        """Update Network Group data and refresh display."""
        self.ng_data = ng_data
        # Refresh the UI with new data
        # For now, we'll recreate the UI
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        self.setup_ui()


class NetworkTopologyView(QGraphicsView):
    """Interactive network topology visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Set background
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        self.ng_data = None
        self.node_items = {}
        self.connection_items = []
    
    def load_network_group(self, ng_data: Dict[str, Any]):
        """Load and visualize a Network Group."""
        self.ng_data = ng_data
        self.scene.clear()
        self.node_items.clear()
        self.connection_items.clear()
        
        if not ng_data:
            return
        
        # Create central Network Group node
        ng_node = self._create_ng_node(ng_data)
        self.scene.addItem(ng_node)
        self.node_items['ng_center'] = ng_node
        
        # Add member nodes
        members = ng_data.get('members', [])
        for i, member in enumerate(members):
            member_node = self._create_member_node(member, i)
            self.scene.addItem(member_node)
            self.node_items[f'member_{i}'] = member_node
            
            # Create connection line
            connection = self._create_connection(ng_node, member_node)
            self.scene.addItem(connection)
            self.connection_items.append(connection)
        
        # Add external peer nodes
        external_peers = ng_data.get('externalPeers', [])
        for i, peer in enumerate(external_peers):
            peer_node = self._create_peer_node(peer, i)
            self.scene.addItem(peer_node)
            self.node_items[f'peer_{i}'] = peer_node
            
            # Create connection line
            connection = self._create_connection(ng_node, peer_node, is_external=True)
            self.scene.addItem(connection)
            self.connection_items.append(connection)
        
        # Auto-fit the view
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def _create_ng_node(self, ng_data: Dict[str, Any]) -> QGraphicsItem:
        """Create the central Network Group node."""
        # Create a circular node for the Network Group
        node = QGraphicsEllipseItem(-40, -40, 80, 80)
        
        # Set gradient fill
        gradient = QRadialGradient(0, 0, 40)
        gradient.setColorAt(0, QColor("#10b981"))
        gradient.setColorAt(1, QColor("#059669"))
        node.setBrush(QBrush(gradient))
        node.setPen(QPen(QColor("#047857"), 2))
        
        # Add text label
        text = QGraphicsTextItem(ng_data.get('name', 'Network Group'))
        text.setPos(-30, 50)
        text.setDefaultTextColor(QColor("#1f2937"))
        font = text.font()
        font.setBold(True)
        font.setPointSize(10)
        text.setFont(font)
        
        # Group items
        group = self.scene.createItemGroup([node, text])
        group.setPos(0, 0)
        
        return group
    
    def _create_member_node(self, member: Dict[str, Any], index: int) -> QGraphicsItem:
        """Create a member node (application/addon)."""
        import math
        
        # Position nodes in a circle around the center
        angle = (2 * math.pi * index) / max(1, len(self.ng_data.get('members', [])))
        radius = 150
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        # Create rectangular node for applications/addons
        node = QGraphicsRectItem(-30, -20, 60, 40)
        node.setBrush(QBrush(QColor("#3b82f6")))
        node.setPen(QPen(QColor("#2563eb"), 2))
        node.setPos(x, y)
        
        # Add text label
        name = member.get('name', f'Member {index + 1}')
        text = QGraphicsTextItem(name)
        text.setPos(x - 25, y + 25)
        text.setDefaultTextColor(QColor("#1f2937"))
        font = text.font()
        font.setPointSize(8)
        text.setFont(font)
        
        # Group items
        group = self.scene.createItemGroup([node, text])
        
        return group
    
    def _create_peer_node(self, peer: Dict[str, Any], index: int) -> QGraphicsItem:
        """Create an external peer node."""
        import math
        
        # Position peers on the outer ring
        angle = (2 * math.pi * index) / max(1, len(self.ng_data.get('externalPeers', [])))
        radius = 250
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        # Create diamond node for external peers
        points = [QPointF(0, -20), QPointF(20, 0), QPointF(0, 20), QPointF(-20, 0)]
        node = self.scene.addPolygon(points, QPen(QColor("#8b5cf6"), 2), QBrush(QColor("#a855f7")))
        node.setPos(x, y)
        
        # Add text label
        name = peer.get('peerLabel', f'Peer {index + 1}')
        text = QGraphicsTextItem(name)
        text.setPos(x - 20, y + 25)
        text.setDefaultTextColor(QColor("#1f2937"))
        font = text.font()
        font.setPointSize(8)
        text.setFont(font)
        
        # Group items
        group = self.scene.createItemGroup([node, text])
        
        return group
    
    def _create_connection(self, node1: QGraphicsItem, node2: QGraphicsItem, is_external: bool = False) -> QGraphicsItem:
        """Create a connection line between two nodes."""
        pos1 = node1.pos()
        pos2 = node2.pos()
        
        line = QGraphicsLineItem(pos1.x(), pos1.y(), pos2.x(), pos2.y())
        
        if is_external:
            # Dashed line for external connections
            pen = QPen(QColor("#8b5cf6"), 2, Qt.PenStyle.DashLine)
        else:
            # Solid line for internal connections
            pen = QPen(QColor("#10b981"), 2)
        
        line.setPen(pen)
        return line


class NetworkGroupCreationDialog(QDialog):
    """Dialog for creating new Network Groups."""
    
    def __init__(self, api_client: CleverCloudClient, org_id: str, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.org_id = org_id
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Create Network Group")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the creation dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Create New Network Group")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Network Group name...")
        form_layout.addRow("Name:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter description (optional)...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Network Group")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.create_btn.clicked.connect(self.create_network_group)
        buttons_layout.addWidget(self.create_btn)
        
        layout.addLayout(buttons_layout)
        
        # Enable/disable create button based on input
        self.name_input.textChanged.connect(self.validate_form)
        self.validate_form()
    
    def validate_form(self):
        """Validate form and enable/disable create button."""
        name = self.name_input.text().strip()
        self.create_btn.setEnabled(bool(name))
    
    def create_network_group(self):
        """Create the Network Group."""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a name for the Network Group.")
            return
        
        self.create_btn.setEnabled(False)
        self.create_btn.setText("Creating...")
        
        # TODO: Implement actual API call
        # For now, just simulate success
        QTimer.singleShot(1000, self.accept)


class NetworkGroupsPage(QWidget):
    """Main Network Groups management page."""
    
    # Signals
    organization_changed = Signal(str)
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        self.current_org_id = None
        self.network_groups = []
        self.filtered_network_groups = []
        
        self.setup_ui()
        self.setup_refresh_timer()
        
        self.logger.info("Network Groups page initialized")
    
    def setup_ui(self):
        """Setup the main UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🌐 Network Groups")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create Network Group button
        self.create_btn = QPushButton("➕ Create Network Group")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.create_btn.clicked.connect(self.create_network_group)
        header_layout.addWidget(self.create_btn)
        
        # Demo Mode button (for when feature is not available)
        self.demo_btn = QPushButton("🎮 Demo Mode")
        self.demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.demo_btn.clicked.connect(self.show_demo_data)
        self.demo_btn.hide()  # Hidden by default
        header_layout.addWidget(self.demo_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_network_groups)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Network Groups list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Search and filters
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Network Groups...")
        self.search_input.textChanged.connect(self.filter_network_groups)
        search_layout.addWidget(self.search_input)
        
        left_layout.addLayout(search_layout)
        
        # Network Groups scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_widget)
        left_layout.addWidget(self.scroll_area)
        
        # Status label
        self.status_label = QLabel("No Network Groups found")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #6b7280;
            font-size: 14px;
            padding: 40px;
        """)
        left_layout.addWidget(self.status_label)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Topology view
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        topology_title = QLabel("Network Topology")
        topology_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 10px;
        """)
        right_layout.addWidget(topology_title)
        
        self.topology_view = NetworkTopologyView()
        right_layout.addWidget(self.topology_view)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        # Initially hide status label
        self.status_label.hide()
    
    def setup_refresh_timer(self):
        """Setup auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_network_groups)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_network_groups(self):
        """Refresh Network Groups data."""
        if not self.current_org_id:
            self.logger.warning("No organization selected for Network Groups refresh")
            return
        
        self.logger.info(f"Refreshing Network Groups for org: {self.current_org_id}")
        self._refresh_network_groups_async()
    
    def _refresh_network_groups_async(self):
        """Refresh Network Groups asynchronously."""
        
        class NetworkGroupsLoader(QObject):
            data_loaded = Signal(list)  # network_groups
            error_occurred = Signal(str)
            
            def __init__(self, api_client, org_id, logger):
                super().__init__()
                self.api_client = api_client
                self.org_id = org_id
                self.logger = logger
                self._should_stop = False
            
            def stop(self):
                """Signal the worker to stop."""
                self._should_stop = True
            
            def load_data(self):
                """Load Network Groups data."""
                import asyncio
                
                async def fetch_network_groups():
                    if self._should_stop:
                        return
                        
                    try:
                        # Create new API client instance for this thread
                        from clever_desktop.api.client import CleverCloudClient
                        from clever_desktop.api.token_auth import CleverCloudTokenAuth
                        
                        # Create isolated API client for this thread
                        auth_manager = CleverCloudTokenAuth()
                        client = CleverCloudClient(auth_manager)
                        
                        # Copy authentication from main client - try multiple approaches
                        if hasattr(self.api_client, 'auth') and hasattr(self.api_client.auth, 'api_token'):
                            client.auth.api_token = self.api_client.auth.api_token
                        elif hasattr(self.api_client, 'api_token'):
                            client.api_token = self.api_client.api_token
                        
                        self.logger.info(f"Loading Network Groups from API for org: {self.org_id}")
                        
                        if self._should_stop:
                            await client.close()
                            return
                        
                        network_groups = await client.get_network_groups(self.org_id)
                        
                        if self._should_stop:
                            await client.close()
                            return
                        
                        # Members should already be included in the Network Groups response
                        # If not, we'll add them as empty arrays for now
                        for ng in network_groups:
                            if self._should_stop:
                                break
                            if 'members' not in ng:
                                ng['members'] = []
                            self.logger.info(f"Network Group {ng.get('name', ng.get('id'))}: {len(ng.get('members', []))} members")
                        
                        await client.close()
                        
                        if not self._should_stop:
                            self.logger.info(f"Loaded {len(network_groups)} Network Groups from API")
                            self.data_loaded.emit(network_groups)
                        
                    except Exception as e:
                        if self._should_stop:
                            return
                            
                        error_msg = str(e)
                        self.logger.error(f"Failed to load Network Groups: {e}")
                        
                        # More specific error detection
                        if "400 Bad Request" in error_msg or "400" in error_msg:
                            if "authorization Required" in error_msg:
                                self.error_occurred.emit("Authentication error: Network Groups access requires proper authorization.")
                            else:
                                self.error_occurred.emit("Network Groups feature is not available for this organization or may require a specific plan.")
                        elif "403" in error_msg:
                            self.error_occurred.emit("Access denied: You don't have permission to view Network Groups for this organization.")
                        elif "404" in error_msg:
                            self.error_occurred.emit("Network Groups endpoint not found. This feature may not be available.")
                        else:
                            self.error_occurred.emit(error_msg)
                
                # Create new event loop for this thread
                try:
                    if self._should_stop:
                        return
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(fetch_network_groups())
                except Exception as e:
                    if not self._should_stop:
                        self.logger.error(f"Network Groups loading failed: {e}")
                        self.error_occurred.emit(str(e))
                finally:
                    try:
                        if 'loop' in locals():
                            loop.close()
                    except:
                        pass
        
        # Create and start loader thread with better cleanup
        if hasattr(self, 'loader_thread') and self.loader_thread is not None:
            try:
                if self.loader_thread.isRunning():
                    self.logger.info("Stopping existing Network Groups thread")
                    
                    # Signal the worker to stop
                    if hasattr(self, 'loader') and hasattr(self.loader, 'stop'):
                        self.loader.stop()
                    
                    # Try graceful shutdown first
                    self.loader_thread.quit()
                    if not self.loader_thread.wait(2000):  # Wait up to 2 seconds
                        self.logger.warning("Network Groups thread did not stop gracefully, terminating")
                        self.loader_thread.terminate()
                        if not self.loader_thread.wait(1000):  # Wait up to 1 second for termination
                            self.logger.error("Network Groups thread could not be terminated")
            except RuntimeError as e:
                # Thread object was already deleted
                self.logger.warning(f"Thread object already deleted: {e}")
                self.loader_thread = None
        
        self.loader_thread = QThread()
        self.loader = NetworkGroupsLoader(self.api_client, self.current_org_id, self.logger)
        self.loader.moveToThread(self.loader_thread)
        
        # Connect signals
        self.loader.data_loaded.connect(self._on_network_groups_loaded)
        self.loader.error_occurred.connect(self._on_network_groups_error)
        self.loader_thread.started.connect(self.loader.load_data)
        
        # Ensure proper cleanup when thread finishes
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)
        
        # Start thread
        self.loader_thread.start()
    
    def _on_network_groups_loaded(self, network_groups: list):
        """Handle loaded Network Groups data."""
        self.network_groups = network_groups
        self.filtered_network_groups = network_groups.copy()
        
        self.logger.info(f"Network Groups loading completed: {len(network_groups)} Network Groups")
        
        # Update display
        self.update_network_groups_display()
        
        # Clean up thread
        if hasattr(self, 'loader_thread'):
            self.loader_thread.quit()
            self.loader_thread.wait()
    
    def _on_network_groups_error(self, error: str):
        """Handle Network Groups loading error."""
        self.logger.error(f"Network Groups loading failed: {error}")
        
        # Clear any existing network groups
        self.network_groups = []
        self.filtered_network_groups = []
        
        # Show appropriate error message
        if "not available" in error.lower() or "400 Bad Request" in error:
            # Feature not available - show helpful message with demo option
            self.status_label.setText("""
🌐 Network Groups Feature

Network Groups are not available for this organization.

This feature may require:
• A specific Clever Cloud plan
• Feature enablement by Clever Cloud support
• Organization-level permissions

Contact Clever Cloud support for more information about enabling Network Groups.

Click "Demo Mode" below to see how Network Groups would work!
            """.strip())
            
            # Show demo button and hide create button
            self.create_btn.hide()
            self.demo_btn.show()
            self.demo_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
        else:
            # Other error - show technical details
            self.status_label.setText(f"Failed to load Network Groups: {error}")
            self.create_btn.hide()
            self.demo_btn.show()
        
        self.status_label.show()
        
        # Update display to show empty state
        self.update_network_groups_display()
        
        # Clean up thread
        if hasattr(self, 'loader_thread'):
            self.loader_thread.quit()
            self.loader_thread.wait()
    
    def set_organization(self, org_id: str):
        """Set current organization and refresh data."""
        self.logger.info(f"Network Groups page: Organization changed to {org_id}")
        self.current_org_id = org_id
        
        # Cancel any running threads first
        if hasattr(self, 'loader_thread') and self.loader_thread is not None:
            try:
                if self.loader_thread.isRunning():
                    self.logger.info("Cancelling existing Network Groups loading thread")
                    
                    # Signal the worker to stop
                    if hasattr(self, 'loader') and hasattr(self.loader, 'stop'):
                        self.loader.stop()
                    
                    self.loader_thread.quit()
                    self.loader_thread.wait(3000)  # Wait up to 3 seconds
                    if self.loader_thread.isRunning():
                        self.logger.warning("Network Groups thread did not stop gracefully, terminating")
                        self.loader_thread.terminate()
                        self.loader_thread.wait(1000)
            except RuntimeError as e:
                # Thread object was already deleted
                self.logger.warning(f"Thread cancellation - object already deleted: {e}")
                self.loader_thread = None
        
        self.refresh_network_groups()
    
    def filter_network_groups(self):
        """Filter Network Groups based on search input."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.filtered_network_groups = self.network_groups.copy()
        else:
            self.filtered_network_groups = [
                ng for ng in self.network_groups
                if search_text in ng.get('name', '').lower() or
                   search_text in ng.get('description', '').lower()
            ]
        
        self.update_network_groups_display()
    
    def update_network_groups_display(self):
        """Update the Network Groups display."""
        # Clear existing cards
        for i in reversed(range(self.scroll_layout.count() - 1)):  # Keep the stretch
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        if not self.filtered_network_groups:
            self.status_label.setText("No Network Groups found" if not self.network_groups else "No Network Groups match your search")
            self.status_label.show()
            return
        
        self.status_label.hide()
        
        # Add Network Group cards
        for ng in self.filtered_network_groups:
            card = NetworkGroupCard(ng)
            card.action_requested.connect(self.handle_ng_action)
            card.view_topology_requested.connect(self.view_topology)
            
            # Insert before the stretch
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)
    
    def handle_ng_action(self, action: str, ng_id: str):
        """Handle Network Group actions."""
        self.logger.info(f"Network Group action: {action} for {ng_id}")
        
        if action == 'members':
            self.manage_members(ng_id)
        elif action == 'add_peer':
            self.add_external_peer(ng_id)
        elif action == 'configure':
            self.configure_network_group(ng_id)
        elif action == 'delete':
            self.delete_network_group(ng_id)
    
    def view_topology(self, ng_id: str):
        """View Network Group topology."""
        ng_data = next((ng for ng in self.network_groups if ng['id'] == ng_id), None)
        if ng_data:
            self.topology_view.load_network_group(ng_data)
            self.logger.info(f"Viewing topology for Network Group: {ng_data.get('name', ng_id)}")
    
    def create_network_group(self):
        """Create new Network Group."""
        if not self.current_org_id:
            QMessageBox.warning(self, "No Organization", "Please select an organization first.")
            return
        
        dialog = NetworkGroupCreationDialog(self.api_client, self.current_org_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_network_groups()
    
    def manage_members(self, ng_id: str):
        """Manage Network Group members."""
        self.logger.info(f"Manage members for Network Group: {ng_id}")
        # TODO: Implement members management dialog
        QMessageBox.information(self, "Members Management", f"Members management for {ng_id} - Coming soon!")
    
    def add_external_peer(self, ng_id: str):
        """Add external peer to Network Group."""
        self.logger.info(f"Add external peer to Network Group: {ng_id}")
        # TODO: Implement external peer creation dialog
        QMessageBox.information(self, "Add External Peer", f"External peer creation for {ng_id} - Coming soon!")
    
    def configure_network_group(self, ng_id: str):
        """Configure Network Group."""
        self.logger.info(f"Configure Network Group: {ng_id}")
        # TODO: Implement configuration dialog
        QMessageBox.information(self, "Configure", f"Configuration for {ng_id} - Coming soon!")
    
    def delete_network_group(self, ng_id: str):
        """Delete Network Group."""
        ng_data = next((ng for ng in self.network_groups if ng['id'] == ng_id), None)
        if not ng_data:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Network Group",
            f"Are you sure you want to delete '{ng_data.get('name', ng_id)}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info(f"Delete Network Group: {ng_id}")
            # TODO: Implement actual deletion
            QMessageBox.information(self, "Delete", f"Deletion of {ng_id} - Coming soon!")
    
    def show_demo_data(self):
        """Show demo Network Groups data."""
        self.logger.info("Showing Network Groups demo data")
        
        # Show demo mode notification
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Demo Mode Activated")
        msg.setText("🎭 Demo Mode: Network Groups")
        msg.setInformativeText("""
You are now viewing sample Network Groups data to demonstrate the functionality.

This demo shows:
• Network Group cards with status and member counts
• Interactive topology visualization
• Member management interface
• External peer connections

All data shown is simulated and not connected to real Clever Cloud resources.
        """.strip())
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
        # Create sample Network Groups data
        demo_data = [
            {
                "id": "ng_demo_1",
                "name": "🏭 Production Network",
                "description": "Main production environment with secure database access and load balancing",
                "status": "active",
                "creationDate": 1640995200,  # 2022-01-01
                "members": [
                    {"id": "app_1", "name": "Web Frontend", "type": "application"},
                    {"id": "app_2", "name": "API Backend", "type": "application"},
                    {"id": "app_3", "name": "Worker Service", "type": "application"},
                    {"id": "addon_1", "name": "PostgreSQL DB", "type": "addon"},
                    {"id": "addon_2", "name": "Redis Cache", "type": "addon"}
                ],
                "externalPeers": [
                    {"id": "peer_1", "peerLabel": "Office VPN Gateway", "status": "connected"},
                    {"id": "peer_2", "peerLabel": "CDN Provider", "status": "connected"},
                    {"id": "peer_3", "peerLabel": "Payment Gateway", "status": "connected"}
                ]
            },
            {
                "id": "ng_demo_2", 
                "name": "🧪 Development Network",
                "description": "Development and testing environment with CI/CD integration",
                "status": "active",
                "creationDate": 1641081600,  # 2022-01-02
                "members": [
                    {"id": "app_4", "name": "Dev API", "type": "application"},
                    {"id": "app_5", "name": "Test Runner", "type": "application"},
                    {"id": "addon_3", "name": "Dev Database", "type": "addon"},
                    {"id": "addon_4", "name": "Message Queue", "type": "addon"}
                ],
                "externalPeers": [
                    {"id": "peer_4", "peerLabel": "CI/CD Server", "status": "connected"},
                    {"id": "peer_5", "peerLabel": "Developer Laptops", "status": "connected"}
                ]
            },
            {
                "id": "ng_demo_3",
                "name": "📊 Monitoring Network", 
                "description": "Isolated monitoring and logging infrastructure with alerting",
                "status": "active",
                "creationDate": 1641168000,  # 2022-01-03
                "members": [
                    {"id": "app_6", "name": "Grafana Dashboard", "type": "application"},
                    {"id": "app_7", "name": "Prometheus", "type": "application"},
                    {"id": "app_8", "name": "AlertManager", "type": "application"},
                    {"id": "addon_5", "name": "InfluxDB", "type": "addon"},
                    {"id": "addon_6", "name": "Elasticsearch", "type": "addon"}
                ],
                "externalPeers": [
                    {"id": "peer_6", "peerLabel": "External Metrics", "status": "connected"}
                ]
            },
            {
                "id": "ng_demo_4",
                "name": "🔒 Security Network",
                "description": "Dedicated security services and authentication infrastructure",
                "status": "active", 
                "creationDate": 1641254400,  # 2022-01-04
                "members": [
                    {"id": "app_9", "name": "Auth Service", "type": "application"},
                    {"id": "app_10", "name": "API Gateway", "type": "application"},
                    {"id": "addon_7", "name": "Vault", "type": "addon"}
                ],
                "externalPeers": [
                    {"id": "peer_7", "peerLabel": "Identity Provider", "status": "connected"},
                    {"id": "peer_8", "peerLabel": "Security Scanner", "status": "connected"}
                ]
            }
        ]
        
        # Load demo data
        self.network_groups = demo_data
        self.filtered_network_groups = demo_data.copy()
        
        # Hide status label and show demo data
        self.status_label.hide()
        
        # Show create button in demo mode (but it will show demo dialog)
        self.create_btn.show()
        self.demo_btn.hide()
        
        # Update display
        self.update_network_groups_display()
        
        # Show the first Network Group in topology view
        if demo_data:
            self.view_topology(demo_data[0]["id"])
            
        # Update window title to indicate demo mode
        if hasattr(self.parent(), 'setWindowTitle'):
            original_title = self.parent().windowTitle()
            if "Demo Mode" not in original_title:
                self.parent().setWindowTitle(f"{original_title} - 🎭 Demo Mode")
        
        self.logger.info(f"Demo mode activated with {len(demo_data)} sample Network Groups")
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Refresh data when page is shown
        if self.current_org_id and not self.network_groups:
            QTimer.singleShot(100, self.refresh_network_groups)
    
    def closeEvent(self, event):
        """Handle close event - cleanup threads."""
        self.cleanup_threads()
        super().closeEvent(event)
    
    def cleanup_threads(self):
        """Clean up any running threads."""
        if hasattr(self, 'loader_thread') and self.loader_thread is not None:
            try:
                if self.loader_thread.isRunning():
                    self.logger.info("Cleaning up Network Groups threads on close")
                    
                    # Signal the worker to stop
                    if hasattr(self, 'loader') and hasattr(self.loader, 'stop'):
                        self.loader.stop()
                    
                    # Force immediate termination on close
                    self.loader_thread.terminate()
                    self.loader_thread.wait(500)  # Short wait on close
            except RuntimeError as e:
                # Thread object was already deleted
                self.logger.warning(f"Thread cleanup - object already deleted: {e}")
            finally:
                self.loader_thread = None 