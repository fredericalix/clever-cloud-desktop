"""
Add-ons Panel

Panel for managing Clever Cloud add-ons.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class AddonsPanel(QWidget):
    """Add-ons management panel."""
    
    def __init__(self, parent=None, api_client=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Add-ons")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        content = QLabel("Add-on management will be implemented here.\n\nYou'll be able to:\n- View all add-ons (PostgreSQL, Redis, MongoDB, etc.)\n- Create new add-ons\n- Configure and monitor add-ons\n- Manage backups and connections")
        content.setStyleSheet("margin: 20px; color: #666;")
        layout.addWidget(content)
        
        layout.addStretch()
    
    def refresh(self):
        """Refresh add-ons data."""
        pass 