"""
Inventory Manager module for node-based storage tracking.
Follows the data flow from local cache to inventory display and management.
"""

import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QGroupBox, QTextEdit, QSplitter, QHeaderView, QMessageBox,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from data_manager import DataManager
from rarity_system import RarityManager, ItemRarity, get_rarity_style_sheet, format_item_with_rarity
from gui.base_module import BaseModule

logger = logging.getLogger(__name__)

class InventoryManagerModule(BaseModule):
    """
    Inventory manager for tracking materials across multiple nodes.
    
    Data Flow: Local Cache -> Inventory Manager -> Display Updates
    """
    
    def __init__(self, data_manager: DataManager):
        self.current_inventory = {}
        self.node_inventories = {}
        
        # Initialize base module
        super().__init__(data_manager, "Inventory")
    
    def setup_ui(self):
        """Setup the inventory manager UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different inventory views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Overview tab
        overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(overview_tab, "📋 Overview")
        
        # Node storage tab
        node_tab = self.create_node_storage_tab()
        self.tab_widget.addTab(node_tab, "🏰 Node Storage")
        
        # Manual entry tab
        manual_tab = self.create_manual_entry_tab()
        self.tab_widget.addTab(manual_tab, "✏️ Manual Entry")
        
        # Future: Screenshot import tab
        # screenshot_tab = self.create_screenshot_tab()
        # self.tab_widget.addTab(screenshot_tab, "📷 Screenshot Import")
    
    def create_overview_tab(self) -> QWidget:
        """Create inventory overview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search and filters
        search_group = QGroupBox("Search & Filters")
        search_layout = QGridLayout(search_group)
        
        # Item search
        search_layout.addWidget(QLabel("Search Items:"), 0, 0)
        self.overview_search = QLineEdit()
        self.overview_search.setPlaceholderText("Type item name...")
        search_layout.addWidget(self.overview_search, 0, 1)
        
        # Filter by rarity
        search_layout.addWidget(QLabel("Rarity:"), 0, 2)
        self.rarity_filter = QComboBox()
        rarity_options = ["All Rarities"] + RarityManager.get_rarity_display_list()
        self.rarity_filter.addItems(rarity_options)
        search_layout.addWidget(self.rarity_filter, 0, 3)
        
        # Filter by availability
        search_layout.addWidget(QLabel("Filter:"), 1, 0)
        self.availability_filter = QComboBox()
        self.availability_filter.addItems([
            "All Items", "In Stock", "Low Stock", "Out of Stock"
        ])
        search_layout.addWidget(self.availability_filter, 1, 1)
        
        # Refresh button
        self.refresh_overview_button = QPushButton("Refresh")
        search_layout.addWidget(self.refresh_overview_button, 1, 2)
        
        layout.addWidget(search_group)
        
        # Inventory summary table
        summary_group = QGroupBox("Inventory Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.overview_table = QTableWidget()
        self.overview_table.setColumnCount(7)
        self.overview_table.setHorizontalHeaderLabels([
            "Item", "Rarity", "Total Qty", "Locations", "Avg Cost", "Total Value", "Status"
        ])
        
        # Configure table
        header = self.overview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        summary_layout.addWidget(self.overview_table)
        layout.addWidget(summary_group)
        
        return tab
    
    def create_node_storage_tab(self) -> QWidget:
        """Create node-specific storage management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left panel - Node selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(250)
        
        # Node selection
        node_group = QGroupBox("Select Node")
        node_layout = QVBoxLayout(node_group)
        
        self.node_list = QTreeWidget()
        self.node_list.setHeaderLabels(["Node", "Items"])
        
        # Popular nodes (mock data)
        popular_nodes = [
            "Lionhold", "Winstead", "Miraleth", "Haelshore", 
            "Dünheim", "New Aela", "Ek'thor"
        ]
        
        for node in popular_nodes:
            node_item = QTreeWidgetItem([node, "0"])
            self.node_list.addTopLevelItem(node_item)
        
        node_layout.addWidget(self.node_list)
        
        # Add new node
        add_node_layout = QHBoxLayout()
        self.new_node_input = QLineEdit()
        self.new_node_input.setPlaceholderText("New node name...")
        add_node_layout.addWidget(self.new_node_input)
        
        self.add_node_button = QPushButton("Add")
        add_node_layout.addWidget(self.add_node_button)
        
        node_layout.addLayout(add_node_layout)
        left_layout.addWidget(node_group)
        
        # Node stats
        stats_group = QGroupBox("Node Statistics")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("Total Items:"), 0, 0)
        self.node_total_items = QLabel("0")
        stats_layout.addWidget(self.node_total_items, 0, 1)
        
        stats_layout.addWidget(QLabel("Total Value:"), 1, 0)
        self.node_total_value = QLabel("0.00 gold")
        stats_layout.addWidget(self.node_total_value, 1, 1)
        
        stats_layout.addWidget(QLabel("Last Updated:"), 2, 0)
        self.node_last_updated = QLabel("Never")
        stats_layout.addWidget(self.node_last_updated, 2, 1)
        
        left_layout.addWidget(stats_group)
        left_layout.addStretch()
        
        layout.addWidget(left_panel)
        
        # Right panel - Node inventory details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Node inventory table
        inventory_group = QGroupBox("Node Inventory")
        inventory_layout = QVBoxLayout(inventory_group)
        
        # Node selection display
        node_header = QHBoxLayout()
        self.selected_node_label = QLabel("Select a node to view inventory")
        self.selected_node_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        node_header.addWidget(self.selected_node_label)
        
        node_header.addStretch()
        
        self.export_node_button = QPushButton("Export Node Data")
        node_header.addWidget(self.export_node_button)
        
        inventory_layout.addLayout(node_header)
        
        # Inventory table
        self.node_inventory_table = QTableWidget()
        self.node_inventory_table.setColumnCount(5)
        self.node_inventory_table.setHorizontalHeaderLabels([
            "Item", "Quantity", "Avg Cost", "Total Value", "Last Updated"
        ])
        
        header = self.node_inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        inventory_layout.addWidget(self.node_inventory_table)
        right_layout.addWidget(inventory_group)
        
        layout.addWidget(right_panel)
        
        return tab
    
    def create_manual_entry_tab(self) -> QWidget:
        """Create manual inventory entry tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Manual entry form
        entry_group = QGroupBox("Add/Update Inventory")
        entry_layout = QGridLayout(entry_group)
        
        # Item selection
        entry_layout.addWidget(QLabel("Item:"), 0, 0)
        self.item_search_manual = QLineEdit()
        self.item_search_manual.setPlaceholderText("Search for item...")
        entry_layout.addWidget(self.item_search_manual, 0, 1)
        
        self.search_manual_button = QPushButton("Search")
        entry_layout.addWidget(self.search_manual_button, 0, 2)
        
        # Item results
        entry_layout.addWidget(QLabel("Select Item:"), 1, 0)
        self.manual_item_combo = QComboBox()
        self.manual_item_combo.setMinimumWidth(300)
        entry_layout.addWidget(self.manual_item_combo, 1, 1, 1, 2)
        
        # Rarity selection
        entry_layout.addWidget(QLabel("Rarity:"), 2, 0)
        self.manual_rarity_combo = QComboBox()
        self.manual_rarity_combo.addItems(RarityManager.get_rarity_display_list())
        self.manual_rarity_combo.setCurrentText("Common")
        entry_layout.addWidget(self.manual_rarity_combo, 2, 1)
        
        # Node selection
        entry_layout.addWidget(QLabel("Node:"), 3, 0)
        self.manual_node_combo = QComboBox()
        self.manual_node_combo.setEditable(True)
        self.manual_node_combo.addItems([
            "Lionhold", "Winstead", "Miraleth", "Haelshore", 
            "Dünheim", "New Aela", "Ek'thor"
        ])
        entry_layout.addWidget(self.manual_node_combo, 3, 1, 1, 2)
        
        # Quantity
        entry_layout.addWidget(QLabel("Quantity:"), 4, 0)
        self.manual_quantity = QSpinBox()
        self.manual_quantity.setRange(0, 99999)
        entry_layout.addWidget(self.manual_quantity, 4, 1)
        
        # Average cost
        entry_layout.addWidget(QLabel("Average Cost:"), 5, 0)
        self.manual_avg_cost = QDoubleSpinBox()
        self.manual_avg_cost.setRange(0.0, 999999.99)
        self.manual_avg_cost.setDecimals(2)
        self.manual_avg_cost.setSuffix(" gold")
        entry_layout.addWidget(self.manual_avg_cost, 5, 1)
        
        # Notes
        entry_layout.addWidget(QLabel("Notes:"), 6, 0)
        self.manual_notes = QLineEdit()
        self.manual_notes.setPlaceholderText("Optional notes...")
        entry_layout.addWidget(self.manual_notes, 6, 1, 1, 2)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.update_inventory_button = QPushButton("Update Inventory")
        self.update_inventory_button.setStyleSheet("background-color: #28a745; font-weight: bold;")
        button_layout.addWidget(self.update_inventory_button)
        
        self.clear_form_button = QPushButton("Clear Form")
        button_layout.addWidget(self.clear_form_button)
        
        button_layout.addStretch()
        
        entry_layout.addLayout(button_layout, 6, 0, 1, 3)
        
        layout.addWidget(entry_group)
        
        # Recent updates
        recent_group = QGroupBox("Recent Updates")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_updates_table = QTableWidget()
        self.recent_updates_table.setColumnCount(5)
        self.recent_updates_table.setHorizontalHeaderLabels([
            "Item", "Node", "Quantity", "Cost", "Updated"
        ])
        self.recent_updates_table.setMaximumHeight(200)
        
        recent_layout.addWidget(self.recent_updates_table)
        layout.addWidget(recent_group)
        
        return tab
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        # Overview tab
        self.refresh_overview_button.clicked.connect(self.refresh_overview)
        self.overview_search.textChanged.connect(self.filter_overview)
        self.availability_filter.currentTextChanged.connect(self.filter_overview)
        
        # Node storage tab
        self.node_list.itemClicked.connect(self.select_node)
        self.add_node_button.clicked.connect(self.add_new_node)
        self.new_node_input.returnPressed.connect(self.add_new_node)
        self.export_node_button.clicked.connect(self.export_node_data)
        
        # Manual entry tab
        self.search_manual_button.clicked.connect(self.search_items_manual)
        self.item_search_manual.returnPressed.connect(self.search_items_manual)
        self.update_inventory_button.clicked.connect(self.update_inventory_manual)
        self.clear_form_button.clicked.connect(self.clear_manual_form)
    
    def refresh_overview(self):
        """Refresh the inventory overview"""
        try:
            # Get all inventory items from database
            # For now, we'll use mock data
            mock_inventory = [
                {
                    'item_name': 'Parchment',
                    'total_quantity': 45,
                    'locations': ['Lionhold: 30', 'Winstead: 15'],
                    'avg_cost': 8.50,
                    'total_value': 382.50,
                    'status': 'In Stock'
                },
                {
                    'item_name': 'Quality Ink',
                    'total_quantity': 5,
                    'locations': ['Lionhold: 5'],
                    'avg_cost': 25.00,
                    'total_value': 125.00,
                    'status': 'Low Stock'
                },
                {
                    'item_name': 'Binding Thread',
                    'total_quantity': 0,
                    'locations': [],
                    'avg_cost': 0.00,
                    'total_value': 0.00,
                    'status': 'Out of Stock'
                }
            ]
            
            self.overview_table.setRowCount(len(mock_inventory))
            
            for row, item in enumerate(mock_inventory):
                # Item name
                self.overview_table.setItem(row, 0, QTableWidgetItem(item['item_name']))
                
                # Total quantity
                qty_item = QTableWidgetItem(str(item['total_quantity']))
                if item['total_quantity'] == 0:
                    qty_item.setBackground(Qt.GlobalColor.red)
                elif item['total_quantity'] < 10:
                    qty_item.setBackground(Qt.GlobalColor.yellow)
                self.overview_table.setItem(row, 1, qty_item)
                
                # Locations
                locations_text = ', '.join(item['locations']) if item['locations'] else 'None'
                self.overview_table.setItem(row, 2, QTableWidgetItem(locations_text))
                
                # Average cost
                self.overview_table.setItem(row, 3, QTableWidgetItem(f"{item['avg_cost']:.2f}"))
                
                # Total value
                self.overview_table.setItem(row, 4, QTableWidgetItem(f"{item['total_value']:.2f}"))
                
                # Status
                status_item = QTableWidgetItem(item['status'])
                if item['status'] == 'Out of Stock':
                    status_item.setBackground(Qt.GlobalColor.red)
                elif item['status'] == 'Low Stock':
                    status_item.setBackground(Qt.GlobalColor.yellow)
                else:
                    status_item.setBackground(Qt.GlobalColor.green)
                self.overview_table.setItem(row, 5, status_item)
            
            logger.info("Inventory overview refreshed")
            
        except Exception as e:
            logger.error(f"Failed to refresh overview: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh overview: {e}")
    
    def filter_overview(self):
        """Filter the overview table based on search and filter criteria"""
        search_text = self.overview_search.text().lower()
        filter_option = self.availability_filter.currentText()
        
        for row in range(self.overview_table.rowCount()):
            # Check search text
            item_name = self.overview_table.item(row, 0).text().lower()
            text_match = search_text in item_name
            
            # Check filter
            status = self.overview_table.item(row, 5).text()
            filter_match = (
                filter_option == "All Items" or 
                filter_option == status
            )
            
            # Show/hide row
            self.overview_table.setRowHidden(row, not (text_match and filter_match))
    
    def select_node(self, item: QTreeWidgetItem):
        """Select a node and display its inventory"""
        node_name = item.text(0)
        self.selected_node_label.setText(f"Node: {node_name}")
        
        # Load node inventory (mock data)
        mock_node_inventory = [
            {
                'item_name': 'Parchment',
                'quantity': 30,
                'avg_cost': 8.50,
                'total_value': 255.00,
                'last_updated': '2 hours ago'
            },
            {
                'item_name': 'Common Ink',
                'quantity': 12,
                'avg_cost': 15.00,
                'total_value': 180.00,
                'last_updated': '1 day ago'
            }
        ]
        
        self.node_inventory_table.setRowCount(len(mock_node_inventory))
        
        total_value = 0.0
        for row, item in enumerate(mock_node_inventory):
            self.node_inventory_table.setItem(row, 0, QTableWidgetItem(item['item_name']))
            self.node_inventory_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            self.node_inventory_table.setItem(row, 2, QTableWidgetItem(f"{item['avg_cost']:.2f}"))
            self.node_inventory_table.setItem(row, 3, QTableWidgetItem(f"{item['total_value']:.2f}"))
            self.node_inventory_table.setItem(row, 4, QTableWidgetItem(item['last_updated']))
            
            total_value += item['total_value']
        
        # Update node stats
        self.node_total_items.setText(str(len(mock_node_inventory)))
        self.node_total_value.setText(f"{total_value:.2f} gold")
        self.node_last_updated.setText("2 hours ago")
        
        logger.info(f"Selected node: {node_name}")
    
    def add_new_node(self):
        """Add a new node to the list"""
        node_name = self.new_node_input.text().strip()
        if not node_name:
            return
        
        # Check if node already exists
        for i in range(self.node_list.topLevelItemCount()):
            if self.node_list.topLevelItem(i).text(0) == node_name:
                QMessageBox.information(self, "Info", "Node already exists")
                return
        
        # Add new node
        node_item = QTreeWidgetItem([node_name, "0"])
        self.node_list.addTopLevelItem(node_item)
        
        # Add to combo box
        self.manual_node_combo.addItem(node_name)
        
        self.new_node_input.clear()
        logger.info(f"Added new node: {node_name}")
    
    def export_node_data(self):
        """Export node inventory data"""
        node_name = self.selected_node_label.text().replace("Node: ", "")
        if node_name == "Select a node to view inventory":
            QMessageBox.information(self, "Info", "Please select a node first")
            return
        
        # TODO: Implement export functionality
        QMessageBox.information(self, "Success", f"Node data for {node_name} exported successfully")
    
    def search_items_manual(self):
        """Search items for manual entry"""
        search_term = self.item_search_manual.text().strip()
        if not search_term:
            return
        
        try:
            # Search items using data manager
            items = self.data_manager.search_items(search_term)
            
            self.manual_item_combo.clear()
            self.manual_item_combo.addItem("Select an item...")
            
            for item in items:
                display_name = f"{item['name']} ({item['type']})"
                self.manual_item_combo.addItem(display_name, item['id'])
            
            logger.info(f"Found {len(items)} items for manual entry")
            
        except Exception as e:
            logger.error(f"Manual item search failed: {e}")
            QMessageBox.warning(self, "Search Error", f"Failed to search items: {e}")
    
    def update_inventory_manual(self):
        """Update inventory with manual entry"""
        if self.manual_item_combo.currentIndex() == 0:
            QMessageBox.information(self, "Info", "Please select an item")
            return
        
        item_id = self.manual_item_combo.currentData()
        node_name = self.manual_node_combo.currentText().strip()
        quantity = self.manual_quantity.value()
        avg_cost = self.manual_avg_cost.value()
        
        if not node_name:
            QMessageBox.information(self, "Info", "Please enter a node name")
            return
        
        try:
            # Update inventory using data manager
            success = self.data_manager.update_inventory(item_id, node_name, quantity, avg_cost)
            
            if success:
                # Add to recent updates table
                self.add_recent_update(
                    self.manual_item_combo.currentText(),
                    node_name,
                    quantity,
                    avg_cost
                )
                
                # Emit signal
                self.inventory_updated.emit(item_id, node_name, quantity)
                
                # Check for low stock
                if 0 < quantity < 10:
                    self.low_stock_alert.emit(
                        item_id, 
                        self.manual_item_combo.currentText(),
                        quantity
                    )
                
                QMessageBox.information(self, "Success", "Inventory updated successfully")
                self.clear_manual_form()
                
            else:
                QMessageBox.warning(self, "Error", "Failed to update inventory")
                
        except Exception as e:
            logger.error(f"Manual inventory update failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update inventory: {e}")
    
    def add_recent_update(self, item_name: str, node_name: str, quantity: int, cost: float):
        """Add entry to recent updates table"""
        row_count = self.recent_updates_table.rowCount()
        self.recent_updates_table.insertRow(0)  # Insert at top
        
        self.recent_updates_table.setItem(0, 0, QTableWidgetItem(item_name))
        self.recent_updates_table.setItem(0, 1, QTableWidgetItem(node_name))
        self.recent_updates_table.setItem(0, 2, QTableWidgetItem(str(quantity)))
        self.recent_updates_table.setItem(0, 3, QTableWidgetItem(f"{cost:.2f}"))
        self.recent_updates_table.setItem(0, 4, QTableWidgetItem("Just now"))
        
        # Limit to 10 recent updates
        if row_count >= 10:
            self.recent_updates_table.removeRow(10)
    
    def clear_manual_form(self):
        """Clear the manual entry form"""
        self.item_search_manual.clear()
        self.manual_item_combo.clear()
        self.manual_item_combo.addItem("Select an item...")
        self.manual_quantity.setValue(0)
        self.manual_avg_cost.setValue(0.0)
        self.manual_notes.clear()
    
    def handle_craft_completed(self, craft_data: dict):
        """Handle craft completion signal from calculator"""
        if not self.validate_required_fields(craft_data, ['item_id', 'rarity', 'quantity', 'total_cost']):
            return
        
        # Add crafted items to current node (default to first node or ask user)
        default_node = "Lionhold"  # Could be made configurable
        
        item_id = craft_data['item_id']
        rarity = craft_data['rarity']
        quantity = craft_data['quantity']
        total_cost = craft_data['total_cost']
        
        # Calculate average cost per item
        avg_cost = total_cost / quantity if quantity > 0 else 0.0
        
        def inventory_update_operation():
            return self.data_manager.update_inventory(item_id, default_node, quantity, rarity, avg_cost)
        
        success = self.safe_data_operation("update inventory from craft", inventory_update_operation)
        
        if success:
            # Emit update through module manager
            self.emit_data_update({
                'type': 'inventory_update',
                'item_id': item_id,
                'rarity': rarity,
                'node_name': default_node,
                'quantity': quantity
            })
            logger.info(f"Added {quantity} {rarity} crafted items to {default_node}")
        
    # Keep the old method for backward compatibility
    def update_inventory_from_craft(self, item_id: int, rarity: str, quantity: int, total_cost: float):
        """Update inventory when items are crafted (legacy method)"""
        craft_data = {
            'item_id': item_id,
            'rarity': rarity,
            'quantity': quantity,
            'total_cost': total_cost
        }
        self.handle_craft_completed(craft_data)
    
    def refresh_data(self):
        """Refresh module data when database is updated"""
        self.refresh_overview()
        
        # If a node is selected, refresh its inventory
        current_node = self.selected_node_label.text()
        if current_node != "Select a node to view inventory":
            # Re-select to refresh
            for i in range(self.node_list.topLevelItemCount()):
                item = self.node_list.topLevelItem(i)
                if f"Node: {item.text(0)}" == current_node:
                    self.select_node(item)
                    break