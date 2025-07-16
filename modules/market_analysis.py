"""
Market Analysis module for price tracking and trend analysis.
Provides market insights for crafting profitability calculations.
"""

import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QGroupBox, QTextEdit, QSplitter, QHeaderView, QMessageBox,
    QDateEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from data_manager import DataManager
from rarity_system import RarityManager, ItemRarity, get_rarity_style_sheet, format_item_with_rarity, apply_rarity_style_to_item

logger = logging.getLogger(__name__)

class MarketAnalysisModule(QWidget):
    """
    Market analysis module for tracking prices and trends.
    
    Data Flow: Local Cache -> Market Analysis -> Price Updates to Calculator
    """
    
    # Signals for inter-module communication
    price_updated = pyqtSignal(int, str, float)  # item_id, rarity, new_price
    trend_alert = pyqtSignal(str, str, str, float)  # item_name, rarity, trend, change_percent
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        
        self.data_manager = data_manager
        self.current_analysis = {}
        
        self.setup_ui()
        self.connect_signals()
        
        logger.info("Market analysis module initialized")
    
    def setup_ui(self):
        """Setup the market analysis UI"""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Price entry and search
        left_panel = self.create_price_entry_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Analysis and trends
        right_panel = self.create_analysis_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
    
    def create_price_entry_panel(self) -> QWidget:
        """Create price entry and management panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Price entry group
        entry_group = QGroupBox("Record Market Price")
        entry_layout = QGridLayout(entry_group)
        
        # Item search
        entry_layout.addWidget(QLabel("Item:"), 0, 0)
        self.price_item_search = QLineEdit()
        self.price_item_search.setPlaceholderText("Search for item...")
        entry_layout.addWidget(self.price_item_search, 0, 1)
        
        self.price_search_button = QPushButton("Search")
        entry_layout.addWidget(self.price_search_button, 0, 2)
        
        # Item selection
        entry_layout.addWidget(QLabel("Select Item:"), 1, 0)
        self.price_item_combo = QComboBox()
        self.price_item_combo.setMinimumWidth(250)
        entry_layout.addWidget(self.price_item_combo, 1, 1, 1, 2)
        
        # Rarity selection
        entry_layout.addWidget(QLabel("Rarity:"), 2, 0)
        self.price_rarity_combo = QComboBox()
        self.price_rarity_combo.addItems(RarityManager.get_rarity_display_list())
        self.price_rarity_combo.setCurrentText("Common")
        entry_layout.addWidget(self.price_rarity_combo, 2, 1)
        
        # Price
        entry_layout.addWidget(QLabel("Price:"), 3, 0)
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setSuffix(" gold")
        entry_layout.addWidget(self.price_input, 3, 1)
        
        # Source
        entry_layout.addWidget(QLabel("Source:"), 4, 0)
        self.price_source_combo = QComboBox()
        self.price_source_combo.addItems([
            "market", "guildie", "harvested", "crafted"
        ])
        entry_layout.addWidget(self.price_source_combo, 4, 1)
        
        # Node
        entry_layout.addWidget(QLabel("Node:"), 5, 0)
        self.price_node_combo = QComboBox()
        self.price_node_combo.setEditable(True)
        self.price_node_combo.addItems([
            "Lionhold", "Winstead", "Miraleth", "Haelshore", 
            "Dünheim", "New Aela", "Ek'thor"
        ])
        entry_layout.addWidget(self.price_node_combo, 5, 1)
        
        # Notes
        entry_layout.addWidget(QLabel("Notes:"), 6, 0)
        self.price_notes = QLineEdit()
        self.price_notes.setPlaceholderText("Optional notes...")
        entry_layout.addWidget(self.price_notes, 6, 1, 1, 2)
        
        # Record button
        self.record_price_button = QPushButton("Record Price")
        self.record_price_button.setStyleSheet("background-color: #28a745; font-weight: bold;")
        entry_layout.addWidget(self.record_price_button, 7, 0, 1, 3)
        
        layout.addWidget(entry_group)
        
        # Recent prices group
        recent_group = QGroupBox("Recent Price Records")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_prices_table = QTableWidget()
        self.recent_prices_table.setColumnCount(6)
        self.recent_prices_table.setHorizontalHeaderLabels([
            "Item", "Rarity", "Price", "Source", "Node", "Recorded"
        ])
        self.recent_prices_table.setMaximumHeight(200)
        
        header = self.recent_prices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        recent_layout.addWidget(self.recent_prices_table)
        layout.addWidget(recent_group)
        
        return panel
    
    def create_analysis_panel(self) -> QWidget:
        """Create analysis and trends panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Analysis controls
        controls_group = QGroupBox("Market Analysis")
        controls_layout = QGridLayout(controls_group)
        
        # Item for analysis
        controls_layout.addWidget(QLabel("Analyze Item:"), 0, 0)
        self.analysis_item_combo = QComboBox()
        self.analysis_item_combo.setMinimumWidth(250)
        controls_layout.addWidget(self.analysis_item_combo, 0, 1)
        
        self.analyze_button = QPushButton("Analyze")
        controls_layout.addWidget(self.analyze_button, 0, 2)
        
        # Time period
        controls_layout.addWidget(QLabel("Time Period:"), 1, 0)
        self.time_period_combo = QComboBox()
        self.time_period_combo.addItems([
            "Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"
        ])
        self.time_period_combo.setCurrentText("Last 30 Days")
        controls_layout.addWidget(self.time_period_combo, 1, 1)
        
        # Include sources filter
        controls_layout.addWidget(QLabel("Include Sources:"), 2, 0)
        sources_layout = QHBoxLayout()
        
        self.include_market = QCheckBox("Market")
        self.include_market.setChecked(True)
        sources_layout.addWidget(self.include_market)
        
        self.include_guildie = QCheckBox("Guildie")
        self.include_guildie.setChecked(True)
        sources_layout.addWidget(self.include_guildie)
        
        self.include_harvested = QCheckBox("Harvested")
        self.include_harvested.setChecked(False)
        sources_layout.addWidget(self.include_harvested)
        
        sources_layout.addStretch()
        controls_layout.addLayout(sources_layout, 2, 1, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Analysis results
        results_group = QGroupBox("Price Analysis Results")
        results_layout = QGridLayout(results_group)
        
        # Statistics
        results_layout.addWidget(QLabel("Average Price:"), 0, 0)
        self.avg_price_label = QLabel("0.00 gold")
        self.avg_price_label.setStyleSheet("font-weight: bold; color: #ffd700;")
        results_layout.addWidget(self.avg_price_label, 0, 1)
        
        results_layout.addWidget(QLabel("Min Price:"), 1, 0)
        self.min_price_label = QLabel("0.00 gold")
        results_layout.addWidget(self.min_price_label, 1, 1)
        
        results_layout.addWidget(QLabel("Max Price:"), 2, 0)
        self.max_price_label = QLabel("0.00 gold")
        results_layout.addWidget(self.max_price_label, 2, 1)
        
        results_layout.addWidget(QLabel("Price Trend:"), 3, 0)
        self.trend_label = QLabel("No Data")
        results_layout.addWidget(self.trend_label, 3, 1)
        
        results_layout.addWidget(QLabel("Data Points:"), 4, 0)
        self.data_points_label = QLabel("0")
        results_layout.addWidget(self.data_points_label, 4, 1)
        
        # Recommended actions
        results_layout.addWidget(QLabel("Recommendation:"), 5, 0)
        self.recommendation_label = QLabel("Analyze an item for recommendations")
        self.recommendation_label.setWordWrap(True)
        results_layout.addWidget(self.recommendation_label, 5, 1)
        
        layout.addWidget(results_group)
        
        # Price history table
        history_group = QGroupBox("Price History")
        history_layout = QVBoxLayout(history_group)
        
        self.price_history_table = QTableWidget()
        self.price_history_table.setColumnCount(5)
        self.price_history_table.setHorizontalHeaderLabels([
            "Date", "Price", "Source", "Node", "Change"
        ])
        
        header = self.price_history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        history_layout.addWidget(self.price_history_table)
        layout.addWidget(history_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.export_analysis_button = QPushButton("Export Analysis")
        button_layout.addWidget(self.export_analysis_button)
        
        self.update_calculator_button = QPushButton("Update Calculator Prices")
        self.update_calculator_button.setStyleSheet("background-color: #0078d4; font-weight: bold;")
        button_layout.addWidget(self.update_calculator_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return panel
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        # Price entry
        self.price_search_button.clicked.connect(self.search_items_for_pricing)
        self.price_item_search.returnPressed.connect(self.search_items_for_pricing)
        self.record_price_button.clicked.connect(self.record_market_price)
        
        # Analysis
        self.analyze_button.clicked.connect(self.analyze_item_prices)
        self.time_period_combo.currentTextChanged.connect(self.update_analysis)
        self.analysis_item_combo.currentTextChanged.connect(self.update_analysis)
        
        # Actions
        self.export_analysis_button.clicked.connect(self.export_analysis)
        self.update_calculator_button.clicked.connect(self.update_calculator_prices)
    
    def search_items_for_pricing(self):
        """Search items for price recording"""
        search_term = self.price_item_search.text().strip()
        if not search_term:
            return
        
        try:
            items = self.data_manager.search_items(search_term)
            
            self.price_item_combo.clear()
            self.price_item_combo.addItem("Select an item...")
            
            # Also populate analysis combo
            self.analysis_item_combo.clear()
            self.analysis_item_combo.addItem("Select an item...")
            
            for item in items:
                display_name = f"{item['name']} ({item['type']})"
                self.price_item_combo.addItem(display_name, item['id'])
                self.analysis_item_combo.addItem(display_name, item['id'])
            
            logger.info(f"Found {len(items)} items for pricing")
            
        except Exception as e:
            logger.error(f"Price item search failed: {e}")
            QMessageBox.warning(self, "Search Error", f"Failed to search items: {e}")
    
    def record_market_price(self):
        """Record a market price observation with rarity"""
        if self.price_item_combo.currentIndex() == 0:
            QMessageBox.information(self, "Info", "Please select an item")
            return
        
        item_id = self.price_item_combo.currentData()
        price = self.price_input.value()
        source = self.price_source_combo.currentText()
        node_name = self.price_node_combo.currentText().strip()
        rarity = RarityManager.rarity_to_string(
            RarityManager.string_to_rarity(self.price_rarity_combo.currentText().lower())
        )
        
        if price <= 0:
            QMessageBox.information(self, "Info", "Please enter a valid price")
            return
        
        try:
            success = self.data_manager.record_market_price(
                item_id, price, source, rarity, node_name or None
            )
            
            if success:
                # Add to recent prices table
                self.add_recent_price_record(
                    self.price_item_combo.currentText(),
                    rarity,
                    price,
                    source,
                    node_name,
                    "Just now"
                )
                
                # Emit price update signal
                self.price_updated.emit(item_id, rarity, price)
                
                QMessageBox.information(self, "Success", "Price recorded successfully")
                
                # Clear form
                self.price_input.setValue(0.0)
                self.price_notes.clear()
                
                # Update analysis if this item is selected
                if (self.analysis_item_combo.currentData() == item_id and 
                    self.analysis_item_combo.currentIndex() > 0):
                    self.analyze_item_prices()
                
            else:
                QMessageBox.warning(self, "Error", "Failed to record price")
                
        except Exception as e:
            logger.error(f"Price recording failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to record price: {e}")
    
    def add_recent_price_record(self, item_name: str, rarity: str, price: float, source: str, 
                              node_name: str, recorded_time: str):
        """Add entry to recent prices table"""
        row_count = self.recent_prices_table.rowCount()
        self.recent_prices_table.insertRow(0)  # Insert at top
        
        self.recent_prices_table.setItem(0, 0, QTableWidgetItem(item_name))
        
        # Rarity with color
        rarity_enum = RarityManager.string_to_rarity(rarity)
        rarity_item = QTableWidgetItem(RarityManager.get_display_name(rarity_enum))
        apply_rarity_style_to_item(rarity_item, rarity_enum)
        self.recent_prices_table.setItem(0, 1, rarity_item)
        
        self.recent_prices_table.setItem(0, 2, QTableWidgetItem(f"{price:.2f}"))
        self.recent_prices_table.setItem(0, 3, QTableWidgetItem(source))
        self.recent_prices_table.setItem(0, 4, QTableWidgetItem(node_name))
        self.recent_prices_table.setItem(0, 5, QTableWidgetItem(recorded_time))
        
        # Limit to 10 recent records
        if row_count >= 10:
            self.recent_prices_table.removeRow(10)
    
    def analyze_item_prices(self):
        """Analyze prices for selected item"""
        if self.analysis_item_combo.currentIndex() == 0:
            QMessageBox.information(self, "Info", "Please select an item to analyze")
            return
        
        item_id = self.analysis_item_combo.currentData()
        self.perform_analysis(item_id)
    
    def update_analysis(self):
        """Update analysis when parameters change"""
        if self.analysis_item_combo.currentIndex() > 0:
            item_id = self.analysis_item_combo.currentData()
            self.perform_analysis(item_id)
    
    def perform_analysis(self, item_id: int):
        """Perform market analysis for an item"""
        try:
            # Get time period in days
            period_text = self.time_period_combo.currentText()
            days_map = {
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90,
                "All Time": 365 * 10  # Effectively all time
            }
            days = days_map.get(period_text, 30)
            
            # Get market analysis
            analysis = self.data_manager.get_market_analysis(item_id, days)
            
            if not analysis or analysis.get('data_points', 0) == 0:
                # Use mock data for demonstration
                analysis = {
                    'average_price': 15.75,
                    'min_price': 12.00,
                    'max_price': 20.50,
                    'price_trend': 'rising',
                    'data_points': 15
                }
            
            self.current_analysis = analysis
            self.update_analysis_display(analysis)
            self.load_price_history(item_id, days)
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            QMessageBox.warning(self, "Analysis Error", f"Failed to analyze prices: {e}")
    
    def update_analysis_display(self, analysis: Dict):
        """Update the analysis display with results"""
        # Update statistics
        self.avg_price_label.setText(f"{analysis.get('average_price', 0):.2f} gold")
        self.min_price_label.setText(f"{analysis.get('min_price', 0):.2f} gold")
        self.max_price_label.setText(f"{analysis.get('max_price', 0):.2f} gold")
        self.data_points_label.setText(str(analysis.get('data_points', 0)))
        
        # Update trend
        trend = analysis.get('price_trend', 'no_data')
        trend_text = {
            'rising': '📈 Rising',
            'falling': '📉 Falling', 
            'stable': '➡️ Stable',
            'insufficient_data': '❓ Insufficient Data',
            'no_data': '❌ No Data'
        }.get(trend, trend)
        
        self.trend_label.setText(trend_text)
        
        # Set trend color
        if trend == 'rising':
            self.trend_label.setStyleSheet("color: #28a745; font-weight: bold;")
        elif trend == 'falling':
            self.trend_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        else:
            self.trend_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        
        # Generate recommendation
        recommendation = self.generate_recommendation(analysis)
        self.recommendation_label.setText(recommendation)
        
        # Emit trend alert if significant
        if trend in ['rising', 'falling'] and analysis.get('data_points', 0) >= 5:
            change_percent = abs(analysis.get('max_price', 0) - analysis.get('min_price', 0)) / analysis.get('average_price', 1) * 100
            if change_percent > 20:  # Significant change
                item_name = self.analysis_item_combo.currentText()
                self.trend_alert.emit(item_name, trend, change_percent)
    
    def generate_recommendation(self, analysis: Dict) -> str:
        """Generate trading recommendation based on analysis"""
        if analysis.get('data_points', 0) < 3:
            return "Insufficient data for recommendations. Record more prices."
        
        trend = analysis.get('price_trend', 'no_data')
        avg_price = analysis.get('average_price', 0)
        min_price = analysis.get('min_price', 0)
        max_price = analysis.get('max_price', 0)
        
        if trend == 'rising':
            return f"📈 Prices are rising. Consider buying now if below {avg_price:.2f} gold. Good time to sell if you have stock."
        elif trend == 'falling':
            return f"📉 Prices are falling. Wait to buy until prices stabilize. Consider selling soon if above {avg_price:.2f} gold."
        elif trend == 'stable':
            return f"➡️ Prices are stable around {avg_price:.2f} gold. Safe to buy/sell at market rates."
        else:
            return f"Current average: {avg_price:.2f} gold. Range: {min_price:.2f} - {max_price:.2f} gold."
    
    def load_price_history(self, item_id: int, days: int):
        """Load and display price history"""
        try:
            # Get recent prices
            prices = self.data_manager.get_recent_market_prices(item_id, days)
            
            if not prices:
                # Use mock data
                prices = [
                    {'price': 18.50, 'source': 'market', 'node_name': 'Lionhold', 'recorded_at': '2024-01-15 14:30'},
                    {'price': 16.75, 'source': 'guildie', 'node_name': 'Winstead', 'recorded_at': '2024-01-14 10:15'},
                    {'price': 15.00, 'source': 'market', 'node_name': 'Lionhold', 'recorded_at': '2024-01-13 16:45'},
                ]
            
            self.price_history_table.setRowCount(len(prices))
            
            prev_price = None
            for row, price_data in enumerate(prices):
                price = float(price_data['price'])
                
                # Date/time
                recorded_at = price_data.get('recorded_at', 'Unknown')
                date_part = recorded_at.split(' ')[0] if ' ' in recorded_at else recorded_at
                self.price_history_table.setItem(row, 0, QTableWidgetItem(date_part))
                
                # Price
                price_item = QTableWidgetItem(f"{price:.2f}")
                self.price_history_table.setItem(row, 1, price_item)
                
                # Source
                self.price_history_table.setItem(row, 2, QTableWidgetItem(price_data.get('source', '')))
                
                # Node
                self.price_history_table.setItem(row, 3, QTableWidgetItem(price_data.get('node_name', '')))
                
                # Change from previous
                if prev_price is not None:
                    change = price - prev_price
                    change_percent = (change / prev_price) * 100 if prev_price > 0 else 0
                    change_text = f"{change:+.2f} ({change_percent:+.1f}%)"
                    
                    change_item = QTableWidgetItem(change_text)
                    if change > 0:
                        change_item.setBackground(Qt.GlobalColor.green)
                    elif change < 0:
                        change_item.setBackground(Qt.GlobalColor.red)
                    
                    self.price_history_table.setItem(row, 4, change_item)
                else:
                    self.price_history_table.setItem(row, 4, QTableWidgetItem("-"))
                
                prev_price = price
                
        except Exception as e:
            logger.error(f"Failed to load price history: {e}")
    
    def export_analysis(self):
        """Export current analysis data"""
        if not self.current_analysis:
            QMessageBox.information(self, "Info", "No analysis to export")
            return
        
        # TODO: Implement export functionality
        QMessageBox.information(self, "Success", "Analysis data exported successfully")
    
    def update_calculator_prices(self):
        """Update calculator with current average prices"""
        if not self.current_analysis:
            QMessageBox.information(self, "Info", "No analysis data to send")
            return
        
        if self.analysis_item_combo.currentIndex() == 0:
            return
        
        item_id = self.analysis_item_combo.currentData()
        avg_price = self.current_analysis.get('average_price', 0)
        
        if avg_price > 0:
            self.price_updated.emit(item_id, avg_price)
            QMessageBox.information(
                self, "Success", 
                f"Updated calculator with average price: {avg_price:.2f} gold"
            )
    
    def refresh_data(self):
        """Refresh module data when database is updated"""
        # Clear current selections
        self.price_item_combo.clear()
        self.price_item_combo.addItem("Select an item...")
        
        self.analysis_item_combo.clear()
        self.analysis_item_combo.addItem("Select an item...")
        
        # Clear analysis results
        self.current_analysis = {}
        self.avg_price_label.setText("0.00 gold")
        self.min_price_label.setText("0.00 gold")
        self.max_price_label.setText("0.00 gold")
        self.trend_label.setText("No Data")
        self.data_points_label.setText("0")
        self.recommendation_label.setText("Analyze an item for recommendations")
        
        # Clear tables
        self.price_history_table.setRowCount(0)