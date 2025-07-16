"""
Main window for the Ashes of Creation Artisan Toolbox.
Provides tab-based interface for different toolbox modules.
"""

import logging
import asyncio
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, 
    QMenuBar, QMessageBox, QProgressBar, QLabel, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QAction, QKeySequence

from data_manager import DataManager
from modules.calculator import CalculatorModule
from modules.inventory_manager import InventoryManagerModule
from modules.market_analysis import MarketAnalysisModule
from modules.batch_planner import BatchPlannerModule
from gui.base_module import ModuleManager

logger = logging.getLogger(__name__)

class DataInitializationThread(QThread):
    """Background thread for data manager initialization"""
    
    progress_update = pyqtSignal(str)  # status message
    initialization_complete = pyqtSignal(bool)  # success flag
    sync_complete = pyqtSignal(bool, dict)  # success, stats
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.should_sync = False
    
    def run(self):
        """Initialize data manager and optionally sync"""
        try:
            # Initialize data manager
            self.progress_update.emit("Initializing database...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(self.data_manager.initialize())
            
            if success:
                self.progress_update.emit("Database initialized successfully")
                self.initialization_complete.emit(True)
                
                # Check if sync is needed
                if self.should_sync:
                    self.progress_update.emit("Syncing with Ashescodex API...")
                    sync_success, stats = loop.run_until_complete(
                        self.data_manager.sync_from_api()
                    )
                    self.sync_complete.emit(sync_success, stats)
                
            else:
                self.initialization_complete.emit(False)
                
        except Exception as e:
            logger.error(f"Data initialization failed: {e}")
            self.initialization_complete.emit(False)
        finally:
            loop.close()
    
    def set_sync_required(self, sync: bool):
        """Set whether to perform API sync"""
        self.should_sync = sync


class MainWindow(QMainWindow):
    """
    Main application window with tab-based interface.
    Coordinates between different toolbox modules and data management.
    """
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        
        self.data_manager = data_manager
        self.modules = {}
        self.initialization_thread = None
        self.module_manager = ModuleManager()
        
        # Setup window
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Initialize components
        self.create_modules()
        
        logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup the main UI structure"""
        self.setWindowTitle("Ashes of Creation Artisan Toolbox")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with tab layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Set tab style
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(False)
    
    def setup_menu(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Data sync action
        sync_action = QAction("&Sync Data", self)
        sync_action.setShortcut(QKeySequence("Ctrl+S"))
        sync_action.setStatusTip("Sync data with Ashescodex API")
        sync_action.triggered.connect(self.sync_data)
        file_menu.addAction(sync_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Clear cache action
        clear_cache_action = QAction("Clear &Cache", self)
        clear_cache_action.setStatusTip("Clear local API cache")
        clear_cache_action.triggered.connect(self.clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # Database stats action
        db_stats_action = QAction("Database &Stats", self)
        db_stats_action.setStatusTip("Show database statistics")
        db_stats_action.triggered.connect(self.show_database_stats)
        tools_menu.addAction(db_stats_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Artisan Toolbox")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar with connection info"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status labels
        self.status_label = QLabel("Ready")
        self.connection_label = QLabel("Not Connected")
        self.data_label = QLabel("No Data")
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add to status bar
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.addPermanentWidget(self.connection_label)
        self.status_bar.addPermanentWidget(self.data_label)
    
    def create_modules(self):
        """Create and setup all toolbox modules"""
        try:
            # Calculator module
            calculator = CalculatorModule(self.data_manager)
            self.modules['calculator'] = calculator
            self.module_manager.register_module(calculator)
            self.tab_widget.addTab(calculator, "🧮 Calculator")
            
            # Inventory manager module  
            inventory = InventoryManagerModule(self.data_manager)
            self.modules['inventory'] = inventory
            self.module_manager.register_module(inventory)
            self.tab_widget.addTab(inventory, "📦 Inventory")
            
            # Market analysis module
            market = MarketAnalysisModule(self.data_manager)
            self.modules['market'] = market
            self.module_manager.register_module(market)
            self.tab_widget.addTab(market, "📈 Market Analysis")
            
            # Batch planner module
            batch_planner = BatchPlannerModule(self.data_manager)
            self.modules['batch_planner'] = batch_planner
            self.module_manager.register_module(batch_planner)
            self.tab_widget.addTab(batch_planner, "📋 Batch Planner")
            
            # Connect inter-module signals
            self.connect_modules()
            
            logger.info("All modules created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create modules: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize modules: {e}")
    
    def connect_modules(self):
        """Connect signals between modules for data flow using module manager"""
        try:
            # Connect craft completion signal
            if 'calculator' in self.modules and 'inventory' in self.modules:
                calc_module = self.modules['calculator']
                inv_module = self.modules['inventory']
                
                # Connect through module manager for better error handling
                calc_module.signals.craft_completed.connect(inv_module.handle_craft_completed)
            
            # Connect market analysis price updates - will be updated when market module is refactored
            # if 'market' in self.modules and 'calculator' in self.modules:
            #     market_module = self.modules['market']
            #     calc_module = self.modules['calculator']
            #     market_module.signals.price_updated.connect(calc_module.update_material_price)
            
            logger.info("Module signals connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect module signals: {e}")
            QMessageBox.warning(self, "Warning", f"Some module connections failed: {e}")
    
    def initialize_data_manager(self):
        """Initialize data manager in background thread"""
        if self.initialization_thread and self.initialization_thread.isRunning():
            return
        
        self.initialization_thread = DataInitializationThread(self.data_manager)
        self.initialization_thread.progress_update.connect(self.update_status)
        self.initialization_thread.initialization_complete.connect(self.on_initialization_complete)
        self.initialization_thread.sync_complete.connect(self.on_sync_complete)
        
        # Check if sync is needed
        data_status = self.data_manager.get_data_status()
        sync_needed = (
            not data_status.get('last_sync') or 
            data_status.get('sync_age_hours', 0) > 24
        )
        
        self.initialization_thread.set_sync_required(sync_needed)
        self.initialization_thread.start()
        
        self.update_status("Starting initialization...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.setText(message)
        logger.info(f"Status: {message}")
    
    def on_initialization_complete(self, success: bool):
        """Handle initialization completion"""
        if success:
            self.connection_label.setText("Connected")
            self.update_status("Ready")
            
            # Update data status
            self.update_data_status()
            
            # Enable modules
            for module in self.modules.values():
                module.setEnabled(True)
                if hasattr(module, 'refresh_data'):
                    module.refresh_data()
                    
        else:
            self.connection_label.setText("Connection Failed")
            self.update_status("Initialization failed")
            QMessageBox.warning(
                self, "Warning", 
                "Failed to initialize data manager. Some features may not work."
            )
    
    def on_sync_complete(self, success: bool, stats: dict):
        """Handle sync completion"""
        self.progress_bar.setVisible(False)
        
        if success:
            items_count = stats.get('items_updated', 0)
            duration = stats.get('sync_duration', 0)
            self.update_status(f"Sync completed: {items_count} items ({duration:.1f}s)")
            
            # Refresh modules with new data
            for module in self.modules.values():
                if hasattr(module, 'refresh_data'):
                    module.refresh_data()
                    
        else:
            self.update_status("Sync failed")
            QMessageBox.warning(self, "Warning", "Data sync failed. Using cached data.")
        
        self.update_data_status()
    
    def update_data_status(self):
        """Update data status display"""
        try:
            status = self.data_manager.get_data_status()
            items_count = status.get('database_stats', {}).get('items', 0)
            sync_age = status.get('sync_age_hours', 0)
            
            if sync_age < 1:
                age_str = "< 1h"
            elif sync_age < 24:
                age_str = f"{sync_age:.1f}h"
            else:
                age_str = f"{sync_age/24:.1f}d"
            
            self.data_label.setText(f"Items: {items_count} (Updated: {age_str})")
            
        except Exception as e:
            logger.error(f"Failed to update data status: {e}")
            self.data_label.setText("Data: Error")
    
    def sync_data(self):
        """Manually trigger data sync"""
        if self.initialization_thread and self.initialization_thread.isRunning():
            QMessageBox.information(self, "Info", "Sync already in progress")
            return
        
        self.initialization_thread = DataInitializationThread(self.data_manager)
        self.initialization_thread.progress_update.connect(self.update_status)
        self.initialization_thread.sync_complete.connect(self.on_sync_complete)
        self.initialization_thread.set_sync_required(True)
        self.initialization_thread.start()
        
        self.update_status("Syncing data...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
    
    def clear_cache(self):
        """Clear local API cache"""
        reply = QMessageBox.question(
            self, "Clear Cache",
            "Are you sure you want to clear the local API cache?\n"
            "This will force a fresh download on next sync.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from api_client import AshesCodexAPIClient
                client = AshesCodexAPIClient()
                client.clear_cache()
                QMessageBox.information(self, "Success", "Cache cleared successfully")
                self.update_status("Cache cleared")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")
    
    def show_database_stats(self):
        """Show database statistics dialog"""
        try:
            status = self.data_manager.get_data_status()
            stats = status.get('database_stats', {})
            
            stats_text = "Database Statistics:\n\n"
            for table, count in stats.items():
                stats_text += f"{table.capitalize()}: {count:,}\n"
            
            last_sync = status.get('last_sync', 'Never')
            stats_text += f"\nLast Sync: {last_sync}"
            
            QMessageBox.information(self, "Database Stats", stats_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get database stats: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>Ashes of Creation Artisan Toolbox</h3>
        <p>Version 1.0.0</p>
        <p>A desktop application for crafting calculations and inventory management 
        for the Ashes of Creation MMORPG.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Tax-aware crafting cost calculations</li>
        <li>Multi-node inventory management</li>
        <li>Market price tracking and analysis</li>
        <li>Batch order planning</li>
        </ul>
        <p>Data provided by <a href="https://ashescodex.com">ashescodex.com</a></p>
        """
        
        QMessageBox.about(self, "About", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop any running threads
        if self.initialization_thread and self.initialization_thread.isRunning():
            self.initialization_thread.terminate()
            self.initialization_thread.wait()
        
        event.accept()