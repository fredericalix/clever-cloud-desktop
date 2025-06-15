"""
Login Dialog

Authentication dialog for user login.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt


class LoginDialog(QDialog):
    """Login dialog for authentication."""
    
    def __init__(self, parent=None, api_client=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Login to Clever Cloud")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Clever Cloud Authentication")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Message
        message = QLabel("Authentication will be implemented here.\n\nThis will include OAuth2 flow and token management.")
        message.setStyleSheet("margin: 20px; color: #666;")
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login (Mock)")
        login_btn.clicked.connect(self.accept)
        button_layout.addWidget(login_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout) 