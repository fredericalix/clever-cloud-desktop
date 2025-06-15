"""
API Token Input Dialog

Dialog for users to input their Clever Cloud API token.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class TokenInputDialog(QDialog):
    """Dialog for API token input."""
    
    token_entered = Signal(str)  # token
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Setup dialog
        self.setWindowTitle("Clever Cloud API Token")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(500, 400)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header section
        header_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("API Token Required")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Enter your Clever Cloud API token")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; font-size: 14px;")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Instructions section
        instructions_frame = QFrame()
        instructions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        instructions_layout = QVBoxLayout(instructions_frame)
        
        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(120)
        instructions_text.setHtml("""
        <p><b>How to get your API token:</b></p>
        <ol>
        <li>Go to <a href="https://console.clever-cloud.com/users/me/tokens">Clever Cloud Console</a></li>
        <li>Click "Create a token"</li>
        <li>Give it a name (e.g., "Desktop Manager")</li>
        <li>Copy the token and paste it below</li>
        </ol>
        """)
        instructions_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_frame)
        
        # Token input section
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        
        token_label = QLabel("API Token:")
        token_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        input_layout.addWidget(token_label)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste your API token here...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.textChanged.connect(self._on_token_changed)
        input_layout.addWidget(self.token_input)
        
        # Show/hide token button
        self.show_token_button = QPushButton("👁 Show Token")
        self.show_token_button.setCheckable(True)
        self.show_token_button.clicked.connect(self._toggle_token_visibility)
        input_layout.addWidget(self.show_token_button)
        
        layout.addWidget(input_frame)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Button section
        button_layout = QHBoxLayout()
        
        self.open_console_button = QPushButton("🌐 Open Console")
        self.open_console_button.clicked.connect(self._open_console)
        button_layout.addWidget(self.open_console_button)
        
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("✓ Use Token")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def setup_styles(self):
        """Setup custom styles for the dialog."""
        self.setStyleSheet("""
        QDialog {
            background-color: #fafafa;
        }
        
        QFrame {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }
        
        QPushButton {
            background-color: #007ACC;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 13px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background-color: #005a9e;
        }
        
        QPushButton:pressed {
            background-color: #004785;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QPushButton#cancel_button, QPushButton#open_console_button {
            background-color: transparent;
            color: #666;
            border: 1px solid #ccc;
        }
        
        QPushButton#cancel_button:hover, QPushButton#open_console_button:hover {
            background-color: #f5f5f5;
        }
        
        QLineEdit {
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            padding: 10px;
            font-size: 14px;
            font-family: monospace;
        }
        
        QLineEdit:focus {
            border-color: #007ACC;
        }
        
        QTextEdit {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 10px;
            background-color: #f9f9f9;
            font-size: 13px;
        }
        
        QLabel {
            color: #333;
        }
        """)
    
    def _on_token_changed(self, text: str):
        """Handle token input change."""
        # Enable OK button only if token is not empty
        self.ok_button.setEnabled(len(text.strip()) > 0)
    
    def _toggle_token_visibility(self, checked: bool):
        """Toggle token visibility."""
        if checked:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_token_button.setText("🙈 Hide Token")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_token_button.setText("👁 Show Token")
    
    def _open_console(self):
        """Open Clever Cloud console in browser."""
        import webbrowser
        webbrowser.open("https://console.clever-cloud.com/users/me/tokens")
    
    def _on_ok_clicked(self):
        """Handle OK button click."""
        token = self.token_input.text().strip()
        if token:
            self.token_entered.emit(token)
            self.accept()
    
    def get_token(self) -> str:
        """Get the entered token."""
        return self.token_input.text().strip() 