"""
Sidebar Navigation

Navigation sidebar with page selection and modern design.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Signal


class Sidebar(QWidget):
    """Sidebar navigation widget."""
    
    page_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = "dashboard"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Logo/Title
        title = QLabel("Clever Desktop")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Navigation buttons
        self.buttons = {}
        pages = [
            ("dashboard", "Dashboard"),
            ("applications", "Applications"),
            ("addons", "Add-ons"),
            ("network_groups", "Network Groups"),
            ("logs", "Logs"),
            ("settings", "Settings"),
        ]
        
        for page_id, title in pages:
            btn = QPushButton(title)
            btn.clicked.connect(lambda checked, p=page_id: self._on_page_clicked(p))
            self.buttons[page_id] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        self.set_active_page("dashboard")
    
    def _on_page_clicked(self, page_id):
        self.page_changed.emit(page_id)
    
    def set_active_page(self, page_id):
        # Reset all buttons
        for btn in self.buttons.values():
            btn.setStyleSheet("")
        
        # Highlight active button
        if page_id in self.buttons:
            self.buttons[page_id].setStyleSheet("background-color: #0066cc; color: white;")
            self.current_page = page_id 