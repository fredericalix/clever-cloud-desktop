"""
Dashboard Panel

Main dashboard showing overview and quick actions.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class Dashboard(QWidget):
    """Dashboard panel widget."""
    
    def __init__(self, parent=None, api_client=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        content = QLabel("Welcome to Clever Cloud Desktop Manager!\n\nThis is the dashboard where you'll see an overview of your applications, add-ons, and recent activity.")
        content.setStyleSheet("margin: 20px; color: #666;")
        layout.addWidget(content)
        
        layout.addStretch()
    
    def refresh(self):
        """Refresh dashboard data."""
        pass 