"""
Applications Management Page

Page for managing Clever Cloud applications with list view, details, and actions.
"""

import logging
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QGroupBox, QProgressBar, QMenu, QMessageBox,
    QSplitter, QTextEdit, QTabWidget, QDialog, QFormLayout, QCheckBox,
    QFileDialog, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QPalette, QAction, QPixmap

from ..api.client import CleverCloudClient


class ApplicationCard(QFrame):
    """Application card widget for grid view."""
    
    # Signals
    application_selected = Signal(dict)  # application_data
    action_requested = Signal(str, dict)  # action, application_data
    
    def __init__(self, app_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with name and status
        header_layout = QHBoxLayout()
        
        # App name
        name = self.app_data.get('name', 'Unknown App')
        self.name_label = QLabel(name)
        self.name_label.setObjectName("appName")
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        # Status indicator
        state = self.app_data.get('state', 'UNKNOWN')
        status_color = self.get_status_color(state)
        self.status_label = QLabel(state)
        self.status_label.setObjectName("appStatus")
        self.status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # App type and zone
        app_type = self.app_data.get('instance', {}).get('type', 'Unknown')
        zone = self.app_data.get('zone', 'Unknown')
        
        info_label = QLabel(f"📦 {app_type} • 🌍 {zone}")
        info_label.setObjectName("appInfo")
        layout.addWidget(info_label)
        
        # Description or ID
        app_id = self.app_data.get('id', '')
        desc_label = QLabel(f"ID: {app_id[:12]}...")
        desc_label.setObjectName("appDescription")
        layout.addWidget(desc_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        # View details button
        self.details_btn = QPushButton("Details")
        self.details_btn.setObjectName("detailsButton")
        self.details_btn.clicked.connect(lambda: self.application_selected.emit(self.app_data))
        buttons_layout.addWidget(self.details_btn)
        
        # Quick actions menu
        self.actions_btn = QPushButton("Actions ▼")
        self.actions_btn.setObjectName("actionsButton")
        self.setup_actions_menu()
        buttons_layout.addWidget(self.actions_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_status_color(self, state: str) -> str:
        """Get color for application state."""
        colors = {
            'RUNNING': '#28a745',
            'STOPPED': '#dc3545',
            'DEPLOYING': '#007ACC',
            'RESTARTING': '#ffc107',
            'UNKNOWN': '#6c757d'
        }
        return colors.get(state, '#6c757d')
    
    def setup_actions_menu(self):
        """Setup the actions menu."""
        menu = QMenu(self)
        
        # Common actions based on state
        state = self.app_data.get('state', 'UNKNOWN')
        
        if state == 'RUNNING':
            restart_action = QAction("🔄 Restart", self)
            restart_action.triggered.connect(lambda: self.action_requested.emit('restart', self.app_data))
            menu.addAction(restart_action)
            
            stop_action = QAction("⏹️ Stop", self)
            stop_action.triggered.connect(lambda: self.action_requested.emit('stop', self.app_data))
            menu.addAction(stop_action)
        
        elif state == 'STOPPED':
            start_action = QAction("▶️ Start", self)
            start_action.triggered.connect(lambda: self.action_requested.emit('start', self.app_data))
            menu.addAction(start_action)
        
        menu.addSeparator()
        
        # Always available actions
        logs_action = QAction("📋 View Logs", self)
        logs_action.triggered.connect(lambda: self.action_requested.emit('logs', self.app_data))
        menu.addAction(logs_action)
        
        env_action = QAction("⚙️ Environment", self)
        env_action.triggered.connect(lambda: self.action_requested.emit('environment', self.app_data))
        menu.addAction(env_action)
        
        deploy_action = QAction("🚀 Deploy", self)
        deploy_action.triggered.connect(lambda: self.action_requested.emit('deploy', self.app_data))
        menu.addAction(deploy_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self.action_requested.emit('delete', self.app_data))
        menu.addAction(delete_action)
        
        self.actions_btn.setMenu(menu)
    
    def setup_styles(self):
        """Setup card styles."""
        self.setStyleSheet("""
        ApplicationCard {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
        }
        
        ApplicationCard:hover {
            border-color: #007ACC;
        }
        
        #appName {
            font-size: 16px;
            font-weight: bold;
            color: #212529;
        }
        
        #appInfo {
            color: #6c757d;
            font-size: 14px;
        }
        
        #appDescription {
            color: #6c757d;
            font-size: 12px;
        }
        
        #detailsButton, #actionsButton {
            padding: 6px 12px;
            border: 1px solid #007ACC;
            border-radius: 4px;
            background-color: white;
            color: #007ACC;
            font-size: 12px;
        }
        
        #detailsButton:hover, #actionsButton:hover {
            background-color: #007ACC;
            color: white;
        }
        """)


class EnvironmentVariablesEditor(QWidget):
    """Environment variables editor with full CRUD operations."""
    
    # Signals
    variables_changed = Signal(dict)  # env_vars
    save_requested = Signal(dict)     # env_vars
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_app_id = None
        self.current_env_vars = {}
        self.original_env_vars = {}
        self.has_changes = False
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the environment variables editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with actions
        header_layout = QHBoxLayout()
        
        # Info label
        self.info_label = QLabel("Environment Variables")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.info_label)
        
        header_layout.addStretch()
        
        # Action buttons
        self.add_btn = QPushButton("➕ Add Variable")
        self.add_btn.clicked.connect(self.add_variable)
        header_layout.addWidget(self.add_btn)
        
        self.import_btn = QPushButton("📁 Import")
        self.import_btn.clicked.connect(self.import_variables)
        header_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.clicked.connect(self.export_variables)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Environment variables table
        self.env_table = QTableWidget()
        self.env_table.setColumnCount(4)
        self.env_table.setHorizontalHeaderLabels(["Name", "Value", "Masked", "Actions"])
        
        # Configure table
        header = self.env_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Value
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Masked
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.env_table.setAlternatingRowColors(True)
        self.env_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.env_table)
        
        # Status and save section
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("No changes")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Save/Cancel buttons
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        self.cancel_btn.setEnabled(False)
        status_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        status_layout.addWidget(self.save_btn)
        
        layout.addLayout(status_layout)
        
        # Initially show empty state
        self.show_empty_state()
    
    def show_empty_state(self):
        """Show empty state when no application is selected."""
        self.env_table.setRowCount(1)
        empty_item = QTableWidgetItem("Select an application to view environment variables")
        empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
        empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.env_table.setItem(0, 0, empty_item)
        self.env_table.setSpan(0, 0, 1, 4)
        
        # Disable controls
        self.add_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
    
    def set_application(self, app_id: str, env_vars: Dict[str, str]):
        """Set the current application and its environment variables."""
        self.logger.info(f"EnvironmentVariablesEditor.set_application called with app_id={app_id}, env_vars={env_vars}")
        
        self.current_app_id = app_id
        self.current_env_vars = env_vars.copy()
        self.original_env_vars = env_vars.copy()
        self.has_changes = False
        
        self.update_display()
        self.update_status()
        
        # Enable controls
        self.add_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        self.logger.info(f"Environment editor set for app {app_id} with {len(env_vars)} variables")
    
    def update_display(self):
        """Update the table display with current environment variables."""
        self.env_table.setRowCount(len(self.current_env_vars))
        
        for row, (name, value) in enumerate(self.current_env_vars.items()):
            # Name column
            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.env_table.setItem(row, 0, name_item)
            
            # Value column (editable)
            value_item = QTableWidgetItem(value)
            value_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            self.env_table.setItem(row, 1, value_item)
            
            # Masked checkbox
            mask_checkbox = QCheckBox()
            mask_checkbox.setChecked(self._is_sensitive_var(name))
            mask_checkbox.stateChanged.connect(lambda state, r=row: self._on_mask_changed(r, state))
            self.env_table.setCellWidget(row, 2, mask_checkbox)
            
            # Actions column
            actions_widget = self._create_actions_widget(row, name)
            self.env_table.setCellWidget(row, 3, actions_widget)
        
        # Connect item changed signal
        self.env_table.itemChanged.connect(self._on_item_changed)
    
    def _create_actions_widget(self, row: int, var_name: str) -> QWidget:
        """Create actions widget for a table row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Edit button
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit variable name")
        edit_btn.setMaximumSize(30, 25)
        edit_btn.clicked.connect(lambda: self._edit_variable_name(row, var_name))
        layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("Delete variable")
        delete_btn.setMaximumSize(30, 25)
        delete_btn.clicked.connect(lambda: self._delete_variable(row, var_name))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        return widget
    
    def _is_sensitive_var(self, name: str) -> bool:
        """Check if a variable name suggests sensitive content."""
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 'auth', 'credential',
            'private', 'pass', 'pwd', 'api_key', 'access_token'
        ]
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in sensitive_keywords)
    
    def _on_mask_changed(self, row: int, state: int):
        """Handle mask checkbox state change."""
        value_item = self.env_table.item(row, 1)
        if value_item:
            if state == Qt.CheckState.Checked.value:
                # Mask the value
                value_item.setText("••••••••")
                value_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            else:
                # Unmask the value
                name_item = self.env_table.item(row, 0)
                if name_item:
                    var_name = name_item.text()
                    actual_value = self.current_env_vars.get(var_name, "")
                    value_item.setText(actual_value)
                    value_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Handle table item changes."""
        if item.column() == 1:  # Value column
            row = item.row()
            name_item = self.env_table.item(row, 0)
            if name_item:
                var_name = name_item.text()
                new_value = item.text()
                
                # Update current env vars
                self.current_env_vars[var_name] = new_value
                self._mark_changed()
    
    def _edit_variable_name(self, row: int, old_name: str):
        """Edit a variable name."""
        from PySide6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self, 
            "Edit Variable Name", 
            "Variable name:", 
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            if new_name in self.current_env_vars:
                QMessageBox.warning(self, "Error", f"Variable '{new_name}' already exists!")
                return
            
            # Update the variable name
            value = self.current_env_vars.pop(old_name)
            self.current_env_vars[new_name] = value
            
            # Update display
            self.update_display()
            self._mark_changed()
    
    def _delete_variable(self, row: int, var_name: str):
        """Delete a variable."""
        reply = QMessageBox.question(
            self,
            "Delete Variable",
            f"Are you sure you want to delete the variable '{var_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_env_vars.pop(var_name, None)
            self.update_display()
            self._mark_changed()
    
    def add_variable(self):
        """Add a new environment variable."""
        from PySide6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Add Variable", "Variable name:")
        if not ok or not name:
            return
        
        if name in self.current_env_vars:
            QMessageBox.warning(self, "Error", f"Variable '{name}' already exists!")
            return
        
        value, ok = QInputDialog.getText(self, "Add Variable", f"Value for '{name}':")
        if ok:
            self.current_env_vars[name] = value
            self.update_display()
            self._mark_changed()
    
    def import_variables(self):
        """Import variables from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Environment Variables",
            "",
            "Environment Files (*.env);;JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            imported_vars = {}
            
            if file_path.endswith('.json'):
                import json
                with open(file_path, 'r') as f:
                    imported_vars = json.load(f)
            else:
                # Assume .env format
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            imported_vars[key.strip()] = value.strip().strip('"\'')
            
            if imported_vars:
                # Ask about conflicts
                conflicts = set(imported_vars.keys()) & set(self.current_env_vars.keys())
                if conflicts:
                    reply = QMessageBox.question(
                        self,
                        "Import Conflicts",
                        f"The following variables already exist:\n{', '.join(conflicts)}\n\nOverwrite them?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply != QMessageBox.StandardButton.Yes:
                        # Remove conflicts from import
                        for conflict in conflicts:
                            imported_vars.pop(conflict, None)
                
                # Import variables
                self.current_env_vars.update(imported_vars)
                self.update_display()
                self._mark_changed()
                
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    f"Imported {len(imported_vars)} variables."
                )
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import variables:\n{str(e)}")
    
    def export_variables(self):
        """Export variables to a file."""
        if not self.current_env_vars:
            QMessageBox.information(self, "Export", "No variables to export.")
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Environment Variables",
            "environment.env",
            "Environment Files (*.env);;JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            if selected_filter.startswith("JSON"):
                import json
                with open(file_path, 'w') as f:
                    json.dump(self.current_env_vars, f, indent=2)
            else:
                # Export as .env format
                with open(file_path, 'w') as f:
                    for key, value in self.current_env_vars.items():
                        f.write(f"{key}={value}\n")
            
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Exported {len(self.current_env_vars)} variables to {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export variables:\n{str(e)}")
    
    def _mark_changed(self):
        """Mark that changes have been made."""
        self.has_changes = True
        self.update_status()
        self.variables_changed.emit(self.current_env_vars)
    
    def update_status(self):
        """Update the status display."""
        if not self.has_changes:
            self.status_label.setText("No changes")
            self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
        else:
            changes_count = len(set(self.current_env_vars.items()) - set(self.original_env_vars.items()))
            self.status_label.setText(f"Unsaved changes ({changes_count} modified)")
            self.status_label.setStyleSheet("color: #ffc107; font-weight: bold;")
            self.save_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
    
    def save_changes(self):
        """Save the current changes."""
        if self.has_changes and self.current_app_id:
            self.save_requested.emit(self.current_env_vars)
    
    def cancel_changes(self):
        """Cancel changes and revert to original."""
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Cancel Changes",
                "Are you sure you want to discard all changes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_env_vars = self.original_env_vars.copy()
                self.has_changes = False
                self.update_display()
                self.update_status()
    
    def mark_saved(self):
        """Mark the current state as saved."""
        self.original_env_vars = self.current_env_vars.copy()
        self.has_changes = False
        self.update_status()


class ApplicationDetailsPanel(QWidget):
    """Application details panel."""
    
    # Signals
    action_requested = Signal(str, dict)  # action, application_data
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_app = None
        self.current_org_id = None
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the details panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.header_label = QLabel("Select an application to view details")
        self.header_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #212529;
            padding: 10px 0;
        """)
        layout.addWidget(self.header_label)
        
        # Tabs for different information
        self.tabs = QTabWidget()
        
        # Overview tab
        self.overview_tab = QWidget()
        self.setup_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Environment tab
        self.env_tab = QWidget()
        self.setup_environment_tab()
        self.tabs.addTab(self.env_tab, "Environment")
        
        # Logs tab
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "Logs")
        
        layout.addWidget(self.tabs)
        
        # Initially hide tabs
        self.tabs.hide()
    
    def setup_overview_tab(self):
        """Setup the overview tab."""
        layout = QVBoxLayout(self.overview_tab)
        
        # Application info
        self.info_group = QGroupBox("Application Information")
        info_layout = QGridLayout(self.info_group)
        
        # Labels for info display
        self.info_labels = {}
        info_fields = [
            ("Name", "name"),
            ("ID", "id"),
            ("State", "state"),
            ("Type", "instance_type"),
            ("Zone", "zone"),
            ("Created", "created_at"),
            ("Last Deploy", "last_deploy")
        ]
        
        for i, (label, field) in enumerate(info_fields):
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel("-")
            
            info_layout.addWidget(label_widget, i, 0)
            info_layout.addWidget(value_widget, i, 1)
            
            self.info_labels[field] = value_widget
        
        layout.addWidget(self.info_group)
        
        # Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.action_buttons = {}
        actions = [
            ("start", "▶️ Start", "#28a745"),
            ("stop", "⏹️ Stop", "#dc3545"),
            ("restart", "🔄 Restart", "#007ACC"),
            ("deploy", "🚀 Deploy", "#007ACC")
        ]
        
        for action_id, text, color in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 15px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            btn.clicked.connect(lambda checked, aid=action_id: self._on_action_clicked(aid))
            actions_layout.addWidget(btn)
            self.action_buttons[action_id] = btn
        
        layout.addWidget(actions_group)
        layout.addStretch()
    
    def setup_environment_tab(self):
        """Setup the environment variables tab with full editor."""
        layout = QVBoxLayout(self.env_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create environment variables editor
        self.env_editor = EnvironmentVariablesEditor()
        self.env_editor.save_requested.connect(self._on_env_save_requested)
        layout.addWidget(self.env_editor)
    
    def setup_logs_tab(self):
        """Setup the logs tab."""
        layout = QVBoxLayout(self.logs_tab)
        
        # Logs display
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setPlainText("Application logs will be displayed here...")
        layout.addWidget(self.logs_text)
        
        # Refresh logs button
        refresh_btn = QPushButton("🔄 Refresh Logs")
        refresh_btn.clicked.connect(self._refresh_logs)
        layout.addWidget(refresh_btn)
    
    def set_application(self, app_data: Dict[str, Any]):
        """Set the current application."""
        self.current_app = app_data
        self.update_display()
        self.tabs.show()
        
        # Load environment variables for the editor
        if hasattr(self, 'env_editor'):
            app_id = app_data.get('id', '')
            if app_id:
                self._load_environment_variables(app_id)
    
    def update_display(self):
        """Update the display with current application data."""
        if not self.current_app:
            return
        
        # Update header
        app_name = self.current_app.get('name', 'Unknown App')
        self.header_label.setText(f"Application: {app_name}")
        
        # Update info labels
        self.info_labels['name'].setText(self.current_app.get('name', '-'))
        self.info_labels['id'].setText(self.current_app.get('id', '-'))
        self.info_labels['state'].setText(self.current_app.get('state', '-'))
        self.info_labels['instance_type'].setText(
            self.current_app.get('instance', {}).get('type', '-')
        )
        self.info_labels['zone'].setText(self.current_app.get('zone', '-'))
        
        # Format dates if available
        created_at = self.current_app.get('creationDate')
        if created_at:
            if isinstance(created_at, int):
                # Convert Unix timestamp to date string
                from datetime import datetime
                try:
                    # Try as seconds first
                    if created_at > 1e10:  # If timestamp is too large, it's probably in milliseconds
                        created_at = created_at / 1000
                    date_str = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d')
                    self.info_labels['created_at'].setText(date_str)
                except (ValueError, OSError):
                    # If conversion fails, show raw value
                    self.info_labels['created_at'].setText(str(created_at))
            elif isinstance(created_at, str):
                self.info_labels['created_at'].setText(created_at[:10])  # Just date part
            else:
                self.info_labels['created_at'].setText('-')
        else:
            self.info_labels['created_at'].setText('-')
        
        # Update action buttons based on state
        state = self.current_app.get('state', 'UNKNOWN')
        self._update_action_buttons(state)
    
    def _update_action_buttons(self, state: str):
        """Update action buttons based on application state."""
        # Enable/disable buttons based on state
        if state == 'RUNNING':
            self.action_buttons['start'].setEnabled(False)
            self.action_buttons['stop'].setEnabled(True)
            self.action_buttons['restart'].setEnabled(True)
        elif state == 'STOPPED':
            self.action_buttons['start'].setEnabled(True)
            self.action_buttons['stop'].setEnabled(False)
            self.action_buttons['restart'].setEnabled(False)
        else:
            # Unknown state - enable all
            for btn in self.action_buttons.values():
                btn.setEnabled(True)
    
    def _on_action_clicked(self, action_id: str):
        """Handle action button click."""
        if self.current_app:
            self.action_requested.emit(action_id, self.current_app)
    
    def _on_env_save_requested(self, env_vars: Dict[str, str]):
        """Handle environment variables save request."""
        if self.current_app:
            # Emit action to parent to handle the API call
            self.action_requested.emit('save_environment', {
                **self.current_app,
                'env_vars': env_vars
            })
    
    def _refresh_logs(self):
        """Refresh application logs."""
        if self.current_app:
            self.action_requested.emit('refresh_logs', self.current_app)
    
    def set_status_message(self, message: str):
        """Set a status message in the details panel."""
        # You could add a status label here if needed
        # For now, just log it
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Application details status: {message}")
    
    def set_organization(self, org_id: str):
        """Set the current organization ID."""
        self.current_org_id = org_id
    
    def _load_environment_variables(self, app_id: str):
        """Load environment variables for an application."""
        if not self.api_client:
            self.logger.error("No API client available for loading environment variables")
            return
            
        # Create a worker to load environment variables
        thread = QThread()
        worker = EnvironmentLoader(self.api_client, app_id, self.current_org_id)
        worker.moveToThread(thread)
        
        # Connect signals
        worker.env_loaded.connect(self._on_env_loaded)
        worker.env_error.connect(self._on_env_error)
        thread.started.connect(worker.load_env)
        
        # Start thread
        thread.start()
        
        # Store reference to clean up later
        self._env_thread = thread
        self._env_worker = worker
    
    def _on_env_loaded(self, app_id: str, env_vars: Dict[str, str]):
        """Handle successful environment variables loading."""
        self.logger.info(f"Received {len(env_vars)} environment variables for app {app_id}: {list(env_vars.keys())}")
        
        if hasattr(self, 'env_editor'):
            self.env_editor.set_application(app_id, env_vars)
        
        # Cleanup thread
        if hasattr(self, '_env_thread'):
            self._env_thread.quit()
            self._env_thread.wait()
    
    def _on_env_error(self, app_id: str, error: str):
        """Handle environment variables loading error."""
        # Show placeholder data with error message
        if hasattr(self, 'env_editor'):
            placeholder_env = {
                'ERROR': f'Failed to load environment variables: {error}'
            }
            self.env_editor.set_application(app_id, placeholder_env)
        
        # Cleanup thread
        if hasattr(self, '_env_thread'):
            self._env_thread.quit()
            self._env_thread.wait()


class EnvironmentLoader(QObject):
    """Worker class for loading environment variables."""
    
    # Signals
    env_loaded = Signal(str, dict)  # app_id, env_vars
    env_error = Signal(str, str)    # app_id, error
    
    def __init__(self, api_client: CleverCloudClient, app_id: str, org_id: Optional[str] = None):
        super().__init__()
        # Store the original client to copy its configuration
        self.original_api_client = api_client
        self.app_id = app_id
        self.org_id = org_id
        self.logger = logging.getLogger(__name__)
    
    def load_env(self):
        """Load environment variables in thread."""
        import asyncio
        from clever_desktop.api.client import CleverCloudClient
        
        async def fetch_env():
            # Create a new API client instance for this thread
            api_client = None
            try:
                self.logger.info(f"Loading environment variables for app: {self.app_id} with org_id: {self.org_id}")
                
                # Create new API client with same auth
                api_client = CleverCloudClient()
                # Copy the auth token from the original client
                if hasattr(self.original_api_client, 'auth') and self.original_api_client.auth.get_api_token():
                    api_client.auth.api_token = self.original_api_client.auth.get_api_token()
                
                env_data = await api_client.get_application_env(self.app_id, self.org_id)
                self.logger.info(f"Raw API response for env vars: {env_data}")
                
                # Convert API format to simple dict
                env_vars = {}
                if isinstance(env_data, list):
                    # API returns directly [{"name": "...", "value": "..."}]
                    for var in env_data:
                        if isinstance(var, dict) and 'name' in var and 'value' in var:
                            env_vars[var['name']] = var['value']
                elif isinstance(env_data, dict) and 'env' in env_data:
                    # API returns {"env": [{"name": "...", "value": "..."}], ...}
                    for var in env_data.get('env', []):
                        if isinstance(var, dict) and 'name' in var and 'value' in var:
                            env_vars[var['name']] = var['value']
                elif isinstance(env_data, dict):
                    # API returns simple dict format
                    env_vars = env_data
                
                self.logger.info(f"Loaded {len(env_vars)} environment variables")
                return env_vars
            except Exception as e:
                self.logger.error(f"Failed to load environment variables: {e}")
                raise e
            finally:
                # Clean up the API client
                if api_client:
                    try:
                        await api_client.close()
                    except:
                        pass
        
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            env_vars = loop.run_until_complete(fetch_env())
            self.env_loaded.emit(self.app_id, env_vars)
        except Exception as e:
            self.env_error.emit(self.app_id, str(e))
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass


class ApplicationActionWorker(QObject):
    """Worker class for application actions that need to run in a separate thread."""
    
    # Signals
    action_completed = Signal(str, str, bool, str)  # action, app_name, success, message
    progress_updated = Signal(str)  # status message
    
    def __init__(self, api_client: CleverCloudClient, action: str, app_id: str, app_name: str, env_vars: Optional[Dict[str, str]] = None):
        super().__init__()
        # Store the original client to copy its configuration
        self.original_api_client = api_client
        self.action = action
        self.app_id = app_id
        self.app_name = app_name
        self.env_vars = env_vars
        self.logger = logging.getLogger(__name__)
    
    def execute_action(self):
        """Execute the application action."""
        import asyncio
        from clever_desktop.api.client import CleverCloudClient
        
        async def run_action():
            # Create a new API client instance for this thread
            api_client = None
            try:
                self.progress_updated.emit(f"{self.action.capitalize()}ing {self.app_name}...")
                self.logger.info(f"Executing {self.action} for application {self.app_name} (ID: {self.app_id})")
                
                # Create new API client with same auth
                api_client = CleverCloudClient()
                # Copy the auth token from the original client
                if hasattr(self.original_api_client, 'auth') and self.original_api_client.auth.get_api_token():
                    api_client.auth.api_token = self.original_api_client.auth.get_api_token()
                
                if self.action == 'start':
                    await api_client.start_application(self.app_id)
                    message = f"Application '{self.app_name}' started successfully."
                elif self.action == 'stop':
                    await api_client.stop_application(self.app_id)
                    message = f"Application '{self.app_name}' stopped successfully."
                elif self.action == 'restart':
                    await api_client.restart_application(self.app_id)
                    message = f"Application '{self.app_name}' restarted successfully."
                elif self.action == 'save_environment':
                    if self.env_vars is not None:
                        await api_client.set_application_env(self.app_id, self.env_vars)
                        message = f"Environment variables for '{self.app_name}' saved successfully."
                    else:
                        raise ValueError("No environment variables provided for save operation")
                else:
                    raise ValueError(f"Unknown action: {self.action}")
                
                self.logger.info(f"Action {self.action} completed successfully for {self.app_name}")
                self.action_completed.emit(self.action, self.app_name, True, message)
                
            except Exception as e:
                error_msg = f"Failed to {self.action} application '{self.app_name}': {str(e)}"
                self.logger.error(error_msg)
                self.action_completed.emit(self.action, self.app_name, False, error_msg)
            finally:
                # Clean up the API client
                if api_client:
                    try:
                        await api_client.close()
                    except:
                        pass
        
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function in this thread
            loop.run_until_complete(run_action())
        except Exception as e:
            error_msg = f"Thread execution failed for {self.action}: {str(e)}"
            self.logger.error(error_msg)
            self.action_completed.emit(self.action, self.app_name, False, error_msg)
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass


class ApplicationsPage(QWidget):
    """Applications management page."""
    
    def __init__(self, api_client: CleverCloudClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Data
        self.current_org_id = None  # Will be set when organization is selected
        self.applications = []
        
        # Action tracking
        self.active_actions = {}  # action_id -> thread info
        
        self.setup_ui()
        self.setup_refresh_timer()
        
        self.logger.info("Applications page initialized")
    
    def setup_ui(self):
        """Setup the applications page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(30, 20, 30, 10)
        
        # Title
        title_label = QLabel("Applications")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #212529;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search applications...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.filter_applications)
        header_layout.addWidget(self.search_input)
        
        # View toggle (could add table/grid view toggle here)
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_applications)
        header_layout.addWidget(self.refresh_btn)
        
        # Create new app button
        self.create_btn = QPushButton("➕ New Application")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.create_btn.clicked.connect(self.create_application)
        header_layout.addWidget(self.create_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Applications list/grid
        self.apps_scroll = QScrollArea()
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setMinimumWidth(400)
        
        self.apps_container = QWidget()
        self.apps_layout = QVBoxLayout(self.apps_container)
        self.apps_layout.setContentsMargins(20, 10, 20, 20)
        self.apps_layout.setSpacing(15)
        
        # Loading label
        self.loading_label = QLabel("Loading applications...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 50px;")
        self.apps_layout.addWidget(self.loading_label)
        
        self.apps_scroll.setWidget(self.apps_container)
        splitter.addWidget(self.apps_scroll)
        
        # Details panel
        self.details_panel = ApplicationDetailsPanel(api_client=self.api_client)
        self.details_panel.action_requested.connect(self.handle_application_action)
        splitter.addWidget(self.details_panel)
        
        # Set splitter proportions
        splitter.setSizes([500, 400])
        
        layout.addWidget(splitter)
        
        # Load applications
        self.refresh_applications()
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_applications)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def refresh_applications(self):
        """Refresh applications list using QTimer to handle async."""
        # Use QTimer to schedule async data loading
        QTimer.singleShot(100, self._refresh_applications_async)
    
    def _refresh_applications_async(self):
        """Refresh applications using a separate thread."""
        from PySide6.QtCore import QThread, QObject, Signal
        
        class ApplicationsLoader(QObject):
            data_loaded = Signal(list)  # applications
            error_occurred = Signal(str)
            
            def __init__(self, api_client, org_id, logger):
                super().__init__()
                self.api_client = api_client
                self.org_id = org_id
                self.logger = logger
            
            def load_data(self):
                """Load applications in thread."""
                import asyncio
                from clever_desktop.api.client import CleverCloudClient
                
                async def fetch_applications():
                    # Create a new API client instance for this thread
                    api_client = None
                    try:
                        self.logger.info(f"Loading applications from API for org: {self.org_id}")
                        
                        # Create new API client with same auth
                        api_client = CleverCloudClient()
                        # Copy the auth token from the original client
                        if hasattr(self.api_client, 'auth') and self.api_client.auth.get_api_token():
                            api_client.auth.api_token = self.api_client.auth.get_api_token()
                        
                        # Get applications from API for current organization
                        if self.org_id:
                            applications = await api_client.get_applications(self.org_id)
                        else:
                            # Fallback to all applications if no org selected
                            applications = await api_client.get_applications()
                        
                        self.logger.info(f"Loaded {len(applications)} applications from API")
                        return applications
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load applications: {e}")
                        raise e
                    finally:
                        # Clean up the API client
                        if api_client:
                            try:
                                await api_client.close()
                            except:
                                pass
                
                try:
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run async code in this thread
                    applications = loop.run_until_complete(fetch_applications())
                    self.data_loaded.emit(applications)
                except Exception as e:
                    self.error_occurred.emit(str(e))
                finally:
                    # Clean up the event loop
                    try:
                        loop.close()
                    except:
                        pass
        
        # Show loading
        self.loading_label.setText("Loading applications...")
        self.loading_label.show()
        
        # Create thread and loader
        if hasattr(self, 'apps_thread') and self.apps_thread.isRunning():
            self.apps_thread.quit()
            self.apps_thread.wait()
        
        self.apps_thread = QThread()
        self.apps_loader = ApplicationsLoader(self.api_client, self.current_org_id, self.logger)
        self.apps_loader.moveToThread(self.apps_thread)
        
        # Connect signals
        self.apps_loader.data_loaded.connect(self._on_applications_loaded)
        self.apps_loader.error_occurred.connect(self._on_applications_error)
        self.apps_thread.started.connect(self.apps_loader.load_data)
        
        # Start thread
        self.apps_thread.start()
        self.logger.info("Started applications loading thread")
    
    def _on_applications_loaded(self, applications: list):
        """Handle successful applications loading."""
        self.logger.info(f"Applications loading completed: {len(applications)} applications")
        
        # Store applications
        self.applications = applications
        
        # Update display
        self.update_applications_display()
        
        # Cleanup thread
        self.apps_thread.quit()
        self.apps_thread.wait()
    
    def _on_applications_error(self, error: str):
        """Handle applications loading error."""
        self.logger.error(f"Applications loading failed: {error}")
        self.loading_label.setText(f"Error loading applications: {error}")
        
        # Cleanup thread
        self.apps_thread.quit()
        self.apps_thread.wait()
    
    def update_applications_display(self):
        """Update the applications display."""
        # Clear existing cards
        for i in reversed(range(self.apps_layout.count())):
            child = self.apps_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.applications:
            no_apps_label = QLabel("No applications found")
            no_apps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_apps_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 50px;")
            self.apps_layout.addWidget(no_apps_label)
            return
        
        # Add application cards
        for app in self.applications:
            card = ApplicationCard(app)
            card.application_selected.connect(self.details_panel.set_application)
            card.action_requested.connect(self.handle_application_action)
            self.apps_layout.addWidget(card)
        
        # Add stretch to push cards to top
        self.apps_layout.addStretch()
    
    def filter_applications(self, search_text: str):
        """Filter applications based on search text."""
        # This would filter the displayed applications
        # For now, just a placeholder
        pass
    
    def create_application(self):
        """Create a new application."""
        # This would open a create application dialog
        QMessageBox.information(self, "Create Application", "Create application dialog will be implemented here.")
    
    def handle_application_action(self, action: str, app_data: Dict[str, Any]):
        """Handle application actions with proper async execution."""
        app_name = app_data.get('name', 'Unknown')
        app_id = app_data.get('id', '')
        
        if not app_id:
            QMessageBox.warning(self, "Error", "Invalid application ID")
            return
        
        self.logger.info(f"Action '{action}' requested for application '{app_name}'")
        
        # Handle actions that require API calls
        if action in ['start', 'stop', 'restart']:
            self._execute_application_action(action, app_id, app_name)
        elif action == 'deploy':
            self.deploy_application(app_id, app_name)
        elif action == 'logs':
            self.view_logs(app_id, app_name)
        elif action == 'environment':
            self.manage_environment(app_id, app_name)
        elif action == 'save_environment':
            self.save_environment_variables(app_data)
        elif action == 'delete':
            self.delete_application(app_id, app_name)
        elif action == 'refresh_logs':
            self.refresh_logs(app_id, app_name)
    
    def _execute_application_action(self, action: str, app_id: str, app_name: str):
        """Execute application action in a separate thread."""
        # Check if an action is already running for this app
        action_key = f"{action}_{app_id}"
        if action_key in self.active_actions:
            QMessageBox.information(
                self, 
                "Action in Progress", 
                f"An action is already running for '{app_name}'. Please wait."
            )
            return
        
        # Confirm destructive actions
        if action in ['stop', 'restart']:
            reply = QMessageBox.question(
                self,
                f"Confirm {action.capitalize()}",
                f"Are you sure you want to {action} application '{app_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Create worker thread
        thread = QThread()
        worker = ApplicationActionWorker(self.api_client, action, app_id, app_name)
        worker.moveToThread(thread)
        
        # Connect signals
        worker.action_completed.connect(self._on_action_completed)
        worker.progress_updated.connect(self._on_action_progress)
        thread.started.connect(worker.execute_action)
        
        # Store thread info
        self.active_actions[action_key] = {
            'thread': thread,
            'worker': worker,
            'app_name': app_name,
            'start_time': QTimer()
        }
        
        # Start the thread
        thread.start()
        self.logger.info(f"Started {action} thread for application {app_name}")
    
    def _on_action_progress(self, message: str):
        """Handle action progress updates."""
        # Update status in details panel if it's showing this app
        if hasattr(self, 'details_panel') and self.details_panel.current_app:
            self.details_panel.set_status_message(message)
        
        # Could also show in a status bar if we had one
        self.logger.debug(f"Action progress: {message}")
    
    def _on_action_completed(self, action: str, app_name: str, success: bool, message: str):
        """Handle action completion."""
        action_key = f"{action}_{app_name}"  # Note: using app_name as approximation
        
        # Remove from active actions (find by app_name since we don't have app_id here)
        to_remove = []
        for key, info in self.active_actions.items():
            if info['app_name'] == app_name:
                to_remove.append(key)
        
        for key in to_remove:
            if key in self.active_actions:
                thread = self.active_actions[key]['thread']
                thread.quit()
                thread.wait()
                del self.active_actions[key]
        
        # Show result to user
        if success:
            QMessageBox.information(self, "Success", message)
            # Refresh applications to show updated state
            QTimer.singleShot(2000, self.refresh_applications)  # Delay to let API settle
        else:
            QMessageBox.critical(self, "Error", message)
        
        self.logger.info(f"Action {action} completed for {app_name}: {'Success' if success else 'Failed'}")
    
    def start_application(self, app_id: str, app_name: str):
        """Start an application - deprecated, use handle_application_action instead."""
        self.logger.warning("Deprecated method start_application called, use handle_application_action")
        self.handle_application_action('start', {'id': app_id, 'name': app_name})
    
    def stop_application(self, app_id: str, app_name: str):
        """Stop an application - deprecated, use handle_application_action instead."""
        self.logger.warning("Deprecated method stop_application called, use handle_application_action")
        self.handle_application_action('stop', {'id': app_id, 'name': app_name})
    
    def restart_application(self, app_id: str, app_name: str):
        """Restart an application - deprecated, use handle_application_action instead."""
        self.logger.warning("Deprecated method restart_application called, use handle_application_action")
        self.handle_application_action('restart', {'id': app_id, 'name': app_name})
    
    def deploy_application(self, app_id: str, app_name: str):
        """Deploy an application."""
        QMessageBox.information(self, "Deploy", f"Deploy dialog for '{app_name}' will be implemented here.")
    
    def view_logs(self, app_id: str, app_name: str):
        """View application logs."""
        QMessageBox.information(self, "Logs", f"Logs viewer for '{app_name}' will be implemented here.")
    
    def manage_environment(self, app_id: str, app_name: str):
        """Manage environment variables."""
        # This is now handled by the environment tab in the details panel
        QMessageBox.information(self, "Environment", f"Use the Environment tab in the details panel to manage variables for '{app_name}'.")
    
    def save_environment_variables(self, app_data: Dict[str, Any]):
        """Save environment variables for an application."""
        app_id = app_data.get('id', '')
        app_name = app_data.get('name', 'Unknown')
        env_vars = app_data.get('env_vars', {})
        
        if not app_id:
            QMessageBox.warning(self, "Error", "Invalid application ID")
            return
        
        self.logger.info(f"Saving environment variables for application {app_name} (ID: {app_id})")
        
        # Create worker thread for saving environment variables
        self._execute_environment_save(app_id, app_name, env_vars)
    
    def _execute_environment_save(self, app_id: str, app_name: str, env_vars: Dict[str, str]):
        """Execute environment variables save in a separate thread."""
        # Check if an action is already running for this app
        action_key = f"save_environment_{app_id}"
        if action_key in self.active_actions:
            QMessageBox.information(
                self, 
                "Save in Progress", 
                f"Environment variables are already being saved for '{app_name}'. Please wait."
            )
            return
        
        # Confirm save action
        reply = QMessageBox.question(
            self,
            "Save Environment Variables",
            f"Save {len(env_vars)} environment variables for '{app_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create worker thread
        thread = QThread()
        worker = ApplicationActionWorker(self.api_client, 'save_environment', app_id, app_name, env_vars)
        worker.moveToThread(thread)
        
        # Connect signals
        worker.action_completed.connect(self._on_environment_save_completed)
        worker.progress_updated.connect(self._on_action_progress)
        thread.started.connect(worker.execute_action)
        
        # Store thread info
        self.active_actions[action_key] = {
            'thread': thread,
            'worker': worker,
            'app_name': app_name,
            'start_time': QTimer()
        }
        
        # Start the thread
        thread.start()
        self.logger.info(f"Started environment save thread for application {app_name}")
    
    def _on_environment_save_completed(self, action: str, app_name: str, success: bool, message: str):
        """Handle environment save completion."""
        # Remove from active actions
        action_key = f"save_environment_{app_name}"  # Approximation using app_name
        to_remove = []
        for key, info in self.active_actions.items():
            if 'save_environment' in key and info['app_name'] == app_name:
                to_remove.append(key)
        
        for key in to_remove:
            if key in self.active_actions:
                thread = self.active_actions[key]['thread']
                thread.quit()
                thread.wait()
                del self.active_actions[key]
        
        # Show result to user
        if success:
            QMessageBox.information(self, "Success", message)
            # Mark as saved in the environment editor
            if hasattr(self.details_panel, 'env_editor'):
                self.details_panel.env_editor.mark_saved()
        else:
            QMessageBox.critical(self, "Error", message)
        
        self.logger.info(f"Environment save completed for {app_name}: {'Success' if success else 'Failed'}")
    
    def delete_application(self, app_id: str, app_name: str):
        """Delete an application."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete application '{app_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Delete", f"Delete functionality for '{app_name}' will be implemented here.")
    
    def refresh_logs(self, app_id: str, app_name: str):
        """Refresh application logs."""
        QMessageBox.information(self, "Refresh Logs", f"Refreshing logs for '{app_name}'...")
    
    def set_organization(self, org_id: str):
        """Set the current organization and refresh applications."""
        self.current_org_id = org_id
        self.logger.info(f"Applications page: Organization changed to {org_id}")
        # Update details panel with new organization
        if hasattr(self, 'details_panel'):
            self.details_panel.set_organization(org_id)
        # Refresh applications with new organization
        self.refresh_applications()
    
    def showEvent(self, event):
        """Handle page show event."""
        super().showEvent(event)
        # Refresh applications when page is shown
        self.refresh_applications()
    
    def closeEvent(self, event):
        """Handle page close event - cleanup active actions."""
        # Cancel all running actions
        for action_key, info in self.active_actions.items():
            thread = info['thread']
            if thread.isRunning():
                self.logger.info(f"Terminating action thread: {action_key}")
                thread.quit()
                thread.wait(3000)  # Wait up to 3 seconds
        
        self.active_actions.clear()
        super().closeEvent(event) 