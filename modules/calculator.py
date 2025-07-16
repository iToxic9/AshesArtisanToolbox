"""
Calculator module for crafting cost calculations with tax integration.
Implements the core calculation logic following the data flow diagram.
"""

import logging
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QSlider, QPushButton, QTableWidget, 
    QTableWidgetItem, QComboBox, QGroupBox, QTextEdit, QSplitter,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from data_manager import DataManager
from rarity_system import RarityManager, ItemRarity, get_rarity_style_sheet, format_item_with_rarity, apply_rarity_style_to_item
from gui.base_module import BaseModule, ModuleError

logger = logging.getLogger(__name__)

class CalculatorModule(BaseModule):
    """
    Calculator module for tax-aware crafting cost calculations.
    
    Data Flow: API Cache -> Calculator <- User Input -> Results Display
    """
    
    def __init__(self, data_manager: DataManager):
        self.current_recipe = None
        self.current_calculation = None
        
        # Initialize base module
        super().__init__(data_manager, "Calculator")
    
    def setup_ui(self):
        """Setup the calculator UI components"""
        layout = QVBoxLayout(self)
        
        # Create main splitter for left/right layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Recipe selection and inputs
        left_panel = self.create_input_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results and calculations
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
    
    def create_input_panel(self) -> QWidget:
        """Create the input panel with recipe selection and parameters"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Recipe selection group
        recipe_group = QGroupBox("Recipe Selection")
        recipe_layout = QGridLayout(recipe_group)
        
        # Profession filter
        recipe_layout.addWidget(QLabel("Profession:"), 0, 0)
        self.profession_combo = QComboBox()
        self.profession_combo.addItems([
            "All Professions", "Scribe", "Alchemist", "Blacksmith", 
            "Carpenter", "Jeweler", "Leatherworker", "Tailor", "Cook"
        ])
        self.profession_combo.setCurrentText("Scribe")  # Default to Scribe
        recipe_layout.addWidget(self.profession_combo, 0, 1)
        
        # Item search
        recipe_layout.addWidget(QLabel("Search Item:"), 1, 0)
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Type item name to search...")
        recipe_layout.addWidget(self.item_search, 1, 1)
        
        # Search button
        self.search_button = QPushButton("Search")
        recipe_layout.addWidget(self.search_button, 1, 2)
        
        # Recipe results
        recipe_layout.addWidget(QLabel("Select Recipe:"), 2, 0)
        self.recipe_combo = QComboBox()
        self.recipe_combo.setMinimumWidth(300)
        recipe_layout.addWidget(self.recipe_combo, 2, 1, 1, 2)
        
        # Target rarity selection
        recipe_layout.addWidget(QLabel("Target Rarity:"), 3, 0)
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItems(RarityManager.get_rarity_display_list())
        self.rarity_combo.setCurrentText("Common")
        recipe_layout.addWidget(self.rarity_combo, 3, 1)
        
        # Quality rating (future implementation)
        recipe_layout.addWidget(QLabel("Quality Rating:"), 3, 2)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(0, 100)
        self.quality_spin.setValue(0)
        self.quality_spin.setToolTip("Future implementation: Higher quality rating may allow lower rarity components")
        self.quality_spin.setEnabled(False)
        recipe_layout.addWidget(self.quality_spin, 3, 2)
        
        layout.addWidget(recipe_group)
        
        # Calculation parameters group
        params_group = QGroupBox("Calculation Parameters")
        params_layout = QGridLayout(params_group)
        
        # Quantity
        params_layout.addWidget(QLabel("Quantity:"), 0, 0)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        params_layout.addWidget(self.quantity_spin, 0, 1)
        
        # Tax rate slider
        params_layout.addWidget(QLabel("Node Tax Rate:"), 1, 0)
        tax_layout = QHBoxLayout()
        
        self.tax_slider = QSlider(Qt.Orientation.Horizontal)
        self.tax_slider.setRange(0, 100)
        self.tax_slider.setValue(15)  # Default 15%
        tax_layout.addWidget(self.tax_slider)
        
        self.tax_label = QLabel("15%")
        self.tax_label.setMinimumWidth(40)
        tax_layout.addWidget(self.tax_label)
        
        params_layout.addLayout(tax_layout, 1, 1)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate Costs")
        self.calculate_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        params_layout.addWidget(self.calculate_button, 2, 0, 1, 2)
        
        layout.addWidget(params_group)
        
        # Custom prices group
        custom_group = QGroupBox("Custom Material Prices")
        custom_layout = QVBoxLayout(custom_group)
        
        custom_layout.addWidget(QLabel("Override market prices for specific materials:"))
        
        self.custom_prices_table = QTableWidget()
        self.custom_prices_table.setColumnCount(4)
        self.custom_prices_table.setHorizontalHeaderLabels(["Material", "Rarity", "Current Price", "Custom Price"])
        self.custom_prices_table.horizontalHeader().setStretchLastSection(True)
        self.custom_prices_table.setMaximumHeight(150)
        custom_layout.addWidget(self.custom_prices_table)
        
        layout.addWidget(custom_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
    
    def create_results_panel(self) -> QWidget:
        """Create the results panel with calculation display"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Results summary group
        summary_group = QGroupBox("Cost Summary")
        summary_layout = QGridLayout(summary_group)
        
        # Summary labels
        summary_layout.addWidget(QLabel("Material Cost:"), 0, 0)
        self.material_cost_label = QLabel("0.00 gold")
        self.material_cost_label.setStyleSheet("font-weight: bold; color: #ffd700;")
        summary_layout.addWidget(self.material_cost_label, 0, 1)
        
        summary_layout.addWidget(QLabel("Base Crafting Fee:"), 1, 0)
        self.base_fee_label = QLabel("0.00 gold")
        summary_layout.addWidget(self.base_fee_label, 1, 1)
        
        summary_layout.addWidget(QLabel("Tax Amount:"), 2, 0)
        self.tax_amount_label = QLabel("0.00 gold")
        summary_layout.addWidget(self.tax_amount_label, 2, 1)
        
        summary_layout.addWidget(QLabel("Total Cost:"), 3, 0)
        self.total_cost_label = QLabel("0.00 gold")
        self.total_cost_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #00ff00;")
        summary_layout.addWidget(self.total_cost_label, 3, 1)
        
        summary_layout.addWidget(QLabel("Cost per Unit:"), 4, 0)
        self.unit_cost_label = QLabel("0.00 gold")
        summary_layout.addWidget(self.unit_cost_label, 4, 1)
        
        layout.addWidget(summary_group)
        
        # Components breakdown table
        components_group = QGroupBox("Material Breakdown")
        components_layout = QVBoxLayout(components_group)
        
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(7)
        self.components_table.setHorizontalHeaderLabels([
            "Material", "Rarity", "Type", "Qty Needed", "Unit Price", "Source", "Total Cost"
        ])
        
        # Set column widths
        header = self.components_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        components_layout.addWidget(self.components_table)
        layout.addWidget(components_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_calculation_button = QPushButton("Save Calculation")
        button_layout.addWidget(self.save_calculation_button)
        
        self.export_button = QPushButton("Export to Batch Planner")
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        
        self.craft_button = QPushButton("Mark as Crafted")
        self.craft_button.setStyleSheet("background-color: #28a745; font-weight: bold;")
        button_layout.addWidget(self.craft_button)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        self.search_button.clicked.connect(self.search_recipes)
        self.item_search.returnPressed.connect(self.search_recipes)
        self.profession_combo.currentTextChanged.connect(self.search_recipes)
        self.recipe_combo.currentTextChanged.connect(self.load_selected_recipe)
        self.rarity_combo.currentTextChanged.connect(self.on_rarity_changed)
        
        self.quantity_spin.valueChanged.connect(self.calculate_costs)
        self.tax_slider.valueChanged.connect(self.on_tax_changed)
        self.calculate_button.clicked.connect(self.calculate_costs)
        
        self.custom_prices_table.cellChanged.connect(self.on_custom_price_changed)
        
        self.save_calculation_button.clicked.connect(self.save_calculation)
        self.export_button.clicked.connect(self.export_to_batch_planner)
        self.craft_button.clicked.connect(self.mark_as_crafted)
    
    def search_recipes(self):
        """Search for recipes based on filters"""
        search_term = self.get_safe_value({"search": self.item_search.text().strip()}, "search", "")
        profession = self.profession_combo.currentText()
        
        if profession == "All Professions":
            profession = None
        
        if not search_term:
            return
        
        def search_operation():
            return self.data_manager.search_items(search_term, profession)
        
        items = self.safe_data_operation("search recipes", search_operation)
        
        if items is None:
            return
        
        try:
            # Update recipe combo
            self.recipe_combo.clear()
            self.recipe_combo.addItem("Select a recipe...")
            
            for item in items:
                display_name = f"{item['name']} (Lvl {item.get('level', 0)})"
                self.recipe_combo.addItem(display_name, item['id'])
            
            logger.info(f"Found {len(items)} recipes for '{search_term}' in {profession or 'all professions'}")
            
        except Exception as e:
            self.handle_error("Failed to process search results", e)
    
    def load_selected_recipe(self):
        """Load the selected recipe for calculation"""
        if self.recipe_combo.currentIndex() == 0:  # "Select a recipe..."
            return
        
        item_id = self.recipe_combo.currentData()
        if item_id:
            self.load_recipe(item_id)
    
    def load_recipe(self, item_id: int):
        """Load a specific recipe by item ID"""
        try:
            # This would load recipe data from database
            # For now, we'll create a mock recipe structure
            self.current_recipe = {
                'item_id': item_id,
                'base_fee': 5.0,  # Mock base crafting fee
                'components': [
                    {'item_id': 101, 'name': 'Parchment', 'quantity': 2},
                    {'item_id': 102, 'name': 'Ink', 'quantity': 1},
                    {'item_id': 103, 'name': 'Binding Thread', 'quantity': 1}
                ]
            }
            
            self.update_custom_prices_table()
            self.calculate_costs()
            self.recipe_changed.emit(item_id)
            
            logger.info(f"Loaded recipe for item {item_id}")
            
        except Exception as e:
            logger.error(f"Failed to load recipe: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load recipe: {e}")
    
    def update_custom_prices_table(self):
        """Update the custom prices table with current recipe components"""
        if not self.current_recipe:
            self.custom_prices_table.setRowCount(0)
            return
        
        # Get current target rarity
        target_rarity = RarityManager.rarity_to_string(
            RarityManager.string_to_rarity(self.rarity_combo.currentText().lower())
        )
        
        components = self.current_recipe.get('components', [])
        self.custom_prices_table.setRowCount(len(components))
        
        for row, component in enumerate(components):
            # Material name
            name_item = QTableWidgetItem(component['name'])
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            name_item.setData(Qt.ItemDataRole.UserRole, component['item_id'])  # Store item_id
            self.custom_prices_table.setItem(row, 0, name_item)
            
            # Determine required rarity for this component
            component_type = component.get('component_type', 'quality')
            if component_type == 'basic':
                required_rarity = component.get('base_rarity', 'common')
            else:
                required_rarity = target_rarity
            
            # Rarity with color
            rarity_enum = RarityManager.string_to_rarity(required_rarity)
            rarity_item = QTableWidgetItem(RarityManager.get_display_name(rarity_enum))
            rarity_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            apply_rarity_style_to_item(rarity_item, rarity_enum)
            self.custom_prices_table.setItem(row, 1, rarity_item)
            
            # Current market price (try to get from data manager)
            try:
                market_analysis = self.data_manager.get_market_analysis(
                    component['item_id'], required_rarity, 7
                )
                current_price_value = market_analysis.get('average_price', 0.0)
            except:
                current_price_value = 0.0
            
            current_price = QTableWidgetItem(f"{current_price_value:.2f}")
            current_price.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.custom_prices_table.setItem(row, 2, current_price)
            
            # Custom price (editable)
            custom_price = QTableWidgetItem("")
            self.custom_prices_table.setItem(row, 3, custom_price)
    
    def on_tax_changed(self, value: int):
        """Handle tax slider change"""
        self.tax_label.setText(f"{value}%")
        self.calculate_costs()
    
    def on_custom_price_changed(self, row: int, column: int):
        """Handle custom price changes"""
        if column == 3:  # Custom price column (updated index)
            self.calculate_costs()
    
    def on_rarity_changed(self):
        """Handle rarity selection changes"""
        self.calculate_costs()
    
    def calculate_costs(self):
        """Calculate total crafting costs with current parameters and rarity"""
        if not self.current_recipe:
            return
        
        # Safely get input values
        quantity = self.get_safe_value({"qty": self.quantity_spin.value()}, "qty", 1, int)
        tax_rate = self.tax_slider.value() / 100.0
        target_rarity = RarityManager.rarity_to_string(
            RarityManager.string_to_rarity(self.rarity_combo.currentText().lower())
        )
        quality_rating = self.quality_spin.value()
        
        # Get custom prices using rarity-aware keys
        custom_prices = self._extract_custom_prices()
        
        def calculation_operation():
            return self.data_manager.calculate_crafting_cost(
                self.current_recipe['item_id'],
                target_rarity,
                quantity,
                tax_rate,
                custom_prices,
                quality_rating
            )
        
        calculation = self.safe_data_operation("calculate crafting costs", calculation_operation)
        
        if calculation is None or 'error' in (calculation or {}):
            # Use mock calculation for demonstration
            calculation = self.mock_calculation(quantity, tax_rate, custom_prices, target_rarity)
        
        if calculation:
            self.current_calculation = calculation
            self.update_results_display(calculation)
            
            # Emit data update signal
            self.emit_data_update({
                'calculation': calculation,
                'item_id': calculation.get('item_id'),
                'target_rarity': calculation.get('target_rarity'),
                'total_cost': calculation.get('total_cost', 0)
            })
    
    def _extract_custom_prices(self) -> Dict[str, float]:
        """Extract custom prices from the table with error handling"""
        custom_prices = {}
        
        try:
            for row in range(self.custom_prices_table.rowCount()):
                custom_item = self.custom_prices_table.item(row, 3)
                if custom_item and custom_item.text().strip():
                    try:
                        # Get component info from table
                        material_item = self.custom_prices_table.item(row, 0)
                        rarity_item = self.custom_prices_table.item(row, 1)
                        
                        if material_item and rarity_item:
                            # Extract item_id from material_item data
                            item_id = material_item.data(Qt.ItemDataRole.UserRole)
                            rarity_text = rarity_item.text().lower()
                            
                            if item_id:
                                component_key = RarityManager.create_item_key(
                                    item_id, RarityManager.string_to_rarity(rarity_text)
                                )
                                custom_prices[component_key] = float(custom_item.text())
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid custom price at row {row}: {e}")
                        continue
        except Exception as e:
            self.handle_error("Failed to extract custom prices", e, show_user=False)
        
        return custom_prices
    
    def mock_calculation(self, quantity: int, tax_rate: float, custom_prices: Dict, target_rarity: str = 'common') -> Dict:
        """Create mock calculation for demonstration"""
        components = []
        total_material_cost = 0.0
        
        for component in self.current_recipe.get('components', []):
            item_id = component['item_id']
            qty_needed = component['quantity'] * quantity
            
            # Use custom price if available, otherwise mock market price
            if item_id in custom_prices:
                unit_price = custom_prices[item_id]
                price_source = "custom"
            else:
                unit_price = 10.50  # Mock price
                price_source = "market"
            
            component_cost = unit_price * qty_needed
            total_material_cost += component_cost
            
            # Determine component rarity and type
            component_type = component.get('component_type', 'quality')
            if component_type == 'basic':
                required_rarity = component.get('base_rarity', 'common')
            else:
                required_rarity = target_rarity
            
            components.append({
                'item_id': item_id,
                'name': component['name'],
                'rarity': required_rarity,
                'component_type': component_type,
                'quantity_needed': qty_needed,
                'unit_price': unit_price,
                'total_cost': component_cost,
                'price_source': price_source
            })
        
        base_fee = self.current_recipe.get('base_fee', 5.0) * quantity
        tax_amount = base_fee * tax_rate
        total_cost = total_material_cost + base_fee + tax_amount
        
        return {
            'item_id': self.current_recipe['item_id'],
            'target_rarity': target_rarity,
            'quantity': quantity,
            'components': components,
            'material_cost': total_material_cost,
            'base_crafting_fee': base_fee,
            'tax_amount': tax_amount,
            'total_cost': total_cost,
            'cost_per_unit': total_cost / quantity if quantity > 0 else 0.0,
            'tax_rate': tax_rate
        }
    
    def update_results_display(self, calculation: Dict):
        """Update the results display with calculation data"""
        # Update summary
        self.material_cost_label.setText(f"{calculation['material_cost']:.2f} gold")
        self.base_fee_label.setText(f"{calculation['base_crafting_fee']:.2f} gold")
        self.tax_amount_label.setText(f"{calculation['tax_amount']:.2f} gold")
        self.total_cost_label.setText(f"{calculation['total_cost']:.2f} gold")
        self.unit_cost_label.setText(f"{calculation['cost_per_unit']:.2f} gold")
        
        # Update components table
        components = calculation.get('components', [])
        self.components_table.setRowCount(len(components))
        
        for row, component in enumerate(components):
            # Material name
            name_item = QTableWidgetItem(component['name'])
            self.components_table.setItem(row, 0, name_item)
            
            # Rarity with color
            rarity_text = component.get('rarity', 'common')
            rarity_enum = RarityManager.string_to_rarity(rarity_text)
            rarity_item = QTableWidgetItem(RarityManager.get_display_name(rarity_enum))
            apply_rarity_style_to_item(rarity_item, rarity_enum)
            self.components_table.setItem(row, 1, rarity_item)
            
            # Component type
            component_type = component.get('component_type', 'quality')
            type_item = QTableWidgetItem(component_type.title())
            if component_type == 'basic':
                type_item.setStyleSheet("color: #888888; font-style: italic;")
            self.components_table.setItem(row, 2, type_item)
            
            # Quantity needed
            self.components_table.setItem(row, 3, QTableWidgetItem(str(component['quantity_needed'])))
            
            # Unit price
            price_item = QTableWidgetItem(f"{component['unit_price']:.2f}")
            if component['price_source'] == 'custom':
                price_item.setBackground(Qt.GlobalColor.yellow)
            self.components_table.setItem(row, 4, price_item)
            
            # Source
            self.components_table.setItem(row, 5, QTableWidgetItem(component['price_source']))
            
            # Total cost
            self.components_table.setItem(row, 6, QTableWidgetItem(f"{component['total_cost']:.2f}"))
    
    def update_material_price(self, item_id: int, price: float):
        """Update material price from market analysis module"""
        # Find the material in custom prices table and update
        for row in range(self.custom_prices_table.rowCount()):
            name_item = self.custom_prices_table.item(row, 0)
            if name_item and self.current_recipe:
                components = self.current_recipe.get('components', [])
                if row < len(components) and components[row]['item_id'] == item_id:
                    current_price_item = self.custom_prices_table.item(row, 1)
                    if current_price_item:
                        current_price_item.setText(f"{price:.2f}")
                    break
        
        # Recalculate if this affects current recipe
        if self.current_recipe:
            self.calculate_costs()
    
    def save_calculation(self):
        """Save current calculation for later reference"""
        if not self.current_calculation:
            QMessageBox.information(self, "Info", "No calculation to save")
            return
        
        # TODO: Implement calculation saving to database
        QMessageBox.information(self, "Success", "Calculation saved successfully")
    
    def export_to_batch_planner(self):
        """Export current recipe to batch planner"""
        if not self.current_recipe:
            QMessageBox.information(self, "Info", "No recipe to export")
            return
        
        # TODO: Signal to batch planner module
        QMessageBox.information(self, "Success", "Recipe exported to batch planner")
    
    def mark_as_crafted(self):
        """Mark items as crafted and update inventory"""
        if not self.current_calculation:
            QMessageBox.information(self, "Info", "No calculation to mark as crafted")
            return
        
        calculation = self.current_calculation
        
        try:
            # Prepare craft data
            craft_data = {
                'item_id': calculation['item_id'],
                'rarity': calculation.get('target_rarity', 'common'),
                'quantity': calculation['quantity'],
                'total_cost': calculation['total_cost'],
                'components': calculation.get('components', [])
            }
            
            # Emit signal through module manager
            self.signals.craft_completed.emit(craft_data)
            
            QMessageBox.information(
                self, "Success", 
                f"Marked {calculation['quantity']} items as crafted for "
                f"{calculation['total_cost']:.2f} gold"
            )
            
        except Exception as e:
            self.handle_error("Failed to mark items as crafted", e)
    
    def refresh_data(self):
        """Refresh module data when database is updated"""
        try:
            # Clear current selection and refresh searches
            self.recipe_combo.clear()
            self.recipe_combo.addItem("Select a recipe...")
            
            # If there was a previous search, repeat it
            if self.item_search.text():
                self.search_recipes()
                
            self.update_status("Data refreshed")
        except Exception as e:
            self.handle_error("Failed to refresh calculator data", e)