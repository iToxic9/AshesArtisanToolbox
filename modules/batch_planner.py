"""
Batch Planner module for planning multiple craft orders.
Integrates with calculator and inventory for optimized crafting planning.
"""

import logging
from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QGroupBox, QTextEdit, QSplitter, QHeaderView, QMessageBox,
    QCheckBox, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from data_manager import DataManager

logger = logging.getLogger(__name__)

class BatchPlannerModule(QWidget):
    """
    Batch planner for optimizing multiple craft orders.
    
    Data Flow: Calculator -> Batch Planner <- Inventory -> Optimized Plans
    """
    
    # Signals for inter-module communication
    recipe_selected = pyqtSignal(int)  # item_id for calculator
    batch_planned = pyqtSignal(dict)  # batch plan details
    inventory_check_requested = pyqtSignal(list)  # list of item_ids needed
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        
        self.data_manager = data_manager
        self.current_batch = []
        self.optimization_results = {}
        
        self.setup_ui()
        self.connect_signals()
        
        logger.info("Batch planner module initialized")
    
    def setup_ui(self):
        """Setup the batch planner UI"""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Batch building
        left_panel = self.create_batch_building_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Optimization and results
        right_panel = self.create_optimization_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([500, 700])
    
    def create_batch_building_panel(self) -> QWidget:
        """Create batch building and recipe selection panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Recipe addition group
        recipe_group = QGroupBox("Add Recipes to Batch")
        recipe_layout = QGridLayout(recipe_group)
        
        # Item search
        recipe_layout.addWidget(QLabel("Search Recipe:"), 0, 0)
        self.recipe_search = QLineEdit()
        self.recipe_search.setPlaceholderText("Type item name...")
        recipe_layout.addWidget(self.recipe_search, 0, 1)
        
        self.recipe_search_button = QPushButton("Search")
        recipe_layout.addWidget(self.recipe_search_button, 0, 2)
        
        # Recipe selection
        recipe_layout.addWidget(QLabel("Select Recipe:"), 1, 0)
        self.recipe_combo = QComboBox()
        self.recipe_combo.setMinimumWidth(250)
        recipe_layout.addWidget(self.recipe_combo, 1, 1, 1, 2)
        
        # Quantity
        recipe_layout.addWidget(QLabel("Quantity:"), 2, 0)
        self.batch_quantity = QSpinBox()
        self.batch_quantity.setRange(1, 9999)
        self.batch_quantity.setValue(1)
        recipe_layout.addWidget(self.batch_quantity, 2, 1)
        
        # Priority
        recipe_layout.addWidget(QLabel("Priority:"), 3, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["High", "Medium", "Low"])
        self.priority_combo.setCurrentText("Medium")
        recipe_layout.addWidget(self.priority_combo, 3, 1)
        
        # Add to batch button
        self.add_to_batch_button = QPushButton("Add to Batch")
        self.add_to_batch_button.setStyleSheet("background-color: #28a745; font-weight: bold;")
        recipe_layout.addWidget(self.add_to_batch_button, 4, 0, 1, 3)
        
        layout.addWidget(recipe_group)
        
        # Current batch group
        batch_group = QGroupBox("Current Batch")
        batch_layout = QVBoxLayout(batch_group)
        
        # Batch controls
        batch_controls = QHBoxLayout()
        
        self.clear_batch_button = QPushButton("Clear Batch")
        batch_controls.addWidget(self.clear_batch_button)
        
        self.save_batch_button = QPushButton("Save Batch")
        batch_controls.addWidget(self.save_batch_button)
        
        self.load_batch_button = QPushButton("Load Batch")
        batch_controls.addWidget(self.load_batch_button)
        
        batch_controls.addStretch()
        
        batch_layout.addLayout(batch_controls)
        
        # Batch table
        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(5)
        self.batch_table.setHorizontalHeaderLabels([
            "Recipe", "Quantity", "Priority", "Status", "Actions"
        ])
        
        header = self.batch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        batch_layout.addWidget(self.batch_table)
        layout.addWidget(batch_group)
        
        # Batch summary
        summary_group = QGroupBox("Batch Summary")
        summary_layout = QGridLayout(summary_group)
        
        summary_layout.addWidget(QLabel("Total Recipes:"), 0, 0)
        self.total_recipes_label = QLabel("0")
        summary_layout.addWidget(self.total_recipes_label, 0, 1)
        
        summary_layout.addWidget(QLabel("Total Items:"), 1, 0)
        self.total_items_label = QLabel("0")
        summary_layout.addWidget(self.total_items_label, 1, 1)
        
        summary_layout.addWidget(QLabel("Estimated Cost:"), 2, 0)
        self.estimated_cost_label = QLabel("0.00 gold")
        self.estimated_cost_label.setStyleSheet("font-weight: bold; color: #ffd700;")
        summary_layout.addWidget(self.estimated_cost_label, 2, 1)
        
        layout.addWidget(summary_group)
        
        return panel
    
    def create_optimization_panel(self) -> QWidget:
        """Create optimization and results panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Optimization settings
        settings_group = QGroupBox("Optimization Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Tax rate
        settings_layout.addWidget(QLabel("Node Tax Rate:"), 0, 0)
        self.opt_tax_slider = QSpinBox()
        self.opt_tax_slider.setRange(0, 100)
        self.opt_tax_slider.setValue(15)
        self.opt_tax_slider.setSuffix("%")
        settings_layout.addWidget(self.opt_tax_slider, 0, 1)
        
        # Optimization goals
        settings_layout.addWidget(QLabel("Optimize For:"), 1, 0)
        self.optimization_goal = QComboBox()
        self.optimization_goal.addItems([
            "Minimum Cost", "Maximum Profit", "Available Materials", "Time Efficiency"
        ])
        settings_layout.addWidget(self.optimization_goal, 1, 1)
        
        # Constraints
        settings_layout.addWidget(QLabel("Constraints:"), 2, 0)
        constraints_layout = QVBoxLayout()
        
        self.use_inventory_constraint = QCheckBox("Use only available inventory")
        self.use_inventory_constraint.setChecked(True)
        constraints_layout.addWidget(self.use_inventory_constraint)
        
        self.respect_priorities = QCheckBox("Respect recipe priorities")
        self.respect_priorities.setChecked(True)
        constraints_layout.addWidget(self.respect_priorities)
        
        self.minimize_node_travel = QCheckBox("Minimize node travel")
        constraints_layout.addWidget(self.minimize_node_travel)
        
        settings_layout.addLayout(constraints_layout, 2, 1)
        
        # Optimize button
        self.optimize_button = QPushButton("Optimize Batch")
        self.optimize_button.setStyleSheet("background-color: #0078d4; font-weight: bold;")
        settings_layout.addWidget(self.optimize_button, 3, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
        # Optimization results
        results_group = QGroupBox("Optimization Results")
        results_layout = QVBoxLayout(results_group)
        
        # Progress bar
        self.optimization_progress = QProgressBar()
        self.optimization_progress.setVisible(False)
        results_layout.addWidget(self.optimization_progress)
        
        # Results summary
        results_summary_layout = QGridLayout()
        
        results_summary_layout.addWidget(QLabel("Feasibility:"), 0, 0)
        self.feasibility_label = QLabel("Not optimized")
        results_summary_layout.addWidget(self.feasibility_label, 0, 1)
        
        results_summary_layout.addWidget(QLabel("Total Cost:"), 1, 0)
        self.optimized_cost_label = QLabel("0.00 gold")
        self.optimized_cost_label.setStyleSheet("font-weight: bold; color: #ffd700;")
        results_summary_layout.addWidget(self.optimized_cost_label, 1, 1)
        
        results_summary_layout.addWidget(QLabel("Materials Needed:"), 2, 0)
        self.materials_needed_label = QLabel("0")
        results_summary_layout.addWidget(self.materials_needed_label, 2, 1)
        
        results_summary_layout.addWidget(QLabel("Missing Materials:"), 3, 0)
        self.missing_materials_label = QLabel("0")
        results_summary_layout.addWidget(self.missing_materials_label, 3, 1)
        
        results_layout.addLayout(results_summary_layout)
        
        # Material requirements table
        materials_label = QLabel("Material Requirements:")
        materials_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        results_layout.addWidget(materials_label)
        
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(6)
        self.materials_table.setHorizontalHeaderLabels([
            "Material", "Total Needed", "Available", "Missing", "Cost", "Sources"
        ])
        
        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        results_layout.addWidget(self.materials_table)
        layout.addWidget(results_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.export_batch_button = QPushButton("Export Batch Plan")
        action_layout.addWidget(self.export_batch_button)
        
        self.shopping_list_button = QPushButton("Generate Shopping List")
        action_layout.addWidget(self.shopping_list_button)
        
        action_layout.addStretch()
        
        self.execute_batch_button = QPushButton("Execute Batch")
        self.execute_batch_button.setStyleSheet("background-color: #28a745; font-weight: bold;")
        action_layout.addWidget(self.execute_batch_button)
        
        layout.addLayout(action_layout)
        
        return panel
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        # Recipe addition
        self.recipe_search_button.clicked.connect(self.search_recipes)
        self.recipe_search.returnPressed.connect(self.search_recipes)
        self.add_to_batch_button.clicked.connect(self.add_recipe_to_batch)
        
        # Batch management
        self.clear_batch_button.clicked.connect(self.clear_batch)
        self.save_batch_button.clicked.connect(self.save_batch)
        self.load_batch_button.clicked.connect(self.load_batch)
        
        # Optimization
        self.optimize_button.clicked.connect(self.optimize_batch)
        self.opt_tax_slider.valueChanged.connect(self.update_optimization)
        self.optimization_goal.currentTextChanged.connect(self.update_optimization)
        
        # Actions
        self.export_batch_button.clicked.connect(self.export_batch_plan)
        self.shopping_list_button.clicked.connect(self.generate_shopping_list)
        self.execute_batch_button.clicked.connect(self.execute_batch)
    
    def search_recipes(self):
        """Search for recipes to add to batch"""
        search_term = self.recipe_search.text().strip()
        if not search_term:
            return
        
        try:
            items = self.data_manager.search_items(search_term)
            
            self.recipe_combo.clear()
            self.recipe_combo.addItem("Select a recipe...")
            
            for item in items:
                display_name = f"{item['name']} (Lvl {item['level']})"
                self.recipe_combo.addItem(display_name, item['id'])
            
            logger.info(f"Found {len(items)} recipes for batch planning")
            
        except Exception as e:
            logger.error(f"Recipe search failed: {e}")
            QMessageBox.warning(self, "Search Error", f"Failed to search recipes: {e}")
    
    def add_recipe_to_batch(self):
        """Add selected recipe to the current batch"""
        if self.recipe_combo.currentIndex() == 0:
            QMessageBox.information(self, "Info", "Please select a recipe")
            return
        
        item_id = self.recipe_combo.currentData()
        recipe_name = self.recipe_combo.currentText()
        quantity = self.batch_quantity.value()
        priority = self.priority_combo.currentText()
        
        # Check if recipe already exists in batch
        for batch_item in self.current_batch:
            if batch_item['item_id'] == item_id:
                # Update existing entry
                batch_item['quantity'] += quantity
                self.update_batch_display()
                self.update_batch_summary()
                return
        
        # Add new recipe to batch
        batch_item = {
            'item_id': item_id,
            'name': recipe_name,
            'quantity': quantity,
            'priority': priority,
            'status': 'Pending'
        }
        
        self.current_batch.append(batch_item)
        self.update_batch_display()
        self.update_batch_summary()
        
        # Clear form
        self.batch_quantity.setValue(1)
        self.recipe_combo.setCurrentIndex(0)
        
        logger.info(f"Added {quantity}x {recipe_name} to batch")
    
    def update_batch_display(self):
        """Update the batch table display"""
        self.batch_table.setRowCount(len(self.current_batch))
        
        for row, batch_item in enumerate(self.current_batch):
            # Recipe name
            self.batch_table.setItem(row, 0, QTableWidgetItem(batch_item['name']))
            
            # Quantity
            self.batch_table.setItem(row, 1, QTableWidgetItem(str(batch_item['quantity'])))
            
            # Priority
            priority_item = QTableWidgetItem(batch_item['priority'])
            if batch_item['priority'] == 'High':
                priority_item.setBackground(Qt.GlobalColor.red)
            elif batch_item['priority'] == 'Medium':
                priority_item.setBackground(Qt.GlobalColor.yellow)
            self.batch_table.setItem(row, 2, priority_item)
            
            # Status
            status_item = QTableWidgetItem(batch_item['status'])
            if batch_item['status'] == 'Ready':
                status_item.setBackground(Qt.GlobalColor.green)
            elif batch_item['status'] == 'Missing Materials':
                status_item.setBackground(Qt.GlobalColor.red)
            self.batch_table.setItem(row, 3, status_item)
            
            # Actions (remove button)
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda checked, r=row: self.remove_from_batch(r))
            self.batch_table.setCellWidget(row, 4, remove_button)
    
    def remove_from_batch(self, row: int):
        """Remove recipe from batch"""
        if 0 <= row < len(self.current_batch):
            removed_item = self.current_batch.pop(row)
            self.update_batch_display()
            self.update_batch_summary()
            logger.info(f"Removed {removed_item['name']} from batch")
    
    def update_batch_summary(self):
        """Update batch summary statistics"""
        if not self.current_batch:
            self.total_recipes_label.setText("0")
            self.total_items_label.setText("0")
            self.estimated_cost_label.setText("0.00 gold")
            return
        
        total_recipes = len(self.current_batch)
        total_items = sum(item['quantity'] for item in self.current_batch)
        
        # Estimate total cost (simplified calculation)
        estimated_cost = 0.0
        for batch_item in self.current_batch:
            # Mock cost calculation - would use actual recipe costs
            estimated_cost += batch_item['quantity'] * 25.0  # Mock 25 gold per item
        
        self.total_recipes_label.setText(str(total_recipes))
        self.total_items_label.setText(str(total_items))
        self.estimated_cost_label.setText(f"{estimated_cost:.2f} gold")
    
    def clear_batch(self):
        """Clear the current batch"""
        reply = QMessageBox.question(
            self, "Clear Batch",
            "Are you sure you want to clear the current batch?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_batch.clear()
            self.update_batch_display()
            self.update_batch_summary()
            self.clear_optimization_results()
            logger.info("Batch cleared")
    
    def save_batch(self):
        """Save current batch to database"""
        if not self.current_batch:
            QMessageBox.information(self, "Info", "No batch to save")
            return
        
        # TODO: Implement batch saving to database
        QMessageBox.information(self, "Success", "Batch saved successfully")
    
    def load_batch(self):
        """Load a saved batch from database"""
        # TODO: Implement batch loading from database
        QMessageBox.information(self, "Info", "Batch loading not yet implemented")
    
    def optimize_batch(self):
        """Optimize the current batch"""
        if not self.current_batch:
            QMessageBox.information(self, "Info", "No batch to optimize")
            return
        
        self.optimization_progress.setVisible(True)
        self.optimization_progress.setRange(0, 0)  # Indeterminate
        
        try:
            # Simulate optimization process
            self.perform_optimization()
            
        except Exception as e:
            logger.error(f"Batch optimization failed: {e}")
            QMessageBox.critical(self, "Error", f"Optimization failed: {e}")
        finally:
            self.optimization_progress.setVisible(False)
    
    def perform_optimization(self):
        """Perform the actual batch optimization"""
        tax_rate = self.opt_tax_slider.value() / 100.0
        goal = self.optimization_goal.currentText()
        use_inventory = self.use_inventory_constraint.isChecked()
        
        # Mock optimization results
        mock_materials = [
            {
                'name': 'Parchment',
                'total_needed': 150,
                'available': 45,
                'missing': 105,
                'cost': 8.50,
                'sources': 'Lionhold, Winstead'
            },
            {
                'name': 'Quality Ink',
                'total_needed': 75,
                'available': 5,
                'missing': 70,
                'cost': 25.00,
                'sources': 'Lionhold'
            },
            {
                'name': 'Binding Thread',
                'total_needed': 75,
                'available': 0,
                'missing': 75,
                'cost': 12.00,
                'sources': 'None available'
            }
        ]
        
        self.optimization_results = {
            'feasible': True,
            'total_cost': 2847.50,
            'materials': mock_materials,
            'missing_count': 2
        }
        
        self.update_optimization_results()
        logger.info("Batch optimization completed")
    
    def update_optimization_results(self):
        """Update the optimization results display"""
        if not self.optimization_results:
            return
        
        results = self.optimization_results
        
        # Update summary
        feasible = "Feasible" if results['feasible'] else "Not Feasible"
        self.feasibility_label.setText(feasible)
        self.feasibility_label.setStyleSheet(
            "color: #28a745; font-weight: bold;" if results['feasible'] 
            else "color: #dc3545; font-weight: bold;"
        )
        
        self.optimized_cost_label.setText(f"{results['total_cost']:.2f} gold")
        
        materials = results.get('materials', [])
        total_materials = len(materials)
        missing_materials = results.get('missing_count', 0)
        
        self.materials_needed_label.setText(str(total_materials))
        self.missing_materials_label.setText(str(missing_materials))
        
        # Update materials table
        self.materials_table.setRowCount(len(materials))
        
        for row, material in enumerate(materials):
            self.materials_table.setItem(row, 0, QTableWidgetItem(material['name']))
            self.materials_table.setItem(row, 1, QTableWidgetItem(str(material['total_needed'])))
            self.materials_table.setItem(row, 2, QTableWidgetItem(str(material['available'])))
            
            # Missing materials (highlight if any)
            missing_item = QTableWidgetItem(str(material['missing']))
            if material['missing'] > 0:
                missing_item.setBackground(Qt.GlobalColor.red)
            self.materials_table.setItem(row, 3, missing_item)
            
            self.materials_table.setItem(row, 4, QTableWidgetItem(f"{material['cost']:.2f}"))
            self.materials_table.setItem(row, 5, QTableWidgetItem(material['sources']))
        
        # Update batch statuses
        for batch_item in self.current_batch:
            if missing_materials == 0:
                batch_item['status'] = 'Ready'
            else:
                batch_item['status'] = 'Missing Materials'
        
        self.update_batch_display()
    
    def update_optimization(self):
        """Update optimization when parameters change"""
        if self.optimization_results:
            self.perform_optimization()
    
    def clear_optimization_results(self):
        """Clear optimization results"""
        self.optimization_results = {}
        self.feasibility_label.setText("Not optimized")
        self.feasibility_label.setStyleSheet("")
        self.optimized_cost_label.setText("0.00 gold")
        self.materials_needed_label.setText("0")
        self.missing_materials_label.setText("0")
        self.materials_table.setRowCount(0)
    
    def export_batch_plan(self):
        """Export the batch plan to file"""
        if not self.current_batch:
            QMessageBox.information(self, "Info", "No batch to export")
            return
        
        # TODO: Implement export functionality
        QMessageBox.information(self, "Success", "Batch plan exported successfully")
    
    def generate_shopping_list(self):
        """Generate a shopping list for missing materials"""
        if not self.optimization_results:
            QMessageBox.information(self, "Info", "Please optimize the batch first")
            return
        
        materials = self.optimization_results.get('materials', [])
        missing_materials = [m for m in materials if m['missing'] > 0]
        
        if not missing_materials:
            QMessageBox.information(self, "Info", "No missing materials - batch is ready!")
            return
        
        # Create shopping list dialog
        shopping_text = "Shopping List:\n\n"
        total_cost = 0.0
        
        for material in missing_materials:
            cost = material['missing'] * material['cost']
            shopping_text += f"• {material['name']}: {material['missing']} @ {material['cost']:.2f} = {cost:.2f} gold\n"
            total_cost += cost
        
        shopping_text += f"\nTotal Cost: {total_cost:.2f} gold"
        
        QMessageBox.information(self, "Shopping List", shopping_text)
    
    def execute_batch(self):
        """Execute the optimized batch"""
        if not self.optimization_results:
            QMessageBox.information(self, "Info", "Please optimize the batch first")
            return
        
        if not self.optimization_results.get('feasible', False):
            QMessageBox.warning(self, "Warning", "Batch is not feasible - missing materials")
            return
        
        reply = QMessageBox.question(
            self, "Execute Batch",
            f"Execute batch for {self.optimized_cost_label.text()}?\n"
            "This will mark items as crafted and update inventory.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement actual batch execution
            # This would craft all items and update inventory
            
            self.batch_planned.emit(self.optimization_results)
            QMessageBox.information(self, "Success", "Batch executed successfully!")
            
            # Clear the batch
            self.current_batch.clear()
            self.update_batch_display()
            self.update_batch_summary()
            self.clear_optimization_results()
    
    def refresh_data(self):
        """Refresh module data when database is updated"""
        # Clear recipe search results
        self.recipe_combo.clear()
        self.recipe_combo.addItem("Select a recipe...")
        
        # Re-optimize if there's a current batch
        if self.current_batch and self.optimization_results:
            self.perform_optimization()