"""
Resources Module

Handles application resources like icons, images, and other assets.
"""

import os
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize


def get_resource_path(filename: str) -> Path:
    """Get the full path to a resource file."""
    resources_dir = Path(__file__).parent
    return resources_dir / filename


def load_icon(filename: str, size: QSize = None) -> QIcon:
    """Load an icon from the resources directory."""
    icon_path = get_resource_path(filename)
    
    if not icon_path.exists():
        # Return empty icon if file doesn't exist
        return QIcon()
    
    if filename.endswith('.svg'):
        # Handle SVG icons
        renderer = QSvgRenderer(str(icon_path))
        if size is None:
            size = QSize(64, 64)
        
        pixmap = QPixmap(size)
        pixmap.fill()  # Fill with transparent
        
        from PySide6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    else:
        # Handle regular image files
        icon = QIcon(str(icon_path))
        return icon


def get_app_icon() -> QIcon:
    """Get the main application icon."""
    return load_icon("icon.svg")


def get_tray_icon() -> QIcon:
    """Get the system tray icon."""
    return load_icon("icon.svg", QSize(22, 22)) 