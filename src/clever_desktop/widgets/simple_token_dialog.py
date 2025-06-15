"""
Simple API Token Input Dialog

Simplified dialog for debugging token input issues.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class SimpleTokenDialog(QDialog):
    """Simplified dialog for API token input."""
    
    token_entered = Signal(str)  # token
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Setup dialog
        self.setWindowTitle("Enter API Token")
        self.setModal(True)
        self.resize(400, 200)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Enter your Clever Cloud API Token")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel("Go to console.clever-cloud.com/users/me/tokens to create a token")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Token input
        token_label = QLabel("API Token:")
        layout.addWidget(token_label)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste your API token here...")
        self.token_input.textChanged.connect(self._on_token_changed)
        layout.addWidget(self.token_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("Use Token")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setEnabled(False)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def _on_token_changed(self, text: str):
        """Handle token input change."""
        self.ok_button.setEnabled(len(text.strip()) > 0)
    
    def _on_ok_clicked(self):
        """Handle OK button click."""
        token = self.token_input.text().strip()
        if token:
            self.logger.info(f"Token entered: {token[:10]}...")
            self.token_entered.emit(token)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please enter a token")
    
    def get_token(self) -> str:
        """Get the entered token."""
        return self.token_input.text().strip() 