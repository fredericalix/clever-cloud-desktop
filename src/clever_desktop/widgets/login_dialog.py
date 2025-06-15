"""
Login Dialog

Modern login dialog for Clever Cloud authentication with OAuth2 support.
"""

import asyncio
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QCheckBox, QFrame, QWidget,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import QTimer, Signal, QThread, QObject
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

from ..api.client import CleverCloudClient
from ..api.auth import OAuth2Error


class AuthWorker(QObject):
    """Worker thread for OAuth2 authentication."""
    
    authentication_success = Signal(dict)  # user_info
    authentication_failed = Signal(str)    # error_message
    check_stored_auth_result = Signal(bool)  # success
    
    def __init__(self, client: CleverCloudClient):
        super().__init__()
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    def check_stored_authentication(self):
        """Check if stored authentication is available and valid."""
        try:
            # Run async function in this thread's event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.client.authenticate_with_stored_credentials())
            self.check_stored_auth_result.emit(result)
            
            if result:
                user_info = self.client.auth.user_info or {}
                self.authentication_success.emit(user_info)
            
            loop.close()
            
        except Exception as e:
            self.logger.error(f"Error checking stored authentication: {e}")
            self.check_stored_auth_result.emit(False)
    
    def start_oauth_authentication(self):
        """Start OAuth2 authentication flow."""
        try:
            # Run async function in this thread's event loop  
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Connect signals from auth manager
            self.client.auth.authentication_success.connect(self.authentication_success.emit)
            self.client.auth.authentication_failed.connect(self.authentication_failed.emit)
            
            # Start authentication
            loop.run_until_complete(self.client.auth.authenticate())
            
            loop.close()
            
        except Exception as e:
            self.logger.error(f"OAuth authentication error: {e}")
            self.authentication_failed.emit(str(e))


class LoginDialog(QDialog):
    """Modern login dialog for Clever Cloud authentication."""
    
    authentication_success = Signal(dict)  # user_info
    
    def __init__(self, client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.logger = logging.getLogger(__name__)
        
        # Setup dialog
        self.setWindowTitle("Clever Cloud Authentication")
        self.setModal(True)
        self.setFixedSize(450, 600)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
        # Auth worker in separate thread
        self.auth_worker = AuthWorker(self.client)
        self.auth_thread = QThread()
        self.auth_worker.moveToThread(self.auth_thread)
        
        # Connect worker signals
        self.auth_worker.authentication_success.connect(self._on_authentication_success)
        self.auth_worker.authentication_failed.connect(self._on_authentication_failed)
        self.auth_worker.check_stored_auth_result.connect(self._on_stored_auth_checked)
        
        # Connect auth manager signals
        self.client.auth.token_input_required.connect(self._on_token_input_required)
        
        # Connect thread signals
        self.auth_thread.started.connect(self.auth_worker.check_stored_authentication)
        
        self.setup_ui()
        self.setup_styles()
        
        # Auto-check for stored credentials
        QTimer.singleShot(500, self._check_stored_credentials)
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Header section
        header_layout = QVBoxLayout()
        
        # Logo placeholder (you can add actual logo later)
        logo_label = QLabel("🚀")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_font = QFont()
        logo_font.setPointSize(48)
        logo_label.setFont(logo_font)
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("Clever Cloud Desktop")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Connect your Clever Cloud account")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; font-size: 14px;")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Status section
        self.status_frame = QFrame()
        self.status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(self.status_frame)
        
        self.status_label = QLabel("Checking for saved credentials...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.status_frame)
        
        # Login options section
        self.login_frame = QFrame()
        login_layout = QVBoxLayout(self.login_frame)
        
        # OAuth2 login button
        self.oauth_button = QPushButton("🔐 Login with Clever Cloud")
        self.oauth_button.clicked.connect(self._start_oauth_login)
        self.oauth_button.setMinimumHeight(50)
        login_layout.addWidget(self.oauth_button)
        
        # Info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setHtml("""
        <p><b>Secure OAuth2 Authentication</b></p>
        <ul>
        <li>Your credentials are never stored by this application</li>
        <li>Authentication uses Clever Cloud's secure OAuth2 flow</li>
        <li>Tokens are securely stored in your system keychain</li>
        </ul>
        """)
        login_layout.addWidget(info_text)
        
        # Remember login checkbox
        self.remember_checkbox = QCheckBox("Remember this login")
        self.remember_checkbox.setChecked(True)
        login_layout.addWidget(self.remember_checkbox)
        
        layout.addWidget(self.login_frame)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Footer buttons
        button_layout = QHBoxLayout()
        
        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self._show_help)
        button_layout.addWidget(self.help_button)
        
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initially hide login frame
        self.login_frame.hide()
    
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
            padding: 20px;
        }
        
        QPushButton {
            background-color: #007ACC;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 14px;
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
        
        #help_button, #cancel_button {
            background-color: transparent;
            color: #666;
            border: 1px solid #ccc;
        }
        
        #help_button:hover, #cancel_button:hover {
            background-color: #f5f5f5;
        }
        
        QProgressBar {
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }
        
        QProgressBar::chunk {
            background-color: #007ACC;
            border-radius: 3px;
        }
        
        QTextEdit {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 10px;
            background-color: #f9f9f9;
            font-size: 13px;
        }
        
        QCheckBox {
            font-size: 13px;
            color: #333;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        
        QCheckBox::indicator:unchecked {
            border: 2px solid #ccc;
            border-radius: 3px;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            border: 2px solid #007ACC;
            border-radius: 3px;
            background-color: #007ACC;
            image: url(:/icons/check.png);
        }
        """)
        
        # Set object names for styling
        self.help_button.setObjectName("help_button")
        self.cancel_button.setObjectName("cancel_button")
    
    def _check_stored_credentials(self):
        """Check for stored credentials."""
        if self.client.has_stored_credentials():
            self.status_label.setText("Found saved credentials, verifying...")
            self.auth_thread.start()
        else:
            self._show_login_options()
    
    def _on_stored_auth_checked(self, success: bool):
        """Handle result of stored authentication check."""
        self.auth_thread.quit()
        self.auth_thread.wait()
        
        if not success:
            self._show_login_options()
    
    def _show_login_options(self):
        """Show login options to user."""
        self.status_frame.hide()
        self.login_frame.show()
        self.oauth_button.setFocus()
    
    def _start_oauth_login(self):
        """Start OAuth2 authentication flow."""
        self.oauth_button.setEnabled(False)
        self.oauth_button.setText("🔄 Opening browser...")
        
        self.status_label.setText("Please complete authentication in your browser...")
        self.status_frame.show()
        self.login_frame.hide()
        
        # Start OAuth in worker thread
        self.auth_thread = QThread()
        self.auth_worker = AuthWorker(self.client)
        self.auth_worker.moveToThread(self.auth_thread)
        
        self.auth_worker.authentication_success.connect(self._on_authentication_success)
        self.auth_worker.authentication_failed.connect(self._on_authentication_failed)
        self.auth_thread.started.connect(self.auth_worker.start_oauth_authentication)
        
        self.auth_thread.start()
    
    def _on_authentication_success(self, user_info: dict):
        """Handle successful authentication."""
        self.auth_thread.quit()
        self.auth_thread.wait()
        
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        
        user_name = user_info.get('name', 'Unknown User')
        self.status_label.setText(f"✅ Welcome back, {user_name}!")
        
        self.logger.info(f"Authentication successful for user: {user_name}")
        
        # Emit success and close dialog
        QTimer.singleShot(1500, lambda: (
            self.authentication_success.emit(user_info),
            self.accept()
        ))
    
    def _on_authentication_failed(self, error_message: str):
        """Handle authentication failure."""
        self.auth_thread.quit()
        self.auth_thread.wait()
        
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        
        self.status_label.setText(f"❌ Authentication failed: {error_message}")
        
        self.logger.error(f"Authentication failed: {error_message}")
        
        # Reset and show login options again
        QTimer.singleShot(3000, self._reset_dialog)
    
    def _reset_dialog(self):
        """Reset dialog to initial state."""
        self.oauth_button.setEnabled(True)
        self.oauth_button.setText("🔐 Login with Clever Cloud")
        
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Ready to authenticate...")
        
        self._show_login_options()
    
    def _on_token_input_required(self):
        """Handle token input request from auth manager."""
        self.logger.info("Token input required, showing simple token dialog")
        
        from .simple_token_dialog import SimpleTokenDialog
        
        dialog = SimpleTokenDialog(self)
        dialog.token_entered.connect(self.client.auth.store_token)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.logger.info("Token entered by user")
        else:
            self.logger.info("Token input cancelled by user")
            self.client.auth.authentication_failed.emit("Authentication cancelled by user")
    
    def _show_help(self):
        """Show help information."""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.information(
            self,
            "Authentication Help",
            """
            <h3>How to authenticate with Clever Cloud:</h3>
            
            <p><b>1. Click "Login with Clever Cloud"</b><br>
            This will show a dialog to enter your API token.</p>
            
            <p><b>2. Get your API token</b><br>
            Go to the Clever Cloud console and create an API token.</p>
            
            <p><b>3. Enter your token</b><br>
            Paste the token in the dialog that appears.</p>
            
            <p><b>4. Start using the application</b><br>
            Your token will be securely stored for future use.</p>
            
            <hr>
            
            <p><b>Troubleshooting:</b></p>
            <ul>
            <li>Make sure you have a valid Clever Cloud account</li>
            <li>Check your internet connection</li>
            <li>Verify your API token is correct</li>
            </ul>
            
            <p>Need more help? Visit the <a href="https://www.clever-cloud.com/doc/">Clever Cloud documentation</a>.</p>
            """
        )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.auth_thread.isRunning():
            self.auth_thread.quit()
            self.auth_thread.wait()
        event.accept() 