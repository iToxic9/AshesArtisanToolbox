"""
Base widget classes for reusability across the Artisan Toolbox application.
Provides common UI components with consistent styling and behavior.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QGroupBox, QTextEdit, QHeaderView, QMessageBox, QDialog,
    QDialogButtonBox, QProgressBar, QCheckBox, QSlider, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)

class StatusIndicator(QLabel):
    """Status indicator widget with color-coded status display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status("Unknown", "gray")
    
    def set_status(self, text: str, color: str = "gray"):
        """Set status text and color"""
        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)

class SearchableComboBox(QComboBox):
    """ComboBox with built-in search functionality"""
    
    item_selected = pyqtSignal(object)  # Emits the item data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Store original items for filtering
        self._all_items: List[Dict[str, Any]] = []
        
        # Connect signals
        self.editTextChanged.connect(self._filter_items)
        self.currentTextChanged.connect(self._on_selection_changed)
    
    def add_searchable_item(self, text: str, data: Any = None, keywords: List[str] = None):
        """Add an item with searchable keywords"""
        item_data = {
            'text': text,
            'data': data,
            'keywords': keywords or [text.lower()]
        }
        self._all_items.append(item_data)
        self.addItem(text, data)
    
    def clear_searchable_items(self):
        """Clear all items including search data"""
        self._all_items.clear()
        self.clear()
    
    def _filter_items(self, search_text: str):
        """Filter items based on search text"""
        if not search_text:
            self._restore_all_items()
            return
        
        search_lower = search_text.lower()
        filtered_items = []
        
        for item in self._all_items:
            # Check if search text matches any keyword
            if any(search_lower in keyword for keyword in item['keywords']):
                filtered_items.append(item)
        
        # Update combo box with filtered items
        self.clear()
        for item in filtered_items:
            self.addItem(item['text'], item['data'])
    
    def _restore_all_items(self):
        """Restore all items to the combo box"""
        self.clear()
        for item in self._all_items:
            self.addItem(item['text'], item['data'])
    
    def _on_selection_changed(self, text: str):
        """Handle selection change"""
        current_data = self.currentData()
        if current_data is not None:
            self.item_selected.emit(current_data)

class ProgressDialog(QDialog):
    """Modal progress dialog for long-running operations"""
    
    def __init__(self, title: str = "Processing", message: str = "Please wait...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)
        
        layout = QVBoxLayout(self)
        
        # Message label
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate by default
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)
    
    def update_message(self, message: str):
        """Update the main message"""
        self.message_label.setText(message)
    
    def update_status(self, status: str):
        """Update the status text"""
        self.status_label.setText(status)
    
    def set_progress(self, value: int, maximum: int = 100):
        """Set progress value (switches to determinate mode)"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
    
    def set_indeterminate(self):
        """Switch to indeterminate progress mode"""
        self.progress_bar.setRange(0, 0)

class DataTable(QTableWidget):
    """Enhanced table widget with common functionality"""
    
    row_double_clicked = pyqtSignal(int, dict)  # row, data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure table appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        
        # Connect signals
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Store row data
        self._row_data: Dict[int, dict] = {}
    
    def setup_columns(self, columns: List[str], widths: List[str] = None):
        """Setup table columns with optional width modes"""
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        header = self.horizontalHeader()
        
        if widths:
            for i, width_mode in enumerate(widths):
                if width_mode == "stretch":
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                elif width_mode == "content":
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
                elif width_mode == "fixed":
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        else:
            # Default: first column stretches, others fit content
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for i in range(1, len(columns)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    
    def add_data_row(self, row_data: dict, columns: List[str] = None):
        """Add a row with associated data"""
        if columns is None:
            columns = [str(row_data.get(f"col_{i}", "")) for i in range(self.columnCount())]
        
        row = self.rowCount()
        self.insertRow(row)
        
        # Store row data
        self._row_data[row] = row_data
        
        # Populate columns
        for col, value in enumerate(columns):
            if col < self.columnCount():
                item = QTableWidgetItem(str(value))
                
                # Apply conditional formatting based on data
                self._apply_conditional_formatting(item, row_data, col)
                
                self.setItem(row, col, item)
    
    def _apply_conditional_formatting(self, item: QTableWidgetItem, row_data: dict, col: int):
        """Apply conditional formatting based on row data"""
        # Override in subclasses for specific formatting rules
        pass
    
    def get_row_data(self, row: int) -> dict:
        """Get data associated with a row"""
        return self._row_data.get(row, {})
    
    def clear_data(self):
        """Clear table data and reset"""
        self.setRowCount(0)
        self._row_data.clear()
    
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle item double click"""
        row = item.row()
        row_data = self.get_row_data(row)
        self.row_double_clicked.emit(row, row_data)

class NumericInput(QWidget):
    """Numeric input with label, validation, and optional suffix"""
    
    value_changed = pyqtSignal(float)
    
    def __init__(self, label: str, min_value: float = 0.0, max_value: float = 999999.99, 
                 decimals: int = 2, suffix: str = "", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        self.label = QLabel(label)
        self.label.setMinimumWidth(100)
        layout.addWidget(self.label)
        
        # Numeric input
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(min_value, max_value)
        self.spinbox.setDecimals(decimals)
        if suffix:
            self.spinbox.setSuffix(f" {suffix}")
        
        layout.addWidget(self.spinbox)
        
        # Connect signal
        self.spinbox.valueChanged.connect(self.value_changed.emit)
    
    def value(self) -> float:
        """Get current value"""
        return self.spinbox.value()
    
    def set_value(self, value: float):
        """Set current value"""
        self.spinbox.setValue(value)

class TaxRateSlider(QWidget):
    """Tax rate slider with percentage display"""
    
    value_changed = pyqtSignal(float)  # Emits percentage as float (0.0-1.0)
    
    def __init__(self, initial_value: float = 0.15, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Tax Rate:"))
        
        self.percentage_label = QLabel("15%")
        self.percentage_label.setStyleSheet("font-weight: bold; color: #ffd700;")
        header_layout.addWidget(self.percentage_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(initial_value * 100))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        
        layout.addWidget(self.slider)
        
        # Connect signal
        self.slider.valueChanged.connect(self._on_value_changed)
    
    def _on_value_changed(self, value: int):
        """Handle slider value change"""
        percentage = value / 100.0
        self.percentage_label.setText(f"{value}%")
        self.value_changed.emit(percentage)
    
    def value(self) -> float:
        """Get current value as percentage (0.0-1.0)"""
        return self.slider.value() / 100.0
    
    def set_value(self, percentage: float):
        """Set value from percentage (0.0-1.0)"""
        self.slider.setValue(int(percentage * 100))

class InfoPanel(QFrame):
    """Information panel with title and key-value pairs"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0078d4; margin-bottom: 8px;")
        layout.addWidget(title_label)
        
        # Content area
        self.content_layout = QGridLayout()
        layout.addLayout(self.content_layout)
        
        layout.addStretch()
        
        self._row = 0
    
    def add_info_item(self, label: str, value: str, value_style: str = ""):
        """Add a label-value pair to the panel"""
        label_widget = QLabel(f"{label}:")
        value_widget = QLabel(value)
        
        if value_style:
            value_widget.setStyleSheet(value_style)
        
        self.content_layout.addWidget(label_widget, self._row, 0)
        self.content_layout.addWidget(value_widget, self._row, 1)
        
        self._row += 1
        
        return value_widget  # Return for later updates
    
    def clear_items(self):
        """Clear all info items"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._row = 0

class ActionButton(QPushButton):
    """Styled action button with predefined styles"""
    
    def __init__(self, text: str, style: str = "primary", parent=None):
        super().__init__(text, parent)
        
        self.setMinimumHeight(32)
        self.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        
        styles = {
            "primary": "background-color: #0078d4; color: white;",
            "success": "background-color: #28a745; color: white;",
            "warning": "background-color: #ffc107; color: black;",
            "danger": "background-color: #dc3545; color: white;",
            "secondary": "background-color: #6c757d; color: white;"
        }
        
        base_style = """
            QPushButton {
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.2);
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        
        self.setStyleSheet(base_style + f"QPushButton {{ {styles.get(style, styles['primary'])} }}")

class ConfirmationDialog(QMessageBox):
    """Styled confirmation dialog"""
    
    @staticmethod
    def ask(parent, title: str, message: str, details: str = None) -> bool:
        """Show confirmation dialog and return True if accepted"""
        dialog = QMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.setIcon(QMessageBox.Icon.Question)
        
        return dialog.exec() == QMessageBox.StandardButton.Yes

# Utility functions for common operations
def show_error(parent, title: str, message: str, details: str = None):
    """Show error message dialog"""
    dialog = QMessageBox(parent)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.setIcon(QMessageBox.Icon.Critical)
    
    if details:
        dialog.setDetailedText(details)
    
    dialog.exec()

def show_info(parent, title: str, message: str):
    """Show information message dialog"""
    QMessageBox.information(parent, title, message)

def show_warning(parent, title: str, message: str):
    """Show warning message dialog"""
    QMessageBox.warning(parent, title, message)

# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    # Test window
    window = QMainWindow()
    window.setWindowTitle("Base Widgets Test")
    
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    
    # Test widgets
    status = StatusIndicator()
    status.set_status("Connected", "#28a745")
    layout.addWidget(status)
    
    search_combo = SearchableComboBox()
    search_combo.add_searchable_item("Test Item 1", 1, ["test", "item", "one"])
    search_combo.add_searchable_item("Another Item", 2, ["another", "item", "two"])
    layout.addWidget(search_combo)
    
    tax_slider = TaxRateSlider()
    layout.addWidget(tax_slider)
    
    numeric_input = NumericInput("Price:", 0.0, 1000.0, 2, "gold")
    layout.addWidget(numeric_input)
    
    info_panel = InfoPanel("Test Info")
    info_panel.add_info_item("Status", "Ready", "color: green; font-weight: bold;")
    info_panel.add_info_item("Items", "42")
    layout.addWidget(info_panel)
    
    button = ActionButton("Test Action", "success")
    layout.addWidget(button)
    
    window.show()
    sys.exit(app.exec())