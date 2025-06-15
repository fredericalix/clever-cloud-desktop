"""
Splash Screen

Simple splash screen for application startup.
"""

from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont


class SplashScreen(QSplashScreen):
    """Application splash screen."""
    
    def __init__(self):
        # Create a simple pixmap for the splash screen
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.GlobalColor.white)
        
        super().__init__(pixmap)
        
        # Create content widget
        self.content_widget = QWidget(self)
        self.content_widget.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self.content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo/Title
        title_label = QLabel("🚀 Clever Cloud Desktop")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #333;
            }
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007ACC;
                border-radius: 3px;
            }
        """)
    
    def update_progress(self, value: int, message: str = ""):
        """Update progress bar and status message."""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
        self.repaint()  # Force immediate update 